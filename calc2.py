import streamlit as st
import math
import time
import os

# 1. Настройка страницы (ОБЯЗАТЕЛЬНО ПЕРВАЯ СТРОКА)
st.set_page_config(page_title="Production Setup Pro", page_icon="⚙️", layout="wide")

st.markdown("""
    <style>
    /* Прямое обращение к контейнеру колонок: отключаем перенос строк */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
        gap: 5px !important;
    }

    /* Каждая колонка внутри блока — строго 33% */
    [data-testid="stHorizontalBlock"] > div {
        width: 33% !important;
        flex: 1 1 33% !important;
        min-width: 0 !important; /* Убираем минимальную ширину, которая всё ломает */
    }

    /* Настройка самих кнопок */
    .stButton > button {
        width: 100% !important;
        height: 50px !important;
        font-size: 20px !important;
        padding: 0 !important;
    }

    /* Возвращаем нормальный вид на компьютере (чтобы не был слишком мелким) */
    @media (min-width: 800px) {
        [data-testid="stHorizontalBlock"] {
            gap: 10px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)


# --- ФУНКЦИИ ДЛЯ РАБОТЫ С ФАЙЛОМ ВРЕМЕНИ ---
TIME_FILE = "last_calc_time.txt"


def save_calc_time():
    with open(TIME_FILE, "w") as f:
        f.write(str(time.time()))


def load_calc_time():
    if os.path.exists(TIME_FILE):
        with open(TIME_FILE, "r") as f:
            try:
                return float(f.read())
            except:
                return None
    return None


# 2. Инициализация памяти (Session State)
if 'active_field' not in st.session_state: st.session_state.active_field = 'D'
if 'D_val' not in st.session_state: st.session_state.D_val = ""
if 't_val' not in st.session_state: st.session_state.t_val = ""
if 'B_val' not in st.session_state: st.session_state.B_val = ""

# Таблица режимов сварки
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


def get_shims(t):
    if t in [4.7625, 6.35, 7.9375]:
        return "4.5 mm"
    elif t in [9.525, 11.1125, 12.7]:
        return "5.0 mm"
    elif t >= 15.875:
        return "5.5 mm"
    return "Not defined"


def get_welding_data(t):
    for row in WELDING_TABLE:
        if abs(row["t"] - t) < 0.001: return row
    return None


def add_num(char):
    target = st.session_state.active_field + '_val'
    if char == "C":
        st.session_state[target] = ""
    else:
        st.session_state[target] += str(char)


# 3. Боковая панель (Управление)
st.sidebar.header("Entering parameters")
c_sel = st.sidebar.columns(3)
if c_sel[0].button("D", use_container_width=True): st.session_state.active_field = 'D'
if c_sel[1].button("t", use_container_width=True): st.session_state.active_field = 't'
if c_sel[2].button("B", use_container_width=True): st.session_state.active_field = 'B'


def display_field(label, val, field_id):
    icon = "🔴" if st.session_state.active_field == field_id else "⚪"
    st.sidebar.markdown(f"{icon} {label}")
    st.sidebar.code(val if val else "0", language="text")


display_field("Diameter (D), mm", st.session_state.D_val, 'D')
display_field("Thickness (t), mm", st.session_state.t_val, 't')
display_field("Width (B), mm", st.session_state.B_val, 'B')

st.sidebar.write("---")
k_cols = st.sidebar.columns(3)
keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '0', 'C']
for i, key in enumerate(keys):
    if k_cols[i % 3].button(key, use_container_width=True, key=f"k_{key}"):
        add_num(key)
        st.rerun()

calc_btn = st.sidebar.button("CALCULATE", type="primary", use_container_width=True)

# 4. Основной экран
st.title("⚙️ Production Setup Card")
st.markdown("### Engineering Calculation")

timer_placeholder = st.empty()

if calc_btn:
    try:
        D = float(st.session_state.D_val.replace(',', '.')) if st.session_state.D_val else 0
        t = float(st.session_state.t_val.replace(',', '.')) if st.session_state.t_val else 0
        B = float(st.session_state.B_val.replace(',', '.')) if st.session_state.B_val else 0

        if D > 0 and t > 0 and B > 0:
            save_calc_time()
            Dm, Di = D - t, D - (2 * t)
            Ri = Di / 2
            alf_in = math.degrees(math.asin(B / (math.pi * Dm)))
            d_in, m_in = int(alf_in), int(round((alf_in - int(alf_in)) * 60))
            alf_out = math.degrees(math.asin(B / (math.pi * Di)))
            d_out, m_out = int(alf_out), int(round((alf_out - int(alf_out)) * 60))

            st.subheader("📐 Geometry & Setup")
            res_col = st.columns(2)
            with res_col[0]:
                st.metric("ENTER ANGLE", f"{d_in}° {m_in}'")
                st.metric("EXIT ANGLE", f"{d_out}° {m_out}'")
            with res_col[1]:
                st.metric("Inner Radius", f"{Ri:.2f} mm")
                st.info(f"⚙️ **SHIMS:** {get_shims(t)}")

            # Сварка
            w_data = get_welding_data(t)
            if w_data:
                st.divider()
                st.subheader(f"🔥 Welding: {w_data['speed']} m/min+-0.2")
                wc1, wc2 = st.columns(2)

                with wc1:
                    # Используем markdown с <br> для переноса строки
                    st.markdown(f"**INNER WELD**  \nAC: {w_data['ac_in']}  \nDC: {w_data['dc_in']}")

                with wc2:
                    st.markdown(f"**OUTER WELD**  \nAC: {w_data['ac_out']}  \nDC: {w_data['dc_out']}")

            st.markdown("""
                <div style="font-style: italic; color: #4CAF50; border-left: 5px solid #4CAF50; padding-left: 10px; margin-top: 20px;">
                    <strong>Accuracy defeats chaos:</strong> Trigonometry and calculations are always more reliable than intuition. 
                    <strong>Automation sets the mind free.</strong>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Please enter parameters")
    except:
        st.error("Check input values")

# --- ЛОГИКА ТАЙМЕРА (С ОБНОВЛЕНИЕМ) ---
start_timestamp = load_calc_time()
if start_timestamp:
    elapsed = int(time.time() - start_timestamp)
    days = elapsed // 86400
    hrs, mins, secs = (elapsed % 86400) // 3600, (elapsed % 3600) // 60, elapsed % 60
    t_str = f"{days}d {hrs:02d}:{mins:02d}:{secs:02d}" if days > 0 else f"{hrs:02d}:{mins:02d}:{secs:02d}"
    timer_placeholder.markdown(f"⏱️ **Time since setup:** `{t_str}`")
    time.sleep(1)
    st.rerun()



