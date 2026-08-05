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
# 3. Інтерфейс та Карта
# ===============================
st.title("☢️ RAD-MOBILE PRO")

if st.button("📘 ІНСТРУКЦІЯ ЩОДО РОБОТИ"):
    st.info("""
    1. Натисніть на мапу (з'явиться червоний маркер вибору точки).
    2. Введіть значення у полі **Потужність дози**.
    3. Натисніть **Зберегти** (на місці маркера з'явиться синя крапка з дробом).
    """)

st.divider()

# 1. Отримуємо збережені координати попереднього кліку з session_state
clicked_lat = st.session_state.get("last_lat", None)
clicked_lon = st.session_state.get("last_lon", None)

# Визначення центру карти
if clicked_lat is not None and clicked_lon is not None:
    center = [clicked_lat, clicked_lon]
elif not st.session_state.data.empty:
    center = [st.session_state.data['lat'].iloc[-1], st.session_state.data['lon'].iloc[-1]]
else:
    center = [50.45, 30.52]

# 2. Створюємо карту
m = folium.Map(location=center, zoom_start=13, prefer_canvas=True)

# 3. Відмалювання вже збережених точок з бази (Синя крапка + Дріб)
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
        weight=1,
        popup=f"Потужність: {v_s}<br>Час: {t_s}"
    ).add_to(m)
    
    folium.Marker(
        [r.lat, r.lon],
        icon=folium.DivIcon(
            icon_anchor=(-6, 18),
            html=get_fraction_label_html(v_s, t_s)
        )
    ).add_to(m)

# 4. Якщо є зафіксований клік — ставимо ЧЕРВОНИЙ маркер ДО рендерингу карти
if clicked_lat is not None and clicked_lon is not None:
    folium.Marker(
        [clicked_lat, clicked_lon],
        popup="Обрана точка",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)

# 5. Відображаємо карту та ловимо новий клік
map_res = st_folium(m, width="100%", height=380, key="map", returned_objects=["last_clicked"])

# 6. Оновлюємо стан кліку при взаємодії з картою
if map_res and map_res.get("last_clicked"):
    new_lat = map_res["last_clicked"]["lat"]
    new_lon = map_res["last_clicked"]["lng"]
    
    # Якщо клікнули в нове місце — зберігаємо в session_state і перезапускаємо для відображення маркера
    if st.session_state.get("last_lat") != new_lat or st.session_state.get("last_lon") != new_lon:
        st.session_state["last_lat"] = new_lat
        st.session_state["last_lon"] = new_lon
        st.rerun()

# Локальний час для форми
auto_time = pd.Timestamp.now(tz="Europe/Kyiv").strftime("%d.%m.%Y %H:%M")
curr_lat = clicked_lat if clicked_lat is not None else center[0]
curr_lon = clicked_lon if clicked_lon is not None else center[1]

# ===============================
# 4. Форма внесення даних
# ===============================
with st.form("input_form"):
    st.markdown(f"📍 **Обрано координати:** `{curr_lat:.5f}, {curr_lon:.5f}` | 🕒 `{auto_time}`")
    
    val = st.number_input("Потужність дози", format="%.2f", step=0.01)
    unit = st.selectbox("Одиниця", ["мкЗв/год", "мЗв/год"])
    
    if st.form_submit_button("✅ ЗБЕРЕГТИ ВИМІРЮВАННЯ"):
        new_point = pd.DataFrame([{"lat": curr_lat, "lon": curr_lon, "value": val, "unit": unit, "time": auto_time}])
        st.session_state.data = pd.concat([st.session_state.data, new_point], ignore_index=True)
        save_to_disk()
        
        # Очищаємо тимчасовий маркер після збереження
        st.session_state["last_lat"] = None
        st.session_state["last_lon"] = None
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
