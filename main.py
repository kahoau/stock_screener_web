import os
import re
import markdown
from flask import Flask, render_template_string, send_from_directory
from datetime import datetime

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_DIR, "stock_analysis_report")

# 统一命名：holding（替换原holdings）
REGIONS = ["HK", "US"]
CATEGORIES = ["holding", "market", "strong_trend", "watch"]


def init_folders():
    today = datetime.now().strftime("%Y%m%d")
    for reg in REGIONS:
        for cat in CATEGORIES:
            cat_path = os.path.join(DATA_ROOT, reg, cat)
            os.makedirs(cat_path, exist_ok=True)

            today_path = os.path.join(cat_path, today)
            img_path = os.path.join(today_path, "img")
            audio_path = os.path.join(today_path, "audio")
            os.makedirs(today_path, exist_ok=True)
            os.makedirs(img_path, exist_ok=True)
            os.makedirs(audio_path, exist_ok=True)


# 图片路由
@app.route("/data/<region>/<category>/<date>/img/<filename>")
def serve_image(region, category, date, filename):
    img_path = os.path.join(DATA_ROOT, region, category, date, "img")
    return send_from_directory(img_path, filename)


# 音频路由（支持MP3播放）
@app.route("/data/<region>/<category>/<date>/audio/<filename>")
def serve_audio(region, category, date, filename):
    audio_path = os.path.join(DATA_ROOT, region, category, date, "audio")
    return send_from_directory(audio_path, filename)


# 主页
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
        <a class="btn btn-hk" href="/list/HK/holding">holding</a>
        <a class="btn btn-hk" href="/list/HK/market">market</a>
        <a class="btn btn-hk" href="/list/HK/strong_trend">strong_trend</a>
        <a class="btn btn-hk" href="/list/HK/watch">watch</a>
    </div>
    <div class="section">
        <h2>美國市場</h2>
        <a class="btn btn-us" href="/list/US/holding">holding</a>
        <a class="btn btn-us" href="/list/US/market">market</a>
        <a class="btn btn-us" href="/list/US/strong_trend">strong_trend</a>
        <a class="btn btn-us" href="/list/US/watch">watch</a>
    </div>
    """
    return render_template_string(html)


# 日期列表页
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
            {"".join([f'<li><a href="/stocks/{region}/{category}/{d}">{d}</a></li>' for d in dates])}
        </ul>
    </div>
    """
    return render_template_string(html)


# 股票列表页（日期下的所有股票）
@app.route("/stocks/<region>/<category>/<date>")
def stock_list(region, category, date):
    if region not in REGIONS or category not in CATEGORIES:
        return "Invalid path", 404

    date_folder = os.path.join(DATA_ROOT, region, category, date)
    if not os.path.exists(date_folder):
        return f"日期 {date} 不存在", 404

    # 获取该日期下所有MD报告
    md_files = [f for f in os.listdir(date_folder) if f.endswith(".md")]
    md_files.sort()

    html = f"""
    <div style="max-width: 600px; margin: 30px auto; padding:0 20px;">
        <h1>{date} - {region} {category}</h1>
        <a href="/list/{region}/{category}" style="font-size:18px;">⬅ 返回日期</a>
        <h3>股票分析報告列表</h3>
        <ul style="font-size:18px; line-height:1.8;">
            {"".join([f'<li><a href="/content/{region}/{category}/{date}/{os.path.splitext(f)[0]}">{f}</a></li>' for f in md_files])}
        </ul>
    </div>
    """
    return render_template_string(html)


# 股票详情页（含图片+音频播放）
@app.route("/content/<region>/<category>/<date>/<report_name>")
def show_content(region, category, date, report_name):
    if region not in REGIONS or category not in CATEGORIES:
        return "Invalid path", 404

    date_folder = os.path.join(DATA_ROOT, region, category, date)
    md_filename = f"{report_name}.md"
    md_path = os.path.join(date_folder, md_filename)

    # ✅ 核心优化：提取股票代码，简化标题
    # 从 report_name 中提取股票代码（比如从 HK_strong_trend_0700HK_20260216 提取 0700HK）
    stock_code_match = re.search(r"(\d+[A-Z]+)", report_name)
    stock_code = stock_code_match.group(1) if stock_code_match else "未知股票"

    # 美化分类名称（比如 strong_trend → Strong Trend）
    pretty_category = category.replace("_", " ").title()
    # 美化地区名称（HK → Hong Kong，US → US）
    pretty_region = "Hong Kong" if region == "HK" else "US"

    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        # 修复图片路径
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

        # 修复音频路径并转为播放控件
        md_content = re.sub(
            r"\]\(\./audio/([^)]+\.mp3)\)",
            f"](/data/{region}/{category}/{date}/audio/\\1)",
            md_content
        )
        md_content = re.sub(
            r"\]\(audio/([^)]+\.mp3)\)",
            f"](/data/{region}/{category}/{date}/audio/\\1)",
            md_content
        )

        # 将MP3链接转为音频播放控件
        def replace_audio_link(match):
            filename = match.group(1)
            url = match.group(2)
            return f'<audio controls style="width: 300px; margin: 5px 0;" src="{url}">{filename}'

        md_content = re.sub(r"\[([^\]]+\.mp3)\]\(([^)]+)\)", replace_audio_link, md_content)

        # MD转HTML
        html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    else:
        html_content = f"<p>暫無內容：找不到 {md_filename}</p>"

    # ✅ 优化后的标题格式：「股票代码 | 地区 | 分类 | 日期」
    html = f"""
    <style>
    .content-container {{
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
        line-height: 1.8;
    }}
    .content-container h1 {{
        color: #2c3e50;
        font-size: 24px;
        margin-bottom: 15px;
        text-align: center;
    }}
    img {{
        max-width: 100%;
        height: auto;
        display: block;
        margin: 10px auto;
        border-radius: 8px;
    }}
    audio {{
        display: block;
        margin: 10px 0;
    }}
    .back-link {{
        color: #007bff;
        text-decoration: none;
        font-size: 16px;
        margin-bottom: 20px;
        display: inline-block;
    }}
    .back-link:hover {{
        text-decoration: underline;
    }}
    </style>
    <div class="content-container">
        <a href="/stocks/{region}/{category}/{date}" class="back-link">⬅ 返回報告列表</a>
        <h1>{stock_code} | {pretty_region} | {pretty_category} | {date}</h1>
        <hr>
        {html_content}
    </div>
    """
    return render_template_string(html)


if __name__ == "__main__":
    init_folders()
    print("✅ Stock screener Web 啟動：http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)