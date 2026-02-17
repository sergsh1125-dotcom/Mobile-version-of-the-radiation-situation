import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

# ===============================
# 1. Налаштування та База Даних
# ===============================
st.set_page_config(page_title="RAD-Mobile Pro", page_icon="☢️", layout="centered")

DB_FILE = "database.csv"

# Завантаження бази при старті
if "data" not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.data = pd.read_csv(DB_FILE)
    else:
        st.session_state.data = pd.DataFrame(columns=["lat", "lon", "value", "unit", "time"])

def save_to_disk():
    st.session_state.data.to_csv(DB_FILE, index=False)

# Стилізація для товстих пальців (великі кнопки)
st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .stButton>button {width: 100%; height: 50px; font-weight: bold; border-radius: 12px;}
    .undo-btn>div>button {background-color: #fff3e0 !important; color: #e65100 !important; border: 1px solid #ffb74d !important;}
    .stDownloadButton>button {background-color: #e1f5fe !important; color: #01579b !important;}
    .stForm {border: 2px solid #3366ff; padding: 15px; border-radius: 15px; background-color: #f8f9fa;}
</style>
""", unsafe_allow_html=True)

# ===============================
# 2. Макет Маркера (Синій трикутник)
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
# 3. Основний екран (Мобільний вид)
# ===============================
st.title("☢️ RAD-MOBILE PRO")

# КАРТА
st.info("👆 Натисніть на карту, щоб обрати місце вимірювання")

# Центрування на останній точці або на Києві
if not st.session_state.data.empty:
    center = [st.session_state.data['lat'].iloc[-1], st.session_state.data['lon'].iloc[-1]]
else:
    center = [50.45, 30.52]

m = folium.Map(location=center, zoom_start=13, control_scale=True)

# Відображення всіх точок з бази
for _, r in st.session_state.data.iterrows():
    v_s = f"{float(r['value']):.4f}".rstrip('0').rstrip('.')
    label = f"{v_s} {r['unit']}"
    folium.Marker([r.lat, r.lon], icon=folium.DivIcon(icon_anchor=(17, 45), html=get_custom_marker_html(label))).add_to(m)

# Відображення карти
map_res = st_folium(m, width="100%", height=350, key="map")

# Отримуємо координати з кліку
clicked_lat = map_res.get("last_clicked", {}).get("lat", center[0])
clicked_lon = map_res.get("last_clicked", {}).get("lng", center[1])

# ФОРМА РУЧНОГО ВВОДУ (під картою)
with st.form("input_form", clear_on_submit=False):
    st.markdown(f"📍 **Координати:** `{clicked_lat:.5f}, {clicked_lon:.5f}`")
    
    # Ручний ввід значень
    val = st.number_input("Потужність (ПЕД)", format="%.4f", step=0.001)
    unit = st.selectbox("Одиниця", ["мкЗв/год", "мЗв/год"])
    t_now = pd.Timestamp.now().strftime("%d.%m.%Y %H:%M")
    time_str = st.text_input("Дата та час", value=t_now)
    
    # Кнопка збереження
    if st.form_submit_button("✅ ДОДАТИ ТОЧКУ В БАЗУ"):
        new_point = pd.DataFrame([{"lat": clicked_lat, "lon": clicked_lon, "value": val, "unit": unit, "time": time_str}])
        st.session_state.data = pd.concat([st.session_state.data, new_point], ignore_index=True)
        save_to_disk()
        st.success("Точку збережено!")
        st.rerun()

# КНОПКА СКАСУВАННЯ (Остання точка)
if not st.session_state.data.empty:
    st.markdown('<div class="undo-btn">', unsafe_allow_html=True)
    if st.button("⬅️ ВИДАЛИТИ ОСТАННЮ ТОЧКУ (UNDO)"):
        st.session_state.data = st.session_state.data.iloc[:-1]
        save_to_disk()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# 4. Робота з файлами (Синхронізація)
# ===============================
st.divider()
st.subheader("📁 Керування базою CSV")

# Скачування на телефон (передача на ПК)
csv_bytes = st.session_state.data.to_csv(index=False).encode('utf-8')
st.download_button(
    label="💾 СКАЧАТИ БАЗУ НА ТЕЛЕФОН",
    data=csv_bytes,
    file_name="radiation_db.csv",
    mime="text/csv",
    use_container_width=True
)

# Завантаження файлу (якщо треба відновити або перекинути з ПК)
uploaded_db = st.file_uploader("📥 Завантажити CSV файл", type="csv")
if uploaded_db:
    if st.button("🔄 Оновити дані з файлу"):
        st.session_state.data = pd.read_csv(uploaded_db)
        save_to_disk()
        st.success("Базу синхронізовано!")
        st.rerun()

# Повне очищення
if st.button("🗑 ПОВНЕ ВИДАЛЕННЯ ВСІХ ДАНИХ"):
    st.session_state.data = pd.DataFrame(columns=["lat", "lon", "value", "unit", "time"])
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    st.warning("Базу повністю очищено!")
    st.rerun()
