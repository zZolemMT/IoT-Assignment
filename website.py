# imports
from machine import Pin, time_pulse_us
import dht
import json
import network
import socket
import time
import rp2

# variables for the sensors and stuff on breadboard like led's
sensor = dht.DHT11(Pin(13))
cooling_led = Pin(0, Pin.OUT)
irrigation_led = Pin(1, Pin.OUT)
trig = Pin(14, Pin.OUT)
echo = Pin(15, Pin.IN)

# settings and variables for the webpage and thresholds
temp_threshold = 24
humidity_threshold = 40
water_threshold = 20
empty_cm = 20.0
full_cm = 5.0
interval = 60

# files
LOG_FILE = "readings.txt"
SETTINGS_FILE = "settings.json"

# for networking
rp2.country('AU')
ssid = "iPhone"
password = 'password'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

max_wait = 20
while max_wait > 0:
    if wlan.status() >= 3:
        break
    max_wait -= 1
    time.sleep(1)

if wlan.status() != 3:
    raise RuntimeError('Network connection failed')

print("Connected! IP:", wlan.ifconfig()[0])

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
previous_socket = globals().get('s')
if previous_socket is not None:
    previous_socket.close()
s = socket.socket()
s.bind(addr)
s.listen(1)
s.settimeout(1)
print('Listening on', addr)

temperature = None
humidity = None
sensor_error = False
distance = None
water_level = None
water_error = False
cooling = False
irrigation = False
low_water = False
start_time = time.time()
last_measure = time.ticks_add(time.ticks_ms(), -interval * 1000)
last_water = time.ticks_add(time.ticks_ms(), -2000)


def save_settings():
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump({
                "temp_threshold": temp_threshold,
                "humidity_threshold": humidity_threshold,
                "water_threshold": water_threshold,
                "empty_cm": empty_cm,
                "full_cm": full_cm,
                "interval": interval
            }, f)
    except OSError as e:
        print("Could not save settings:", e)


def load_settings():
    global temp_threshold, humidity_threshold, water_threshold
    global empty_cm, full_cm, interval
    try:
        with open(SETTINGS_FILE) as f:
            data = json.load(f)
        temp_threshold = data.get("temp_threshold", temp_threshold)
        humidity_threshold = data.get("humidity_threshold", humidity_threshold)
        water_threshold = data.get("water_threshold", water_threshold)
        empty_cm = data.get("empty_cm", empty_cm)
        full_cm = data.get("full_cm", full_cm)
        interval = data.get("interval", interval)
    except (OSError, ValueError):
        pass


def read_distance_once():
    trig.value(0)
    time.sleep_us(5)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    duration = time_pulse_us(echo, 1, 30000)
    if duration < 0:
        return None
    return duration * 0.0343 / 2


