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
# 2. Функція Маркера
# ===============================
def get_custom_marker_html(label_text):
    return f"""
    <div style="position: relative; display: flex; align-items: center; width: 220px;">
        <svg width="35" height="45" viewBox="0 0 40 50" xmlns="http://www.w3.org/2000/svg">
            <line x1="20" y1="35" x2="20" y2="45" stroke="blue" stroke-width="3" />
            <polygon points="2,5 38,5 20,35" fill="blue" stroke="white" stroke-width="1"/>
            <circle cx="20" cy="18" r="8" fill="yellow" />
            <circle cx="20" cy="18" r="1.5" fill="black" />
            <path d="M20,18 L17,13 A7,7 0 0,1 23,13 Z" fill="black" />
            <path d="M20,18 L24,22 A7,7 0 0,1 16,22 Z" fill="black" />
            <path d="M13,18 A7,7 0 0,1 15,13 L20,18 Z" fill="black" />
            <path d="M25,13 A7,7 0 0,1 27,18 L20,18 Z" fill="black" />
        </svg>
        <div style="margin-left:4px; color:blue; font-family:sans-serif; font-size:10pt; font-weight:bold; text-shadow:1px 1px 2px white;">
            {label_text}
        </div>
    </div>
    """

# ===============================
# 3. Інтерфейс
# ===============================
st.title("☢️ RAD-MOBILE PRO")

if st.button("📘 ІНСТРУКЦІЯ ЩОДО РОБОТИ"):
    st.info("""
    1. Натисніть на мапу (час та місце заповняться самі).
    2. Введіть значення у полі **Потужність дози**.
    3. Натисніть **Зберегти**.
    """)

st.divider()

# Карта
if not st.session_state.data.empty:
    center = [st.session_state.data['lat'].iloc[-1], st.session_state.data['lon'].iloc[-1]]
else:
    center = [50.45, 30.52]

m = folium.Map(location=center, zoom_start=13)

for _, r in st.session_state.data.iterrows():
    # Округлення до 2 знаків для карти
    v_s = f"{float(r['value']):.2f}"
    label = f"{v_s} {r['unit']} | {r['time']}"
    folium.Marker([r.lat, r.lon], icon=folium.DivIcon(icon_anchor=(17, 45), html=get_custom_marker_html(label))).add_to(m)

map_res = st_folium(m, width="100%", height=350, key="map")

# Логіка кліку
if map_res and map_res.get("last_clicked"):
    clicked_lat = map_res["last_clicked"]["lat"]
    clicked_lon = map_res["last_clicked"]["lng"]
    auto_time = pd.Timestamp.now(tz="Europe/Kyiv").strftime("%d.%m.%Y %H:%M")
else:
    clicked_lat = center[0]
    clicked_lon = center[1]
    auto_time = pd.Timestamp.now(tz="Europe/Kyiv").strftime("%d.%m.%Y %H:%M")

# Форма
with st.form("input_form"):
    st.markdown(f"📍 **Точка:** `{clicked_lat:.5f}, {clicked_lon:.5f}` | 🕒 `{auto_time}`")
    
    # Змінено напис та формат (2 знаки після коми)
    val = st.number_input("Потужність дози", format="%.2f", step=0.01)
    unit = st.selectbox("Одиниця", ["мкЗв/год", "мЗв/год"])
    
    if st.form_submit_button("✅ ЗБЕРЕГТИ ВИМІРЮВАННЯ"):
        new_point = pd.DataFrame([{"lat": clicked_lat, "lon": clicked_lon, "value": val, "unit": unit, "time": auto_time}])
        st.session_state.data = pd.concat([st.session_state.data, new_point], ignore_index=True)
        save_to_disk()
        st.rerun()

# Undo
if not st.session_state.data.empty:
    st.markdown('<div class="undo-btn">', unsafe_allow_html=True)
    if st.button("⬅️ ВИДАЛИТИ ОСТАННЮ ТОЧКУ"):
        st.session_state.data = st.session_state.data.iloc[:-1]
        save_to_disk()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Експорт
st.divider()
st.subheader("📊 Звіти")

if not st.session_state.data.empty:
    export_map = folium.Map(location=[st.session_state.data.lat.mean(), st.session_state.data.lon.mean()], zoom_start=12)
    for _, r in st.session_state.data.iterrows():
        v_s = f"{float(r['value']):.2f}"
        label = f"{v_s} {r['unit']} | {r['time']}"
        folium.Marker([r.lat, r.lon], icon=folium.DivIcon(icon_anchor=(17, 45), html=get_custom_marker_html(label))).add_to(export_map)
    
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
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()
