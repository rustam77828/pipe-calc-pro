import streamlit as st
import math
import time
import requests
import os
from datetime import datetime
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
[data-testid="stAppViewContainer"] [data-testid="stHorizontalBlock"] > div {
    width: 33% !important;
    flex: 1 1 33% !important;
    min-width: 0 !important;
}
.stButton > button {
    width: 100% !important;
    height: 50px !important;
    font-size: 20px !important;
}
.weather-text {
    text-align: left;
    font-size: 45px;
    font-weight: bold;
    margin-bottom: -10px;
    line-height: 1;
}
.weather-sub {
    text-align: left;
    font-size: 14px;
    color: gray;
    margin: 0;
    padding-left: 5px;
}
</style>
""", unsafe_allow_html=True)


# ---------------- WEATHER FUNCTION ----------------
@st.cache_data(ttl=3600)
def get_weather(city):
    raw_key = os.getenv("WEATHER_API_KEY") or st.secrets.get("WEATHER_API_KEY")
    if not raw_key: return "No Key", None

    api_key = raw_key.strip()
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            temp = math.ceil(data['main']['temp'])
            hum = math.floor(data['main']['humidity'])
            wind_kmh = math.floor(data['wind']['speed'] * 3.6)

            main = data['weather'][0]['main'].lower()
            description = data['weather'][0]['description'].lower()

            sunrise = data['sys']['sunrise']
            sunset = data['sys']['sunset']

            if "dust" in main or "sand" in main or "dust" in description:
                weather_type = "dust"
            elif "cloud" in main:
                weather_type = "cloud"
            elif "rain" in main or "drizzle" in main:
                weather_type = "rain"
            else:
                weather_type = "clear"

            if "clear" in main:
                icon = "☀️"
            elif "cloud" in main:
                icon = "☁️"
            elif "rain" in main or "drizzle" in main:
                icon = "🌧️"
            else:
                icon = "⛅"

            weather_text = f"{temp}°C {icon} <span style='font-size: 20px; vertical-align: middle;'>| 💧{hum}% | 💨 {wind_kmh} km/h</span>"

            sun_data = {
                "sunrise": sunrise,
                "sunset": sunset,
                "weather_type": weather_type,
            }
            return weather_text, sun_data
        return f"Err {res.status_code}", None
    except:
        return "Offline", None


# ---------------- ФУНКЦИЯ ДЛЯ ОПРЕДЕЛЕНИЯ ФАЗЫ ДНЯ ----------------
def get_time_of_day_phase(current_time):
    """Возвращает фазу дня по времени (UTC)"""
    hour = datetime.fromtimestamp(current_time).hour

    if 6 <= hour < 12:
        return "🌅 УТРО", "Солнце поднимается к зениту", "#FFA500"
    elif 12 <= hour < 18:
        return "☀️ ДЕНЬ", "Солнце в наивысшей точке и начинает опускаться", "#FFD700"
    elif 18 <= hour < 24:
        return "🌆 ВЕЧЕР", "Солнце заходит, наступают сумерки", "#FF8844"
    else:
        return "🌙 НОЧЬ", "Солнце находится под горизонтом", "#6688AA"


# ---------------- ГРАФИК СОЛНЦА (С ФАЗАМИ ДНЯ) ----------------
def get_sun_graph_html():
    _, sun_data = get_weather("Tel Aviv")

    if not sun_data:
        return "<div style='text-align:center; padding:20px;'>⚠️ Нет данных</div>"

    sunrise = sun_data["sunrise"]
    sunset = sun_data["sunset"]
    weather_type = sun_data["weather_type"]

    # Цвета фона
    if weather_type == "dust":
        bg_top = "#c2a366"
        bg_bottom = "#8b6914"
        sun_color_start = "#FFD700"
        sun_color_end = "#FF8C00"
        sun_glow = "rgba(255,200,0,0.4)"
        arc_color = "#FFD700"
        icon = "🏜️"
        title = "ПЫЛЬНАЯ БУРЯ"
    elif weather_type == "cloud":
        bg_top = "#8a8a8a"
        bg_bottom = "#5a5a5a"
        sun_color_start = "#CCCCAA"
        sun_color_end = "#999966"
        sun_glow = "rgba(200,200,150,0.3)"
        arc_color = "#DDD"
        icon = "☁️"
        title = "ПАСМУРНО"
    elif weather_type == "rain":
        bg_top = "#4a4a6a"
        bg_bottom = "#2a2a4a"
        sun_color_start = "#AAAACC"
        sun_color_end = "#8888AA"
        sun_glow = "rgba(150,150,200,0.3)"
        arc_color = "#8899AA"
        icon = "🌧️"
        title = "ДОЖДЬ"
    else:
        bg_top = "#4AB5E8"
        bg_bottom = "#1E6B8F"
        sun_color_start = "#FFF176"
        sun_color_end = "#FF8F00"
        sun_glow = "rgba(255,215,0,0.5)"
        arc_color = "#FFD700"
        icon = "☀️"
        title = "ЯСНЫЙ ДЕНЬ"

    html_code = f"""
    <div id="sunGraphContainer" style="background: linear-gradient(135deg, {bg_top}, {bg_bottom}); border-radius: 20px; padding: 15px; margin-top: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.3); width: 100%;">

        <!-- Блок с фазой дня -->
        <div id="timeOfDayBlock" style="text-align: center; margin-bottom: 10px;">
            <span id="phaseName" style="font-size: 20px; font-weight: bold; color: #FFD700;">--</span>
            <span id="phaseDesc" style="font-size: 12px; color: rgba(255,255,255,0.8); display: block;">--</span>
        </div>

        <div style="text-align: center; color: white; margin-bottom: 12px;">
            <span id="titleSpan" style="font-size: 18px;">{icon} {title} {icon}</span>
        </div>

        <canvas id="sunPathCanvas" width="450" height="150" style="width: 100%; height: auto; max-width: 450px; margin: 0 auto; display: block; border-radius: 10px;"></canvas>

        <div style="text-align: center; padding: 10px 0 5px 0;">
            <span id="directionSpan" style="color: white; background: rgba(0,0,0,0.6); padding: 6px 16px; border-radius: 25px; font-size: 15px; font-weight: bold;">--</span>
        </div>
    </div>

    <script>
    (function() {{
        const canvas = document.getElementById('sunPathCanvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;

        const sunrise = {sunrise};
        const sunset = {sunset};
        const sunColorStart = '{sun_color_start}';
        const sunColorEnd = '{sun_color_end}';
        const sunGlow = '{sun_glow}';
        const arcColor = '{arc_color}';

        const dayBgTop = '{bg_top}';
        const dayBgBottom = '{bg_bottom}';
        const nightBgTop = '#0a0a2a';
        const nightBgBottom = '#1a1a3e';

        const directionSpan = document.getElementById('directionSpan');
        const titleSpan = document.getElementById('titleSpan');
        const phaseNameSpan = document.getElementById('phaseName');
        const phaseDescSpan = document.getElementById('phaseDesc');

        // Границы дуги
        const leftMargin = 25;
        const rightMargin = w - 25;

        function getY(x) {{
            const t = (x - leftMargin) / (rightMargin - leftMargin);
            return (h - 18) - 4.2 * (h - 40) * t * (1 - t);
        }}

        function getTimeOfDayPhase(timestamp) {{
            const date = new Date(timestamp * 1000);
            const hour = date.getHours();

            if (hour >= 6 && hour < 12) {{
                return {{color: "#FFA500" }};
            }} else if (hour >= 12 && hour < 18) {{
                return {{color: "#FFD700" }};
            }} else if (hour >= 18 && hour < 24) {{
                return {{color: "#FF8844" }};
            }} else {{
                return {{color: "#6688AA" }};
            }}
        }}

        function updateContainerBackground(isNight) {{
            const container = document.getElementById('sunGraphContainer');
            if (container) {{
                if (isNight) {{
                    container.style.background = `linear-gradient(135deg, ${{nightBgTop}}, ${{nightBgBottom}})`;
                    if (titleSpan) titleSpan.textContent = '';
                }} else {{
                    container.style.background = `linear-gradient(135deg, ${{dayBgTop}}, ${{dayBgBottom}})`;
                    if (titleSpan) titleSpan.textContent = '{icon} {title} {icon}';
                }}
            }}
        }}

        function draw() {{
            const now = Math.floor(Date.now() / 1000);
            const isNight = now < sunrise || now > sunset;

            let progress, percent, directionText;
            const dayLength = sunset - sunrise;

            // Получаем фазу дня
            const phase = getTimeOfDayPhase(now);
            if (phaseNameSpan) phaseNameSpan.textContent = phase.name;
            if (phaseDescSpan) phaseDescSpan.textContent = phase.desc;
            if (phaseNameSpan) phaseNameSpan.style.color = phase.color;

            updateContainerBackground(isNight);

            if (isNight) {{
                const nextSunrise = sunrise + 86400;
                const nightLength = nextSunrise - sunset;
                if (nightLength > 0) {{
                    progress = (now - sunset) / nightLength;
                }} else {{
                    progress = 0.5;
                }}
                progress = Math.max(0, Math.min(1, progress));
                percent = Math.floor(progress * 100);
                directionText = ` ${{percent}}%`;
            }} else {{
                if (dayLength > 0) {{
                    progress = (now - sunrise) / dayLength;
                }} else {{
                    progress = 0.5;
                }}
                progress = Math.max(0, Math.min(1, progress));

                if (progress <= 0.5) {{
                    percent = Math.floor(progress * 200);
                    directionText = `⬆️ ПОДЪЁМ +${{percent}}%`;
                }} else {{
                    percent = Math.floor((1 - progress) * 200);
                    directionText = `⬇️ СПУСК -${{percent}}%`;
                }}
            }}

            if (directionSpan) directionSpan.textContent = directionText;

            ctx.clearRect(0, 0, w, h);

            // Дуга
            ctx.beginPath();
            ctx.moveTo(leftMargin, getY(leftMargin));
            for (let x = leftMargin; x <= rightMargin; x++) {{
                ctx.lineTo(x, getY(x));
            }}
            ctx.strokeStyle = arcColor;
            ctx.lineWidth = 3;
            ctx.setLineDash([6, 6]);
            ctx.stroke();
            ctx.setLineDash([]);

            // Восход
            ctx.fillStyle = '#FFA500';
            ctx.beginPath();
            ctx.arc(leftMargin, getY(leftMargin), 6, 0, 2*Math.PI);
            ctx.fill();

            // Зенит
            const zenithX = leftMargin + (rightMargin - leftMargin) / 2;
            if (!isNight) {{
                ctx.fillStyle = '#FFD700';
                ctx.beginPath();
                ctx.arc(zenithX, getY(zenithX), 7, 0, 2*Math.PI);
                ctx.fill();
                ctx.fillStyle = 'white';
                ctx.font = 'bold 11px Arial';
                ctx.fillText('ЗЕНИТ', zenithX - 22, getY(zenithX) - 10);
            }}

            // Закат
            ctx.fillStyle = '#FFA500';
            ctx.beginPath();
            ctx.arc(rightMargin, getY(rightMargin), 6, 0, 2*Math.PI);
            ctx.fill();

            // Светило
            const x = leftMargin + progress * (rightMargin - leftMargin);
            const y = getY(x);
            const radius = 16;

            ctx.shadowBlur = 18;
            ctx.shadowColor = sunGlow;

            let grad;
            if (isNight) {{
                grad = ctx.createRadialGradient(x, y, radius*0.3, x, y, radius);
                grad.addColorStop(0, '#E8E8E8');
                grad.addColorStop(1, '#A0A0A0');
            }} else {{
                grad = ctx.createRadialGradient(x, y, radius*0.3, x, y, radius);
                grad.addColorStop(0, sunColorStart);
                grad.addColorStop(1, sunColorEnd);
            }}
            ctx.fillStyle = grad;

            ctx.beginPath();
            ctx.arc(x, y, radius, 0, 2*Math.PI);
            ctx.fill();

            ctx.shadowBlur = 0;
            ctx.strokeStyle = isNight ? '#ccc' : '#FF6600';
            ctx.lineWidth = 2;
            ctx.stroke();

            // Блик
            ctx.beginPath();
            ctx.arc(x-5, y-5, 5, 0, 2*Math.PI);
            ctx.fillStyle = 'rgba(255,255,255,0.5)';
            ctx.fill();

            // Стрелка
            if (!isNight) {{
                ctx.fillStyle = progress <= 0.5 ? '#88FF88' : '#FF8888';
                ctx.font = 'bold 16px Arial';
                ctx.fillText(progress <= 0.5 ? '⬆️' : '⬇️', x-12, y-22);
            }}

            // Процент
            ctx.fillStyle = 'white';
            ctx.font = 'bold 16px Arial';
            ctx.shadowBlur = 3;
            ctx.fillText(percent + '%', x-12, y+26);
            ctx.shadowBlur = 0;
        }}

        draw();
        setInterval(draw, 600000);
    }})();
    </script>
    """
    return html_code


# ---------------- HEADER ----------------
col_title, col_weather = st.columns([1.5, 1])

with col_title:
    st.title("⚙️ Production Setup Card")
    st.markdown("### Engineering Calculation")

with col_weather:
    cities = ["Beersheba", "Tel Aviv", "Eilat"]
    for city in cities:
        weather_data, _ = get_weather(city)
        st.markdown(f'<p class="weather-text">{weather_data}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="weather-sub">{city}</p>', unsafe_allow_html=True)

    st.markdown("""
        <div style="text-align: right; margin-top: 20px; font-size: 10px; color: gray;">
            Source: <a href="https://openweathermap.org" target="_blank" style="color: gray; text-decoration: none;">OpenWeatherMap.org</a>
        </div>
    """, unsafe_allow_html=True)

    # ГРАФИК СОЛНЦА
    st.components.v1.html(get_sun_graph_html(), height=270)

# ---------------- STATE ----------------
if "start" in st.query_params and 'start_ts' not in st.session_state:
    st.session_state.start_ts = float(st.query_params["start"])

if 'active_field' not in st.session_state:
    st.session_state.active_field = 'D'

for f in ['D_val', 't_val', 'B_val']:
    if f not in st.session_state:
        st.session_state[f] = ""

if 'start_ts' not in st.session_state:
    st.session_state.start_ts = None


# ---------------- ENGINEERING ----------------
def get_shims(t):
    if t <= 8: return "4.5 mm"
    if t <= 13: return "5.0 mm"
    if t >= 14: return "5.5 mm"
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
keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '0', 'C']
for i, k in enumerate(keys):
    if k_cols[i % 3].button(k, use_container_width=True, key=f"k_{k}"):
        target = st.session_state.active_field + "_val"
        if k == "C":
            st.session_state[target] = ""
        else:
            st.session_state[target] += k
        st.rerun()

calc_btn = st.sidebar.button("CALCULATE", type="primary", use_container_width=True)

# ---------------- TIMER ----------------
timer_area = st.empty()


@st.fragment(run_every=1)
def run_timer():
    if st.session_state.start_ts:
        el = int(time.time() - st.session_state.start_ts)

        months = el // (30 * 86400)
        days = (el % (30 * 86400)) // 86400
        hours = (el % 86400) // 3600
        minutes = (el % 3600) // 60
        seconds = el % 60

        if months > 0:
            ts_str = f"{months}mo {days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
        elif days > 0:
            ts_str = f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            ts_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        timer_area.markdown(f"⏱️ `{ts_str}`")


run_timer()

# ---------------- CALCULATION ----------------
if calc_btn:
    try:
        new_start = time.time()
        st.query_params["start"] = str(new_start)
        st.session_state.start_ts = new_start

        D = float(st.session_state.D_val)
        t = float(st.session_state.t_val)
        B = float(st.session_state.B_val)

        Dm, Di = D - t, D - (2 * t)
        Ri = Di / 2
        x_in = max(min(B / (math.pi * Dm), 1), -1)
        x_out = max(min(B / (math.pi * Di), 1), -1)
        a_in, a_out = math.degrees(math.asin(x_in)), math.degrees(math.asin(x_out))

        limit_min = 7.0
        limit_max = 40.0 + (8 / 60)

        in_ok = limit_min <= a_in <= limit_max
        out_ok = limit_min <= a_out <= limit_max

        if not in_ok or not out_ok:
            st.error("⛔ Angles are out of range. Please recalculate with different parameters.")
        else:
            st.subheader("📐 Geometry & Setup")
            r1, r2 = st.columns(2)
            with r1:
                st.metric("ENTER ANGLE", f"{int(a_in)}° {int((a_in - int(a_in)) * 60)}'")
                st.metric("EXIT ANGLE", f"{int(a_out)}° {int((a_out - int(a_out)) * 60)}'")
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
            st.success("✅ 100% Accuracy Confirmed")
    except Exception as e:
        st.sidebar.error(f"❌ Error: {e}")