def read_distance():
    samples = []
    for _ in range(5):
        d = read_distance_once()
        if d is not None:
            samples.append(d)
        time.sleep_ms(60)
    if not samples:
        return None
    samples.sort()
    return samples[len(samples) // 2]


def update_outputs():
    global cooling, irrigation, low_water
    low_water = water_level is not None and water_level < water_threshold
    if temperature is not None:
        cooling = temperature > temp_threshold
        cooling_led.value(1 if cooling else 0)
    if humidity is not None:
        irrigation = humidity < humidity_threshold and not low_water
        irrigation_led.value(1 if irrigation else 0)


def update_water():
    global distance, water_level, water_error
    d = read_distance()
    if d is None:
        distance = None
        water_level = None
        water_error = True
        return
    distance = round(d, 1)
    span = empty_cm - full_cm
    if span <= 0:
        level = 0
    else:
        level = (empty_cm - d) / span * 100
    water_level = int(max(0, min(100, level)))
    water_error = False


def take_reading():
    global temperature, humidity, sensor_error
    try:
        sensor.measure()
        temperature = sensor.temperature()
        humidity = sensor.humidity()
        sensor_error = False
        update_outputs()
        with open(LOG_FILE, "a") as f:
            f.write("{}s, {}C, {}%, water={}%, cooling={}, irrigation={}\n".format(
                time.time() - start_time, temperature, humidity,
                water_level, cooling, irrigation))
    except OSError as e:
        print("DHT read failed:", e)
        temperature = None
        humidity = None
        sensor_error = True


def get_param(path, name):
    if "?" not in path:
        return None
    for pair in path.split("?", 1)[1].split("&"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            if k == name:
                return v
    return None


def state_json():
    return json.dumps({
        "temperature": temperature,
        "humidity": humidity,
        "sensor_error": sensor_error,
        "distance": distance,
        "water_level": water_level,
        "water_error": water_error,
        "low_water": low_water,
        "cooling": cooling,
        "irrigation": irrigation,
        "temp_threshold": temp_threshold,
        "humidity_threshold": humidity_threshold,
        "water_threshold": water_threshold,
        "empty_cm": empty_cm,
        "full_cm": full_cm,
        "interval": interval
    })


load_settings()

html = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Smart Farming Dashboard</title>
<style>
    :root {
        --bg: #eef5ee;
        --card: #ffffff;
        --text: #1e2d1f;
        --muted: #6b7d6c;
        --green: #2e9e4f;
        --green-dark: #23793c;
        --red: #d9534f;
        --blue: #2f80c9;
        --border: #dbe7dc;
    }
    * { box-sizing: border-box; }
    body {
        margin: 0;
        font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background: var(--bg);
        color: var(--text);
    }
    header {
        background: linear-gradient(135deg, #2e9e4f, #1f7a3a);
        color: #fff;
        padding: 28px 20px;
        text-align: center;
    }
    header h1 { margin: 0; font-size: 1.7rem; }
    header p { margin: 6px 0 0; opacity: 0.85; font-size: 0.95rem; }
    main { max-width: 720px; margin: 0 auto; padding: 20px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .wide { grid-column: 1 / -1; }
    .card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    .card h2 {
        margin: 0 0 10px;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--muted);
    }
    .value { font-size: 2.4rem; font-weight: 700; }
    .sub { color: var(--muted); font-size: 0.85rem; margin-top: 4px; }
    .badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 1.1rem;
        background: #e8ece8;
        color: var(--muted);
    }
    .badge.on-cool { background: #dcecfa; color: var(--blue); }
    .badge.on-water { background: #dcf3e2; color: var(--green-dark); }
    .badge.warn { background: #fbe1e0; color: var(--red); }
    .tank {
        height: 22px;
        background: #e3ecf4;
        border-radius: 999px;
        overflow: hidden;
        margin: 12px 0 8px;
    }
    .tank-fill {
        height: 100%;
        width: 0%;
        background: linear-gradient(90deg, #5aa9e6, #2f80c9);
        transition: width 0.4s ease;
    }
    .tank-fill.low { background: linear-gradient(90deg, #e8847f, #d9534f); }
    .water-top { display: flex; justify-content: space-between; align-items: baseline; }
    .settings { margin-top: 16px; }
    label { display: block; font-size: 0.9rem; margin-bottom: 4px; color: var(--muted); }
    input[type=number] {
        width: 100%;
        padding: 10px 12px;
        font-size: 1rem;
        border: 1px solid var(--border);
        border-radius: 8px;
        margin-bottom: 14px;
        background: #fafdfa;
    }
    input[type=number]:focus { outline: 2px solid var(--green); border-color: transparent; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    button {
        background: var(--green);
        color: #fff;
        border: none;
        padding: 11px 22px;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 8px;
        cursor: pointer;
    }
    button:hover { background: var(--green-dark); }
    button.alt { background: var(--blue); }
    button.alt:hover { background: #256aa6; }
    .btns { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
    .msg { margin-left: 12px; color: var(--green-dark); font-weight: 600; }
    .help { color: var(--muted); font-size: 0.9rem; margin: 0 0 8px; line-height: 1.4; }
    @media (max-width: 520px) {
        .grid { grid-template-columns: 1fr; }
        .row { grid-template-columns: 1fr; }
    }
</style>
</head>
<body>
<header>
    <h1>&#127793; Smart Farming Dashboard</h1>
    <p>Live greenhouse monitoring and automation</p>
</header>
<main>
    <div class="grid">
        <div class="card">
            <h2>Temperature</h2>
            <div class="value" id="temperature">--</div>
            <div class="sub">Cooling on above <span id="tt">--</span> &deg;C</div>
        </div>
        <div class="card">
            <h2>Humidity</h2>
            <div class="value" id="humidity">--</div>
            <div class="sub">Irrigation on below <span id="ht">--</span> %</div>
        </div>
        <div class="card wide">
            <div class="water-top">
                <h2>Water Tank</h2>
                <span class="badge" id="waterbadge">--</span>
            </div>
            <div class="value" id="water">--</div>
            <div class="tank"><div class="tank-fill" id="tankfill"></div></div>
            <div class="sub">Sensor distance: <span id="dist">--</span> cm &middot; Low water below <span id="wt">--</span> %</div>
        </div>
        <div class="card">
            <h2>Cooling (GP0)</h2>
            <span class="badge" id="cooling">--</span>
        </div>
        <div class="card">
            <h2>Irrigation (GP1)</h2>
            <span class="badge" id="irrigation">--</span>
        </div>
    </div>

    <div class="card settings">
        <h2>Threshold Settings</h2>
        <div class="row">
            <div>
                <label for="temp_threshold">Cooling above (&deg;C)</label>
                <input type="number" id="temp_threshold">
            </div>
            <div>
                <label for="humidity_threshold">Irrigation below (%)</label>
                <input type="number" id="humidity_threshold">
            </div>
            <div>
                <label for="water_threshold">Low water below (%)</label>
                <input type="number" id="water_threshold" min="0" max="100">
            </div>
            <div>
                <label for="interval">Read temp/humidity every (sec)</label>
                <input type="number" id="interval" min="2">
            </div>
        </div>
        <button onclick="saveSettings()">Save</button>
        <span class="msg" id="saved"></span>
    </div>

    <div class="card settings">
        <h2>Water Sensor Calibration</h2>
        <p class="help">1. Leave the tank empty and press <b>Set empty (0%)</b>.<br>
        2. Fill the tank to the level you want as full and press <b>Set full (100%)</b>.</p>
        <p class="help">Current distance: <b><span id="dist2">--</span> cm</b> &middot;
        Empty = <b><span id="ecm">--</span> cm</b> &middot; Full = <b><span id="fcm">--</span> cm</b></p>
        <div class="btns">
            <button class="alt" onclick="calibrate('empty')">Set empty (0%)</button>
            <button class="alt" onclick="calibrate('full')">Set full (100%)</button>
        </div>
        <span class="msg" id="calmsg"></span>
    </div>
</main>

<script>
    let inputsFilled = false;
    const $ = function (id) { return document.getElementById(id); };

    function setBadge(id, on, onClass, onText, offText) {
        const el = $(id);
        el.textContent = on ? onText : offText;
        el.className = 'badge ' + (on ? onClass : '');
    }

    function show(state) {
        $('temperature').textContent = state.temperature === null
            ? (state.sensor_error ? 'Read failed' : '--') : state.temperature + ' °C';
        $('humidity').textContent = state.humidity === null
            ? (state.sensor_error ? 'Read failed' : '--') : state.humidity + ' %';
        $('tt').textContent = state.temp_threshold;
        $('ht').textContent = state.humidity_threshold;
        $('wt').textContent = state.water_threshold;
        $('ecm').textContent = state.empty_cm;
        $('fcm').textContent = state.full_cm;
        const d = state.distance === null ? '--' : state.distance;
        $('dist').textContent = d;
        $('dist2').textContent = d;

        if (state.water_level === null) {
            $('water').textContent = state.water_error ? 'Read failed' : '--';
            $('tankfill').style.width = '0%';
            $('waterbadge').textContent = '--';
            $('waterbadge').className = 'badge';
        } else {
            $('water').textContent = state.water_level + ' %';
            $('tankfill').style.width = state.water_level + '%';
            $('tankfill').className = 'tank-fill' + (state.low_water ? ' low' : '');
            $('waterbadge').textContent = state.low_water ? 'LOW WATER' : 'OK';
            $('waterbadge').className = 'badge ' + (state.low_water ? 'warn' : 'on-water');
        }

        setBadge('cooling', state.cooling, 'on-cool', 'ON', 'OFF');
        setBadge('irrigation', state.irrigation, 'on-water', 'ON', 'OFF');

        if (!inputsFilled) {
            $('temp_threshold').value = state.temp_threshold;
            $('humidity_threshold').value = state.humidity_threshold;
            $('water_threshold').value = state.water_threshold;
            $('interval').value = state.interval;
            inputsFilled = true;
        }
    }

    async function updateStatus() {
        try {
            const response = await fetch('/state', { cache: 'no-store' });
            show(await response.json());
        } catch (error) {
            $('temperature').textContent = 'No connection';
            $('humidity').textContent = 'No connection';
            $('water').textContent = 'No connection';
        }
    }

    function flash(id, text) {
        $(id).textContent = text;
        setTimeout(function () { $(id).textContent = ''; }, 2500);
    }

    async function saveSettings() {
        const url = '/set?temp=' + encodeURIComponent($('temp_threshold').value) +
                    '&hum=' + encodeURIComponent($('humidity_threshold').value) +
                    '&water=' + encodeURIComponent($('water_threshold').value) +
                    '&interval=' + encodeURIComponent($('interval').value);
        try {
            const response = await fetch(url, { cache: 'no-store' });
            show(await response.json());
            flash('saved', 'Saved \\u2713');
        } catch (error) {
            flash('saved', 'Save failed');
        }
    }

    async function calibrate(point) {
        try {
            const response = await fetch('/cal?point=' + point, { cache: 'no-store' });
            const state = await response.json();
            show(state);
            flash('calmsg', (point === 'empty' ? 'Empty' : 'Full') + ' set \\u2713');
        } catch (error) {
            flash('calmsg', 'Calibration failed');
        }
    }

    updateStatus();
    setInterval(updateStatus, 1000);
</script>
</body>
</html>
"""

while True:
    now = time.ticks_ms()
    if time.ticks_diff(now, last_measure) >= interval * 1000:
        take_reading()
        last_measure = now
    if time.ticks_diff(now, last_water) >= 2000:
        update_water()
        update_outputs()
        last_water = now

    cl = None
    try:
        cl, addr = s.accept()
    except OSError:
        continue

    try:
        request = cl.recv(1024)
        request_line = request.split(b"\r\n", 1)[0].decode()
        parts = request_line.split(" ")
        path = parts[1] if len(parts) > 1 else "/"

        if path.startswith("/set"):
            try:
                new_temp = get_param(path, "temp")
                new_hum = get_param(path, "hum")
                new_water = get_param(path, "water")
                new_interval = get_param(path, "interval")
                if new_temp:
                    temp_threshold = int(new_temp)
                if new_hum:
                    humidity_threshold = int(new_hum)
                if new_water:
                    water_threshold = max(0, min(100, int(new_water)))
                if new_interval:
                    interval = max(2, int(new_interval))
                update_outputs()
                save_settings()
            except ValueError:
                print("Bad settings value")
            body = state_json()
            content_type = "application/json; charset=UTF-8"
        elif path.startswith("/cal"):
            point = get_param(path, "point")
            d = read_distance()
            if d is not None:
                if point == "empty":
                    empty_cm = round(d, 1)
                elif point == "full":
                    full_cm = round(d, 1)
                save_settings()
                update_water()
                update_outputs()
            body = state_json()
            content_type = "application/json; charset=UTF-8"
        elif path.startswith("/state"):
            body = state_json()
            content_type = "application/json; charset=UTF-8"
        else:
            body = html
            content_type = "text/html; charset=UTF-8"

        body_bytes = body.encode("utf-8")
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: " + content_type + "\r\n"
            "Content-Length: " + str(len(body_bytes)) + "\r\n"
            "Cache-Control: no-store\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).encode("utf-8") + body_bytes
        cl.sendall(response)

    except Exception as e:
        print("Server error:", e)

    finally:
        if cl:
            cl.close()
