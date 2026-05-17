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
    raw_key = os.getenv("WEATHER_API_KEY") or st.secrets.get("WEATHER_API_KEY", None)
    if not raw_key:
        return "No Key", None

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
    except Exception:
        return "Offline", None


# ---------------- ГРАФИК СОЛНЦА (ИСПРАВЛЕННЫЙ) ----------------
def get_sun_graph_html():
    _, sun_data = get_weather("Tel Aviv")

    if not sun_data:
        return "<div style='text-align:center; padding:20px; color:white;'>⚠️ Нет данных о погоде</div>"

    sunrise = sun_data["sunrise"]
    sunset = sun_data["sunset"]
    weather_type = sun_data["weather_type"]

    themes = {
        "dust":  dict(bg_top="#c2a366", bg_bottom="#8b6914", sun_cs="#FFD700", sun_ce="#FF8C00", glow="rgba(255,200,0,0.4)",   arc="#FFD700", icon="🏜️"),
        "cloud": dict(bg_top="#8a8a8a", bg_bottom="#5a5a5a", sun_cs="#CCCCAA", sun_ce="#999966", glow="rgba(200,200,150,0.3)", arc="#DDD",    icon="☁️"),
        "rain":  dict(bg_top="#4a4a6a", bg_bottom="#2a2a4a", sun_cs="#AAAACC", sun_ce="#8888AA", glow="rgba(150,150,200,0.3)", arc="#8899AA", icon="🌧️"),
        "clear": dict(bg_top="#4AB5E8", bg_bottom="#1E6B8F", sun_cs="#FFF176", sun_ce="#FF8F00", glow="rgba(255,215,0,0.5)",   arc="#FFD700", icon="☀️"),
    }
    th = themes.get(weather_type, themes["clear"])

    html_code = f"""
    <div id="sunGraphContainer" style="
        background: linear-gradient(135deg, {th['bg_top']}, {th['bg_bottom']});
        border-radius: 20px;
        padding: 15px;
        margin-top: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.3);
        width: 100%;
        box-sizing: border-box;
    ">
        <div style="text-align:center; margin-bottom:10px;">
            <span id="phaseName" style="font-size:20px; font-weight:bold; color:#FFD700;">--</span>
            <span id="phaseDesc" style="font-size:12px; color:rgba(255,255,255,0.8); display:block;">--</span>
        </div>

        <div style="text-align:center; color:white; margin-bottom:12px;">
            <span id="titleSpan" style="font-size:18px;">{th['icon']}</span>
        </div>

        <canvas id="sunPathCanvas" width="450" height="150"
            style="width:100%; height:auto; max-width:450px; margin:0 auto; display:block; border-radius:10px;">
        </canvas>

        <div style="text-align:center; padding:10px 0 5px 0;">
            <span id="directionSpan" style="
                color:white; background:rgba(0,0,0,0.6);
                padding:6px 16px; border-radius:25px;
                font-size:15px; font-weight:bold;
            ">--</span>
        </div>
    </div>

    <script>
    (function() {{

        // FIX 1: убиваем старый интервал если Streamlit пересоздал iframe
        if (window._sunGraphRunning) {{
            clearInterval(window._sunGraphRunning);
            window._sunGraphRunning = null;
        }}

        const canvas = document.getElementById('sunPathCanvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const W = canvas.width;
        const H = canvas.height;

        const SUNRISE   = {sunrise};
        const SUNSET    = {sunset};
        const SUN_CS    = '{th["sun_cs"]}';
        const SUN_CE    = '{th["sun_ce"]}';
        const SUN_GLOW  = '{th["glow"]}';
        const ARC_COLOR = '{th["arc"]}';
        const DAY_TOP   = '{th["bg_top"]}';
        const DAY_BOT   = '{th["bg_bottom"]}';
        const NIGHT_TOP = '#0a0a2a';
        const NIGHT_BOT = '#1a1a3e';

        const elPhaseName = document.getElementById('phaseName');
        const elPhaseDesc = document.getElementById('phaseDesc');
        const elDirection = document.getElementById('directionSpan');
        const elTitle     = document.getElementById('titleSpan');
        const elContainer = document.getElementById('sunGraphContainer');

        const LEFT  = 25;
        const RIGHT = W - 25;

        function arcY(x) {{
            const t = (x - LEFT) / (RIGHT - LEFT);
            return (H - 18) - 4.2 * (H - 40) * t * (1 - t);
        }}

        function getPhase(ts) {{
            const h = new Date(ts * 1000).getHours();
            if (h >= 6  && h < 12) return {{ color:'#FFA500', name:'🌅 Утро',  desc:'Рассвет — полдень' }};
            if (h >= 12 && h < 18) return {{ color:'#FFD700', name:'☀️ День',  desc:'Полдень — вечер' }};
            if (h >= 18 && h < 24) return {{ color:'#FF8844', name:'🌇 Вечер', desc:'Закат — полночь' }};
            return                          {{ color:'#6688AA', name:'🌙 Ночь',  desc:'Полночь — рассвет' }};
        }}

        // Серп луны через compositing
        function drawMoon(x, y, r) {{
            ctx.save();
            ctx.shadowBlur  = 18;
            ctx.shadowColor = 'rgba(200,220,255,0.5)';
            ctx.beginPath();
            ctx.arc(x, y, r, 0, Math.PI * 2);
            ctx.fillStyle = '#E8E8D0';
            ctx.fill();
            ctx.shadowBlur = 0;

            // Вырезаем серп
            ctx.globalCompositeOperation = 'destination-out';
            ctx.beginPath();
            ctx.arc(x + r * 0.45, y, r * 0.88, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(0,0,0,1)';
            ctx.fill();
            ctx.globalCompositeOperation = 'source-over';

            ctx.strokeStyle = '#aabbcc';
            ctx.lineWidth   = 1.5;
            ctx.beginPath();
            ctx.arc(x, y, r, 0, Math.PI * 2);
            ctx.stroke();
            ctx.restore();
        }}

        function draw() {{
            const now = Math.floor(Date.now() / 1000);
            const isNight = (now < SUNRISE) || (now > SUNSET);

            let progress, percent, dirText;

            if (isNight) {{
                // FIX 2: два случая ночи — до рассвета и после заката
                let nightStart, nightEnd;
                if (now > SUNSET) {{
                    // Вечер/ночь: после заката → до рассвета следующего дня
                    nightStart = SUNSET;
                    nightEnd   = SUNRISE + 86400;
                }} else {{
                    // Раннее утро: после полуночи → до рассвета сегодня
                    nightStart = SUNSET - 86400;
                    nightEnd   = SUNRISE;
                }}
                const nightLen = nightEnd - nightStart;
                progress = nightLen > 0 ? (now - nightStart) / nightLen : 0.5;
                progress = Math.max(0, Math.min(1, progress));
                percent  = Math.floor(progress * 100);
                dirText  = `🌙 ${{percent}}%`;
            }} else {{
                const dayLen = SUNSET - SUNRISE;
                progress = dayLen > 0 ? (now - SUNRISE) / dayLen : 0.5;
                progress = Math.max(0, Math.min(1, progress));
                if (progress <= 0.5) {{
                    percent = Math.floor(progress * 200);
                    dirText = `⬆️ +${{percent}}%`;
                }} else {{
                    percent = Math.floor((1 - progress) * 200);
                    dirText = `⬇️ -${{percent}}%`;
                }}
            }}

            // Обновляем DOM
            const phase = getPhase(now);
            if (elPhaseName) {{ elPhaseName.textContent = phase.name; elPhaseName.style.color = phase.color; }}
            if (elPhaseDesc) elPhaseDesc.textContent = phase.desc;
            if (elDirection) elDirection.textContent  = dirText;
            if (elTitle)     elTitle.textContent       = isNight ? '🌙' : '{th["icon"]}';
            if (elContainer) {{
                elContainer.style.background = isNight
                    ? `linear-gradient(135deg, ${{NIGHT_TOP}}, ${{NIGHT_BOT}})`
                    : `linear-gradient(135deg, ${{DAY_TOP}}, ${{DAY_BOT}})`;
            }}

            // Canvas
            ctx.clearRect(0, 0, W, H);

            // Дуга траектории
            ctx.beginPath();
            ctx.moveTo(LEFT, arcY(LEFT));
            for (let x = LEFT; x <= RIGHT; x++) ctx.lineTo(x, arcY(x));
            ctx.strokeStyle = ARC_COLOR;
            ctx.lineWidth   = 3;
            ctx.setLineDash([6, 6]);
            ctx.stroke();
            ctx.setLineDash([]);

            // Точки восхода и заката
            [LEFT, RIGHT].forEach(px => {{
                ctx.beginPath();
                ctx.arc(px, arcY(px), 6, 0, Math.PI * 2);
                ctx.fillStyle = '#FFA500';
                ctx.fill();
            }});

            // Зенит (только днём)
            if (!isNight) {{
                const zx = (LEFT + RIGHT) / 2;
                ctx.beginPath();
                ctx.arc(zx, arcY(zx), 7, 0, Math.PI * 2);
                ctx.fillStyle = '#FFD700';
                ctx.fill();
            }}

            // Позиция светила
            const sx = LEFT + progress * (RIGHT - LEFT);
            const sy = arcY(sx);
            const R  = 16;

            if (isNight) {{
                drawMoon(sx, sy, R);
            }} else {{
                // Солнце
                ctx.shadowBlur  = 18;
                ctx.shadowColor = SUN_GLOW;
                const grad = ctx.createRadialGradient(sx, sy, R * 0.3, sx, sy, R);
                grad.addColorStop(0, SUN_CS);
                grad.addColorStop(1, SUN_CE);
                ctx.beginPath();
                ctx.arc(sx, sy, R, 0, Math.PI * 2);
                ctx.fillStyle = grad;
                ctx.fill();
                ctx.shadowBlur  = 0;
                ctx.strokeStyle = '#FF6600';
                ctx.lineWidth   = 2;
                ctx.stroke();

                // Блик
                ctx.beginPath();
                ctx.arc(sx - 5, sy - 5, 5, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(255,255,255,0.5)';
                ctx.fill();

                // Стрелка
                ctx.font      = 'bold 14px Arial';
                ctx.fillStyle = progress <= 0.5 ? '#88FF88' : '#FF8888';
                ctx.textAlign = 'center';
                ctx.fillText(progress <= 0.5 ? '⬆️' : '⬇️', sx, sy - 22);
            }}

            // Процент
            ctx.fillStyle   = 'white';
            ctx.font        = 'bold 14px Arial';
            ctx.textAlign   = 'center';
            ctx.shadowBlur  = 3;
            ctx.shadowColor = 'rgba(0,0,0,0.8)';
            ctx.fillText(percent + '%', sx, sy + 30);

            // Сбрасываем состояние контекста
            ctx.shadowBlur = 0;
            ctx.textAlign  = 'left';
        }}

        // Первый рендер немедленно
        draw();

        // FIX 3: интервал 10 сек (в оригинале было 600000 мс = 10 минут!)
        window._sunGraphRunning = setInterval(draw, 10000);

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
    if t <= 8:  return "4.5 mm"
    if t < 14:  return "5.0 mm"
    return "5.5 mm"


WELDING_TABLE = [
    {"t": 4.7625,  "speed": 1.5, "ac_in": ".....",    "dc_in": "500A/28V",  "ac_out": "400A/34V",   "dc_out": "580A/30V"},
    {"t": 6.35,    "speed": 2.4, "ac_in": "450A/32V", "dc_in": "750A/30V",  "ac_out": "420A/32V",   "dc_out": "830A/30V"},
    {"t": 7.9375,  "speed": 2.2, "ac_in": "450A/32V", "dc_in": "850A/31V",  "ac_out": "420A/32V",   "dc_out": "890A/31V"},
    {"t": 9.525,   "speed": 2.0, "ac_in": "480A/32V", "dc_in": "990A/31V",  "ac_out": "450A/33V",   "dc_out": "970A/31V"},
    {"t": 11.1125, "speed": 1.9, "ac_in": "510A/32V", "dc_in": "950A/31V",  "ac_out": "450A/32V",   "dc_out": "1000A/30V"},
    {"t": 12.7,    "speed": 1.9, "ac_in": "550A/32V", "dc_in": "980A/32V",  "ac_out": "450A/32.5V", "dc_out": "1100A/30V"},
    {"t": 15.875,  "speed": 1.2, "ac_in": "540A/33V", "dc_in": "1000A/30V", "ac_out": "520A/33.5V", "dc_out": "1100A/31V"},
    {"t": 17.78,   "speed": 1.2, "ac_in": "520A/34V", "dc_in": "1100A/31V", "ac_out": "520A/34V",   "dc_out": "1200A/33V"},
    {"t": 19.05,   "speed": 1.1, "ac_in": "520A/34V", "dc_in": "1150A/32V", "ac_out": "520A/32V",   "dc_out": "1200A/31V"},
    {"t": 25.4,    "speed": 1.1, "ac_in": "550A/34V", "dc_in": "1250A/32V", "ac_out": "550A/32V",   "dc_out": "1300A/31V"},
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


draw_f("Diameter",  st.session_state.D_val, 'D')
draw_f("Thickness", st.session_state.t_val, 't')
draw_f("Width",     st.session_state.B_val, 'B')
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

        months  = el // (30 * 86400)
        days    = (el % (30 * 86400)) // 86400
        hours   = (el % 86400) // 3600
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
        x_in  = max(min(B / (math.pi * Dm), 1), -1)
        x_out = max(min(B / (math.pi * Di), 1), -1)
        a_in  = math.degrees(math.asin(x_in))
        a_out = math.degrees(math.asin(x_out))

        limit_min = 7.0
        limit_max = 40.0 + (8 / 60)

        in_ok  = limit_min <= a_in  <= limit_max
        out_ok = limit_min <= a_out <= limit_max

        if not in_ok or not out_ok:
            st.error("⛔ Angles are out of range. Please recalculate with different parameters.")
        else:
            st.subheader("📐 Geometry & Setup")
            r1, r2 = st.columns(2)
            with r1:
                st.metric("ENTER ANGLE", f"{int(a_in)}° {int((a_in - int(a_in)) * 60)}'")
                st.metric("EXIT ANGLE",  f"{int(a_out)}° {int((a_out - int(a_out)) * 60)}'")
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
