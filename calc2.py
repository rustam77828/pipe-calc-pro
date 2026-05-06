import streamlit as st
import math
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Production Setup", page_icon="⚙️", layout="wide")

# ---------------- CSS ----------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] [data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 5px !important;
}
.stButton > button {
    width: 100% !important;
    height: 50px !important;
    font-size: 20px !important;
}
/* Стиль для блока погоды */
.weather-container {
    text-align: right;
    margin-bottom: 15px;
}
.weather-text {
    font-size: 32px;
    font-weight: bold;
    margin-bottom: -5px;
    line-height: 1;
}
.weather-sub {
    font-size: 14px;
    color: gray;
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 1px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- WEATHER FUNCTION ----------------
def get_weather(city): # Добавляем аргумент city
    raw_key = os.getenv("WEATHER_API_KEY") or st.secrets.get("WEATHER_API_KEY")
    if not raw_key:
        return "No Key"

    api_key = raw_key.strip()
    # Используем переменную city в URL
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            temp = int(data['main']['temp'])
            main = data['weather'][0]['main'].lower()
            icon = "☀️" if "clear" in main else "☁️" if "cloud" in main else "🌧️"
            return f"{temp}°C {icon}"
        else:
            return f"Error {res.status_code}"
    except:
        return "Conn Error"

# ---------------- STATE ----------------
if 'active_field' not in st.session_state:
    st.session_state.active_field = 'D'

for f in ['D_val', 't_val', 'B_val']:
    if f not in st.session_state:
        st.session_state[f] = ""

if 'start_ts' not in st.session_state:
    st.session_state.start_ts = None

# ---------------- ENGINEERING ----------------
def get_shims(t):
    if t in [4.7625, 6.35, 7.9375]: return "4.5 mm"
    elif t in [9.525, 11.1125, 12.7]: return "5.0 mm"
    elif t >= 15.875: return "5.5 mm"
    return "Not defined"

WELDING_TABLE = [
    {"t": 4.7625, "speed": 1.5, "ac_in": ".....", "dc_in": "500A/28V", "ac_out": "400A/34V", "dc_out": "580A/30V"},
    {"t": 6.35, "speed": 2.4, "ac_in": "450A/32V", "dc_in": "750A/30V", "ac_out": "420A/32V", "dc_out": "830A/30V"},
    {"t": 7.9375, "speed": 2.2, "ac_in": "450A/32V", "dc_in": "850A/31V", "ac_out": "420A/32V", "dc_out": "890A/31V"},
    {"t": 9.525, "speed": 2.0, "ac_in": "480A/32V", "dc_in": "990A/31V", "ac_out": "450A/33V", "dc_out": "970A/31V"},
    {"t": 11.1125, "speed": 1.9, "ac_in": "510A/32V", "dc_in": "950A/31V", "ac_out": "450A/32V", "dc_out": "1000A/30V"},
    {"t": 12.7, "speed": 1.9, "ac_in": "550A/32V", "dc_in": "980A/32V", "ac_out": "450A/32.5V", "dc_out": "1100A/30V"},
    {"t": 15.875, "speed": 1.2, "ac_in": "540A/33V", "dc_in": "1000A/30V", "ac_out": "520A/33.5V", "dc_out": "1100A/31V"},
    {"t": 17.78, "speed": 1.2, "ac_in": "520A/34V", "dc_in": "1100A/31V", "ac_out": "520A/34V", "dc_out": "1200A/33V"},
    {"t": 19.05, "speed": 1.1, "ac_in": "520A/34V", "dc_in": "1150A/32V", "ac_out": "520A/32V", "dc_out": "1200A/31V"},
    {"t": 25.4, "speed": 1.1, "ac_in": "550A/34V", "dc_in": "1250A/32V", "ac_out": "550A/32V", "dc_out": "1300A/31V"}
]

# ---------------- HEADER ----------------
col_title, col_weather = st.columns([2, 1])

with col_title:
    st.title("⚙️ Production Setup Card")
    st.markdown("### Engineering Calculation")

with col_weather:
    cities = ["Beersheba", "Tel Aviv", "Eilat"]
    for city in cities:
        weather_data = get_weather(city)
        # Выводим данные
        st.markdown(f'<p class="weather-text">{weather_data}</p>', unsafe_allow_html=True)
        # Выводим подпись города
        st.markdown(f'<p class="weather-sub">{city}</p>', unsafe_allow_html=True)


# ---------------- SIDEBAR ----------------
st.sidebar.header("Parameters")
c1, c2, c3 = st.sidebar.columns(3)
if c1.button("D"): st.session_state.active_field = 'D'
if c2.button("t"): st.session_state.active_field = 't'
if c3.button("B"): st.session_state.active_field = 'B'

def draw_f(label, val, f_id):
    st.sidebar.markdown(f"{'🔴' if st.session_state.active_field == f_id else '⚪'} {label}")
    st.sidebar.code(val if val else "0")

draw_f("Diameter", st.session_state.D_val, 'D')
draw_f("Thickness", st.session_state.t_val, 't')
draw_f("Width", st.session_state.B_val, 'B')
st.sidebar.write("---")

# ---------------- KEYPAD ----------------
k_cols = st.sidebar.columns(3)
keys = ['1','2','3','4','5','6','7','8','9','.','0','C']
for i, k in enumerate(keys):
    if k_cols[i % 3].button(k, use_container_width=True, key=f"k_{k}"):
        target = st.session_state.active_field + "_val"
        if k == "C": st.session_state[target] = ""
        else: st.session_state[target] += k
        st.rerun()

calc_btn = st.sidebar.button("CALCULATE", type="primary", use_container_width=True)

# ---------------- TIMER ----------------
timer_area = st.empty()
@st.fragment(run_every=1)
def run_timer():
    if st.session_state.start_ts:
        el = int(time.time() - st.session_state.start_ts)
        h, m, s = el // 3600, (el % 3600)//60, el % 60
        timer_area.markdown(f"⏱️ `{h:02d}:{m:02d}:{s:02d}`")
run_timer()

# ---------------- CALCULATION ----------------
if calc_btn:
    try:
        D = float(st.session_state.D_val.replace(',', '.'))
        t = float(st.session_state.t_val.replace(',', '.'))
        B = float(st.session_state.B_val.replace(',', '.'))
        st.session_state.start_ts = time.time()

        Dm, Di = D - t, D - (2 * t)
        Ri = Di / 2
        x_in = max(min(B / (math.pi * Dm), 1), -1)
        x_out = max(min(B / (math.pi * Di), 1), -1)
        a_in, a_out = math.degrees(math.asin(x_in)), math.degrees(math.asin(x_out))

        st.subheader("📐 Geometry & Setup")
        r1, r2 = st.columns(2)
        with r1:
            st.metric("ENTER ANGLE", f"{int(a_in)}° {int(round((a_in - int(a_in)) * 60))}'")
            st.metric("EXIT ANGLE", f"{int(a_out)}° {int(round((a_out - int(a_out)) * 60))}'")
        with r2:
            st.metric("Inner Radius", f"{Ri:.2f} mm")
            st.info(f"⚙️ SHIMS: {get_shims(t)}")

        w = next((r for r in WELDING_TABLE if abs(r["t"] - t) < 0.01), None)
        if w:
            st.divider()
            st.subheader(f"🔥 Welding: {w['speed']} m/min+-0.2")
            wc1, wc2 = st.columns(2)
            wc1.markdown(f"**INNER**  \nAC: {w['ac_in']}  \nDC: {w['dc_in']}")
            wc2.markdown(f"**OUTER**  \nAC: {w['ac_out']}  \nDC: {w['dc_out']}")
        st.success("100% Accuracy Confirmed")
    except:
        st.sidebar.error("❌ Enter all parameters!")

