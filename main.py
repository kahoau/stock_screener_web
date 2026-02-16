import os
import re
import markdown
from flask import Flask, render_template_string, send_from_directory
from datetime import datetime

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_DIR, "stock_analysis_report")

REGIONS = ["HK", "US"]
CATEGORIES = ["holdings", "market", "strong_trend", "watch"]


def init_folders():
    today = datetime.now().strftime("%Y%m%d")
    for reg in REGIONS:
        for cat in CATEGORIES:
            cat_path = os.path.join(DATA_ROOT, reg, cat)
            os.makedirs(cat_path, exist_ok=True)

            today_path = os.path.join(cat_path, today)
            img_path = os.path.join(today_path, "img")
            os.makedirs(today_path, exist_ok=True)
            os.makedirs(img_path, exist_ok=True)

            md_filename = f"{reg.lower()}_{cat}_report_{today}.md"
            md_path = os.path.join(today_path, md_filename)
            if not os.path.exists(md_path):
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(f"# {today} {reg} {cat}\n\n")
                    f.write("![Sample Image](./img/img1.jpg)\n")


# -------------------
# Correct Image Route (Critical Fix!)
# -------------------
@app.route("/data/<region>/<category>/<date>/img/<filename>")
def serve_image(region, category, date, filename):
    img_path = os.path.join(DATA_ROOT, region, category, date, "img")
    print(f"Loading image from: {img_path}/{filename}")
    return send_from_directory(img_path, filename)


# -------------------
# Home Page (Updated Display Text)
# -------------------
@app.route("/")
def index():
    html = """
    <style>
    .section {
        max-width: 360px;
        margin: 30px auto;
        padding: 0 20px;
    }
    .section h2 {
        text-align: center;
        margin-bottom: 15px;
        color: #222;
    }
    .btn {
        display: block;
        width: 100%;
        margin: 8px 0;
        padding: 14px;
        font-size: 16px;
        border-radius: 10px;
        border: none;
        background: #0d6efd;
        color: white;
        cursor: pointer;
        text-align: center;
        text-decoration: none;
    }
    .btn-hk {
        background: #007bff;
    }
    .btn-us {
        background: #28a745;
    }
    .btn:hover {
        opacity: 0.9;
    }
    h1 {
        text-align: center;
        margin-top: 20px;
    }
    </style>

    <h1>Stock screener</h1>
    <div class="section">
        <h2>香港市場</h2>
        <a class="btn btn-hk" href="/list/HK/holdings">holdings</a>
        <a class="btn btn-hk" href="/list/HK/market">market</a>
        <a class="btn btn-hk" href="/list/HK/strong_trend">strong_trend</a>
        <a class="btn btn-hk" href="/list/HK/watch">watch</a>
    </div>
    <div class="section">
        <h2>美國市場</h2>
        <a class="btn btn-us" href="/list/US/holdings">holdings</a>
        <a class="btn btn-us" href="/list/US/market">market</a>
        <a class="btn btn-us" href="/list/US/strong_trend">strong_trend</a>
        <a class="btn btn-us" href="/list/US/watch">watch</a>
    </div>
    """
    return render_template_string(html)


# -------------------
# Date List Page
# -------------------
@app.route("/list/<region>/<category>")
def date_list(region, category):
    if region not in REGIONS or category not in CATEGORIES:
        return "Error", 404

    folder = os.path.join(DATA_ROOT, region, category)
    dates = [d for d in os.listdir(folder) if re.fullmatch(r"\d{8}", d)]
    dates.sort(reverse=True)

    html = f"""
    <div style="max-width: 400px; margin: 30px auto; padding:0 20px;">
        <h1>{region} {category}</h1>
        <a href="/" style="font-size:18px;">⬅ 返回主頁</a>
        <h3>日期列表</h3>
        <ul style="font-size:18px; line-height:1.8;">
            {"".join([f'<li><a href="/content/{region}/{category}/{d}">{d}</a></li>' for d in dates])}
        </ul>
    </div>
    """
    return render_template_string(html)


# -------------------
# Content Page (Fixed Image Path Conversion)
# -------------------
@app.route("/content/<region>/<category>/<date>")
def show_content(region, category, date):
    if region not in REGIONS or category not in CATEGORIES:
        return "Invalid path", 404

    date_folder = os.path.join(DATA_ROOT, region, category, date)
    md_filename = f"{region.lower()}_{category}_report_{date}.md"
    md_path = os.path.join(date_folder, md_filename)

    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        md_content = md_content.replace("\\", "/")
        md_content = re.sub(
            r"\]\(\./img/([^)]+)\)",
            f"](/data/{region}/{category}/{date}/img/\\1)",
            md_content
        )
        md_content = re.sub(
            r"\]\(img/([^)]+)\)",
            f"](/data/{region}/{category}/{date}/img/\\1)",
            md_content
        )

        html_content = markdown.markdown(md_content)
    else:
        html_content = f"<p>暫無內容：找不到 {md_filename}</p>"

    html = f"""
    <style>
    .content-container {{
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
        line-height: 1.8;
    }}
    img {{
        max-width: 100%;
        height: auto;
        display: block;
        margin: 10px auto;
        border-radius: 8px;
    }}
    </style>
    <div class="content-container">
        <h1>{date} - {region} {category}</h1>
        <a href="/list/{region}/{category}">⬅ 返回日期</a>
        <hr>
        {html_content}
    </div>
    """
    return render_template_string(html)


if __name__ == "__main__":
    init_folders()
    print("✅ Stock screener Web 啟動：http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)