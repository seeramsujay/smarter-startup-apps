import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

try:
    from flask import Flask, render_template_string
except ImportError:
    print("[GhostOS] Flask not installed. Run: pip install flask")
    sys.exit(1)

from analysis.patterns import hourly_pattern, top_apps
from core.feedback import adaptive_predict_for_hour
from core.paths import DB_PATH

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Ghost OS X Dashboard</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #1a1a2e; color: #fff; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { margin: 0; font-size: 2.5em; color: #e94560; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: #16213e; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .card h2 { margin-top: 0; color: #0f3460; font-size: 1.2em; border-bottom: 2px solid #0f3460; padding-bottom: 10px; color: #43bccd; }
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #2a2a4e; }
        th { color: #888; }
        .prediction { font-size: 1.5em; text-align: center; color: #4ade80; margin: 20px 0; }
        .conf { font-size: 0.6em; color: #aaa; }
        .status { text-align: center; margin-top: 30px; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Ghost OS X</h1>
            <p>Activity Intelligence Engine</p>
        </div>
        
        <div class="card" style="margin-bottom: 20px;">
            <h2>Current Prediction (Hour: {{ hour }}:00)</h2>
            {% if prediction %}
                <div class="prediction">
                    {{ prediction[0] }} <span class="conf">({{ prediction[1] }}% confidence, {{ prediction[2] }})</span>
                </div>
            {% else %}
                <div class="prediction" style="color: #666;">No prediction available</div>
            {% endif %}
        </div>

        <div class="grid">
            <div class="card">
                <h2>Top Applications</h2>
                <table>
                    <tr><th>App</th><th>Time (min)</th></tr>
                    {% for app, total in apps[:5] %}
                    <tr><td>{{ app }}</td><td>{{ "%.1f"|format(total/60) }}</td></tr>
                    {% endfor %}
                </table>
            </div>

            <div class="card">
                <h2>Hourly Pattern</h2>
                <table>
                    <tr><th>Hour</th><th>Dominant App</th></tr>
                    {% for h in sorted_hours %}
                    <tr><td>{{ h }}:00</td><td>{{ hours[h] }}</td></tr>
                    {% endfor %}
                </table>
            </div>
        </div>

        <div class="status">
            Database: {{ db_path }}
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    if not os.path.exists(DB_PATH):
        return "No data available. Run 'ghostos track' first."

    hour = datetime.now().strftime("%H")
    prediction = None
    try:
        result = adaptive_predict_for_hour(hour)
        if result and result[0]:
            prediction = result
    except Exception:
        pass

    apps = top_apps()
    hours = hourly_pattern()
    sorted_hours = sorted(list(hours.keys()))

    return render_template_string(
        TEMPLATE,
        hour=hour,
        prediction=prediction,
        apps=apps,
        hours=hours,
        sorted_hours=sorted_hours,
        db_path=DB_PATH,
    )


def main():
    print("[GhostOS] Starting dashboard on http://localhost:5000")
    try:
        app.run(host="127.0.0.1", port=5000)
    except Exception as e:
        print(f"[GhostOS] Failed to start dashboard: {e}")


if __name__ == "__main__":
    main()
