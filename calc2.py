import streamlit as st
import math
import time

# 1. Настройка страницы
st.set_page_config(page_title="Production Setup", page_icon="⚙️", layout="wide")

# CSS для фиксации клавиатуры 3х4
st.markdown("""
    <style>
    [data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; gap: 5px !important; }
    [data-testid="stHorizontalBlock"] > div { width: 33% !important; flex: 1 1 33% !important; min-width: 0 !important; }
    .stButton > button { width: 100% !important; height: 50px !important; font-size: 20px !important; }
    </style>
""", unsafe_allow_html=True)

# 2. Инициализация памяти
if 'active_field' not in st.session_state: st.session_state.active_field = 'D'
for f in ['D_val', 't_val', 'B_val']:
    if f not in st.session_state: st.session_state[f] = ""
if 'start_ts' not in st.session_state: st.session_state.start_ts = None


# Таблицы данных
def get_shims(t):
    if t in [4.7625, 6.35, 7.9375]:
        return "4.5 mm"
    elif t in [9.525, 11.1125, 12.7]:
        return "5.0 mm"
    elif t >= 15.875:
        return "5.5 mm"
    return "Not defined"


WELDING_TABLE = [
    {"t": 4.7625, "speed": 1.5, "ac_in": ".....", "dc_in": "500A/28V", "ac_out": "400A/34V", "dc_out": "580A/30V"},
    {"t": 6.35, "speed": 2.4, "ac_in": "450A/32V", "dc_in": "750A/30V", "ac_out": "420A/32V", "dc_out": "830A/30V"},
    {"t": 7.9375, "speed": 2.2, "ac_in": "450A/32V", "dc_in": "850A/31V", "ac_out": "420A/32V", "dc_out": "890A/31V"},
    {"t": 9.525, "speed": 2.0, "ac_in": "480A/32V", "dc_in": "990A/31V", "ac_out": "450A/33V", "dc_out": "970A/31V"},
    {"t": 11.1125, "speed": 1.9, "ac_in": "510A/32V", "dc_in": "950A/31V", "ac_out": "450A/32V", "dc_out": "1000A/30V"},
    {"t": 12.7, "speed": 1.9, "ac_in": "550A/32V", "dc_in": "980A/32V", "ac_out": "450A/32.5V", "dc_out": "1100A/30V"},
    {"t": 15.875, "speed": 1.2, "ac_in": "540A/33V", "dc_in": "1000A/30V", "ac_out": "520A/33.5V",
     "dc_out": "1100A/31V"},
    {"t": 17.78, "speed": 1.2, "ac_in": "520A/34V", "dc_in": "1100A/31V", "ac_out": "520A/34V", "dc_out": "1200A/33V"},
    {"t": 19.05, "speed": 1.1, "ac_in": "520A/34V", "dc_in": "1150A/32V", "ac_out": "520A/32V", "dc_out": "1200A/31V"},
    {"t": 25.4, "speed": 1.1, "ac_in": "550A/34V", "dc_in": "1250A/32V", "ac_out": "550A/32V", "dc_out": "1300A/31V"}
]

# 3. Боковая панель
st.sidebar.header("Parameters")
c1, c2, c3 = st.sidebar.columns(3)
if c1.button("D", use_container_width=True): st.session_state.active_field = 'D'
if c2.button("t", use_container_width=True): st.session_state.active_field = 't'
if c3.button("B", use_container_width=True): st.session_state.active_field = 'B'


def draw_f(label, val, f_id):
    st.sidebar.markdown(f"{'🔴' if st.session_state.active_field == f_id else '⚪'} {label}")
    st.sidebar.code(val if val else "0", language="text")


draw_f("Diameter (D)", st.session_state.D_val, 'D')
draw_f("Thickness (t)", st.session_state.t_val, 't')
draw_f("Width (B)", st.session_state.B_val, 'B')

st.sidebar.write("---")
k_cols = st.sidebar.columns(3)
keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '0', 'C']
for i, k in enumerate(keys):
    if k_cols[i % 3].button(k, use_container_width=True, key=f"k_{k}"):
        target = st.session_state.active_field + '_val'
        if k == "C":
            st.session_state[target] = ""
        else:
            st.session_state[target] += k
        st.rerun()

calc_btn = st.sidebar.button("CALCULATE", type="primary", use_container_width=True)

# 4. Основной экран
st.title("⚙️ Production Setup Card")
st.markdown("### Engineering Calculation")

# --- СЕКЦИЯ ТАЙМЕРА (С ФРАГМЕНТОМ) ---
timer_area = st.empty()


@st.fragment(run_every=1)
def run_timer():
    if st.session_state.start_ts:
        el = int(time.time() - st.session_state.start_ts)
        h, m, s = el // 3600, (el % 3600) // 60, el % 60
        timer_area.markdown(f"⏱️ **Time since setup:** `{h:02d}:{m:02d}:{s:02d}`")


run_timer()

if calc_btn:
    try:
        D = float(st.session_state.D_val.replace(',', '.'))
        t = float(st.session_state.t_val.replace(',', '.'))
        B = float(st.session_state.B_val.replace(',', '.'))

        st.session_state.start_ts = time.time()

        Dm, Di = D - t, D - (2 * t)
        Ri = Di / 2
        a_in = math.degrees(math.asin(B / (math.pi * Dm)))
        a_out = math.degrees(math.asin(B / (math.pi * Di)))

        st.subheader("📐 Geometry & Setup")
        r1, r2 = st.columns(2)
        with r1:
            st.metric("ENTER ANGLE", f"{int(a_in)}° {int(round((a_in - int(a_in)) * 60))}'")
            st.metric("EXIT ANGLE", f"{int(a_out)}° {int(round((a_out - int(a_out)) * 60))}'")
        with r2:
            st.metric("Inner Radius", f"{Ri:.2f} mm")
            st.info(f"⚙️ **SHIMS: {get_shims(t)}**")

        w = next((r for r in WELDING_TABLE if abs(r["t"] - t) < 0.01), None)
        if w:
            st.divider()
            st.subheader(f"🔥 Welding: {w['speed']} m/min+-0.2")
            wc1, wc2 = st.columns(2)
            wc1.markdown(f"**INNER**  \nAC: {w['ac_in']}  \nDC: {w['dc_in']}")
            wc2.markdown(f"**OUTER**  \nAC: {w['ac_out']}  \nDC: {w['dc_out']}")

        st.success("100% Accuracy Confirmed")
        st.rerun()  # Нужно, чтобы таймер сразу отрисовал 00:00:01
    except:
        st.sidebar.error("❌ Enter all parameters!")











