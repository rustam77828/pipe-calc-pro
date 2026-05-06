import streamlit as st
import math
import time
import requests
import os
from dotenv import load_dotenv
from streamlit_js_eval import get_geolocation

load_dotenv()

st.set_page_config(page_title="Production Setup", page_icon="⚙️", layout="wide")

# --- CSS ---
st.markdown("""
<style>
[data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; gap: 5px !important; }
[data-testid="stHorizontalBlock"] > div { width: 33% !important; flex: 1 1 33% !important; min-width: 0 !important; }
.stButton > button { width: 100% !important; height: 50px !important; font-size: 20px !important; }
.weather-text { text-align: right; font-size: 40px; font-weight: bold; margin-bottom: -5px; }
.weather-sub { text-align: right; font-size: 14px; color: gray; margin: 0; }
.weather-icon { text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- ПОГОДА С КЭШЕМ ---
@st.cache_data(ttl=600)
def get_weather(lat=None, lon=None):
    raw_key = os.getenv("WEATHER_API_KEY") or st.secrets.get("WEATHER_API_KEY")
    if not raw_key:
        return "No Key", "", ""

    api_key = raw_key.strip()

    if lat and lon:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    else:
        url = f"https://api.openweathermap.org/data/2.5/weather?q=Beersheba&appid={api_key}&units=metric"

    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            temp = int(data['main']['temp'])
            city = data['name']
            icon_code = data['weather'][0]['icon']

            icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"

            return f"{temp}°C", city, icon_url
        else:
            return f"Error {res.status_code}", "", ""
    except:
        return "Conn Error", "", ""

# --- ГЕОЛОКАЦИЯ ---
geo = get_geolocation()
lat, lon = None, None

if geo and "coords" in geo:
    lat = geo["coords"]["latitude"]
    lon = geo["coords"]["longitude"]

# --- HEADER ---
col_title, col_weather = st.columns([2, 1])

with col_title:
    st.title("⚙️ Production Setup Card")
    st.markdown("### Engineering Calculation")

with col_weather:
    weather, city, icon = get_weather(lat, lon)

    if icon:
        st.markdown(f'<div class="weather-icon"><img src="{icon}" width="70"></div>', unsafe_allow_html=True)

    st.markdown(f'<p class="weather-text">{weather}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="weather-sub">{city}</p>', unsafe_allow_html=True)

# --- STATE ---
if 'active_field' not in st.session_state: st.session_state.active_field = 'D'
for f in ['D_val', 't_val', 'B_val']:
    if f not in st.session_state: st.session_state[f] = ""
if 'start_ts' not in st.session_state: st.session_state.start_ts = None

# --- FUNCTIONS ---
def get_shims(t):
    if t in [4.7625, 6.35, 7.9375]:
        return "4.5 mm"
    elif t in [9.525, 11.1125, 12.7]:
        return "5.0 mm"
    elif t >= 15.875:
        return "5.5 mm"
    return "Not defined"

WELDING_TABLE = [
    {"t": 6.35, "speed": 2.4, "ac_in": "450A/32V", "dc_in": "750A/30V", "ac_out": "420A/32V", "dc_out": "830A/30V"},
    {"t": 12.7, "speed": 1.9, "ac_in": "550A/32V", "dc_in": "980A/32V", "ac_out": "450A/32.5V", "dc_out": "1100A/30V"}
]

# --- SIDEBAR ---
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

# --- TIMER ---
timer_area = st.empty()

@st.fragment(run_every=1)
def run_timer():
    if st.session_state.start_ts:
        el = int(time.time() - st.session_state.start_ts)
        h, m, s = el // 3600, (el % 3600)//60, el % 60
        timer_area.markdown(f"⏱️ `{h:02d}:{m:02d}:{s:02d}`")

run_timer()

# --- CALC ---
if st.sidebar.button("CALCULATE"):
    try:
        D = float(st.session_state.D_val)
        t = float(st.session_state.t_val)
        B = float(st.session_state.B_val)

        st.session_state.start_ts = time.time()

        Dm = D - t
        Di = D - 2*t
        Ri = Di / 2

        a_in = math.degrees(math.asin(B / (math.pi * Dm)))
        a_out = math.degrees(math.asin(B / (math.pi * Di)))

        st.subheader("Geometry")
        st.metric("Enter Angle", f"{a_in:.2f}°")
        st.metric("Exit Angle", f"{a_out:.2f}°")
        st.metric("Inner Radius", f"{Ri:.2f} mm")
        st.info(f"SHIMS: {get_shims(t)}")

    except:
        st.error("Error input")
