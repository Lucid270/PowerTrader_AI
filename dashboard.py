
from flask import Flask, render_template_string, jsonify, request
import os
import subprocess
import signal
import threading
import time
import json


app = Flask(__name__)
TRADER_PROCESS = None
TRADER_LOCK = threading.Lock()
TRADER_CMD = ["python", "pt_trader.py"]


# --- Trading Bot Controls ---
def is_trader_running():
    with TRADER_LOCK:
        global TRADER_PROCESS
        return TRADER_PROCESS is not None and TRADER_PROCESS.poll() is None

def start_trader():
    with TRADER_LOCK:
        global TRADER_PROCESS
        if is_trader_running():
            return False
        TRADER_PROCESS = subprocess.Popen(TRADER_CMD)
        return True

def stop_trader():
    with TRADER_LOCK:
        global TRADER_PROCESS
        if TRADER_PROCESS and TRADER_PROCESS.poll() is None:
            TRADER_PROCESS.terminate()
            try:
                TRADER_PROCESS.wait(timeout=5)
            except subprocess.TimeoutExpired:
                TRADER_PROCESS.kill()
            TRADER_PROCESS = None
            return True
        return False

@app.route("/")
def home():
    return render_template_string('''
    <html>
    <head>
        <title>PowerTrader Dashboard</title>
        <style>
            body { background: #181c24; color: #eee; font-family: sans-serif; }
            .logbox { background: #222; color: #eee; padding: 1em; max-height: 40vh; overflow: auto; }
            .controls { margin-bottom: 1em; }
            button { margin-right: 1em; padding: 0.5em 1em; }
            #chart { background: #fff; }
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
        function fetchLog() {
            fetch('/log').then(r => r.json()).then(data => {
                document.getElementById('log').textContent = data.log;
            });
        }
        function fetchStatus() {
            fetch('/status').then(r => r.json()).then(data => {
                document.getElementById('status').textContent = data.running ? 'Running' : 'Stopped';
            });
        }
        function startTrader() {
            fetch('/start', {method: 'POST'}).then(_ => { fetchStatus(); });
        }
        function stopTrader() {
            fetch('/stop', {method: 'POST'}).then(_ => { fetchStatus(); });
        }
        function fetchChart() {
            fetch('/chart').then(r => r.json()).then(data => {
                const ctx = document.getElementById('chart').getContext('2d');
                if(window.accountChart) window.accountChart.destroy();
                window.accountChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Account Value',
                            data: data.values,
                            borderColor: '#00FF66',
                            backgroundColor: 'rgba(0,255,102,0.1)',
                            fill: true,
                        }]
                    },
                    options: {
                        scales: { x: { display: false }, y: { beginAtZero: true } },
                        plugins: { legend: { labels: { color: '#eee' } } }
                    }
                });
            });
        }
        setInterval(fetchLog, 2000);
        setInterval(fetchStatus, 2000);
        setInterval(fetchChart, 10000);
        window.onload = function() { fetchLog(); fetchStatus(); fetchChart(); };
        </script>
    </head>
    <body>
        <h2>PowerTrader Dashboard</h2>
        <div class="controls">
            <b>Status:</b> <span id="status">...</span>
            <button onclick="startTrader()">Start Bot</button>
            <button onclick="stopTrader()">Stop Bot</button>
        </div>
        <h3>Trainer Log</h3>
        <pre id="log" class="logbox">Loading...</pre>
        <h3>Account Value</h3>
        <canvas id="chart" width="800" height="200"></canvas>
    </body>
    </html>
    ''')


# --- API Endpoints ---
@app.route('/log')
def log():
    log_content = ''
    if os.path.exists('trainer.log'):
        with open('trainer.log') as f:
            log_content = f.read()[-10000:]
    return jsonify({'log': log_content})

@app.route('/status')
def status():
    return jsonify({'running': is_trader_running()})

@app.route('/start', methods=['POST'])
def start():
    ok = start_trader()
    return jsonify({'started': ok})

@app.route('/stop', methods=['POST'])
def stop():
    ok = stop_trader()
    return jsonify({'stopped': ok})

@app.route('/chart')
def chart():
    # Read account value history
    path = os.path.join('hub_data', 'account_value_history.jsonl')
    labels, values = [], []
    if os.path.exists(path):
        with open(path) as f:
            for line in list(f)[-200:]:
                try:
                    rec = json.loads(line)
                    labels.append(time.strftime('%H:%M', time.localtime(rec['ts'])))
                    values.append(rec['total_account_value'])
                except Exception:
                    continue
    return jsonify({'labels': labels, 'values': values})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
