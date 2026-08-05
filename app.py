import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

# ===============================
# 1. Налаштування сторінки
# ===============================
st.set_page_config(page_title="RAD-Mobile Pro", page_icon="☢️", layout="centered")

DB_FILE = "database.csv"

if "data" not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.data = pd.read_csv(DB_FILE)
    else:
        st.session_state.data = pd.DataFrame(columns=["lat", "lon", "value", "unit", "time"])

def save_to_disk():
    st.session_state.data.to_csv(DB_FILE, index=False)

st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .stButton>button {width: 100%; height: 55px; font-weight: bold; border-radius: 12px;}
    .undo-btn>div>button {background-color: #fff3e0 !important; color: #e65100 !important; border: 1px solid #ffb74d !important; height: 45px !important;}
    .stDownloadButton>button {background-color: #e8f5e9 !important; color: #2e7d32 !important; border: 1px solid #a5d6a7 !important;}
    .stForm {border: 2px solid #3366ff; padding: 15px; border-radius: 15px; background-color: #f8f9fa;}
</style>
""", unsafe_allow_html=True)

# ===============================
# 2. Функція HTML-підпису (Дріб)
# ===============================
def get_fraction_label_html(value_str, date_str):
    """Генерує HTML для синього дробу: Чисельник = Потужність, Знаменник = Дата"""
    return f"""
    <div style="
        display: inline-flex; 
        flex-direction: column; 
        align-items: center; 
        justify-content: center; 
        color: #0044cc; 
        font-family: Arial, sans-serif; 
        font-size: 11px; 
        font-weight: bold; 
        line-height: 1.1;
        white-space: nowrap;
        background: rgba(255, 255, 255, 0.85);
        padding: 2px 4px;
        border-radius: 4px;
        box-shadow: 0px 1px 3px rgba(0,0,0,0.2);
    ">
        <span style="border-bottom: 1.5px solid #0044cc; padding-bottom: 1px; width: 100%; text-align: center;">
            {value_str}
        </span>
        <span style="padding-top: 1px; width: 100%; text-align: center; font-size: 9.5px;">
            {date_str}
        </span>
    </div>
    """

# ===============================
# 3. Інтерфейс
# ===============================
st.title("☢️ RAD-MOBILE PRO")

if st.button("📘 ІНСТРУКЦІЯ ЩОДО РОБОТИ"):
    st.info("""
    1. Натисніть на мапу (з'явиться червоний маркер вибору точки).
    2. Введіть значення у полі **Потужність дози**.
    3. Натисніть **Зберегти** (на місці маркера з'явиться синя крапка з дробом).
    """)

st.divider()

# Визначення центру карти
if not st.session_state.data.empty:
    center = [st.session_state.data['lat'].iloc[-1], st.session_state.data['lon'].iloc[-1]]
else:
    center = [50.45, 30.52]

m = folium.Map(location=center, zoom_start=13, prefer_canvas=True)

# Відмалювання збережених точок вимірювання (Синя крапка + Дріб)
for _, r in st.session_state.data.iterrows():
    v_s = f"{float(r['value']):.2f} {r['unit']}"
    t_s = str(r['time'])
    
    # 1. Синя точка діаметром ~1 мм (radius=3.5 px)
    folium.CircleMarker(
        location=[r.lat, r.lon],
        radius=3.5,
        color="#0033cc",
        fill=True,
        fill_color="#0055ff",
        fill_opacity=1.0,
        weight=1,
        popup=f"Потужність: {v_s}<br>Час: {t_s}"
    ).add_to(m)
    
    # 2. Підпис біля точки у вигляді дробу
    folium.Marker(
        [r.lat, r.lon],
        icon=folium.DivIcon(
            icon_anchor=(-6, 18),  # Зміщення дробу трохи праворуч і вище точки
            html=get_fraction_label_html(v_s, t_s)
        )
    ).add_to(m)

# Відображення карти у Streamlit
map_res = st_folium(m, width="100%", height=380, key="map", returned_objects=["last_clicked"])

# Обробка кліку пальцем по карті
if map_res and map_res.get("last_clicked"):
    clicked_lat = map_res["last_clicked"]["lat"]
    clicked_lon = map_res["last_clicked"]["lng"]
    auto_time = pd.Timestamp.now(tz="Europe/Kyiv").strftime("%d.%m.%Y %H:%M")
    
    # Додаємо тимчасовий червоний маркер для візуалізації зафіксованої точки
    folium.Marker(
        [clicked_lat, clicked_lon],
        popup="Обрана точка",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)
else:
    clicked_lat = center[0]
    clicked_lon = center[1]
    auto_time = pd.Timestamp.now(tz="Europe/Kyiv").strftime("%d.%m.%Y %H:%M")

# ===============================
# 4. Форма внесення даних
# ===============================
with st.form("input_form"):
    st.markdown(f"📍 **Обрано координати:** `{clicked_lat:.5f}, {clicked_lon:.5f}` | 🕒 `{auto_time}`")
    
    val = st.number_input("Потужність дози", format="%.2f", step=0.01)
    unit = st.selectbox("Одиниця", ["мкЗв/год", "мЗв/год"])
    
    if st.form_submit_button("✅ ЗБЕРЕГТИ ВИМІРЮВАННЯ"):
        new_point = pd.DataFrame([{"lat": clicked_lat, "lon": clicked_lon, "value": val, "unit": unit, "time": auto_time}])
        st.session_state.data = pd.concat([st.session_state.data, new_point], ignore_index=True)
        save_to_disk()
        st.rerun()

# Видалення останньої точки
if not st.session_state.data.empty:
    st.markdown('<div class="undo-btn">', unsafe_allow_html=True)
    if st.button("⬅️ ВИДАЛИТИ ОСТАННЮ ТОЧКУ"):
        st.session_state.data = st.session_state.data.iloc[:-1]
        save_to_disk()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# 5. Експорт даних та HTML-звіту
# ===============================
st.divider()
st.subheader("📊 Звіти")

if not st.session_state.data.empty:
    export_map = folium.Map(location=[st.session_state.data.lat.mean(), st.session_state.data.lon.mean()], zoom_start=12)
    for _, r in st.session_state.data.iterrows():
        v_s = f"{float(r['value']):.2f} {r['unit']}"
        t_s = str(r['time'])
        
        folium.CircleMarker(
            location=[r.lat, r.lon],
            radius=3.5,
            color="#0033cc",
            fill=True,
            fill_color="#0055ff",
            fill_opacity=1.0,
            weight=1
        ).add_to(export_map)
        
        folium.Marker(
            [r.lat, r.lon],
            icon=folium.DivIcon(
                icon_anchor=(-6, 18),
                html=get_fraction_label_html(v_s, t_s)
            )
        ).add_to(export_map)
    
    st.download_button(
        label="🌐 ЗБЕРЕГТИ КАРТУ У HTML (ЗВІТ)",
        data=export_map._repr_html_().encode('utf-8'),
        file_name=f"Rad_Report_{pd.Timestamp.now().strftime('%d_%m_%Y')}.html",
        mime="text/html",
        use_container_width=True
    )

st.download_button(
    label="💾 СКАЧАТИ БАЗУ CSV",
    data=st.session_state.data.to_csv(index=False).encode('utf-8'),
    file_name="radiation_db.csv",
    mime="text/csv",
    use_container_width=True
)

with st.expander("📥 Керування"):
    up_db = st.file_uploader("Завантажити CSV", type="csv")
    if up_db and st.button("🔄 Оновити"):
        st.session_state.data = pd.read_csv(up_db)
        save_to_disk()
        st.rerun()
    if st.button("🗑 ПОВНЕ ОЧИЩЕННЯ"):
        st.session_state.data = pd.DataFrame(columns=["lat", "lon", "value", "unit", "time"])
        if os.path.exists(DB_FILE): 
            os.remove(DB_FILE)
        st.rerun()
