# 模擬 Oddspedia 抓資料（未串接 API，日後可用 Selenium/Requests 完整替換）
from datetime import datetime
from predict import analyze_and_predict

def fetch_all_odds_report(keyword=None):
    now = datetime.now().strftime("%m/%d %H:%M")
    text = f"📊 賠率分析更新時間：{now}\n\n"

    sample_matches = [
        {
            "sport": "⚽ 各國足球",
            "time": "21:00",
            "match": "利物浦 vs 曼城",
            "team": "利物浦",
            "odds": "+1.5"
        },
        {
            "sport": "🏀 美國籃球",
            "time": "08:30",
            "match": "湖人 vs 勇士",
            "team": "大分",
            "odds": "228.5"
        },
        {
            "sport": "⚾ 台韓日美棒球",
            "time": "17:00",
            "match": "阪神虎 vs 巨人",
            "team": "巨人",
            "odds": "-1.5"
        }
    ]

    for item in sample_matches:
        if keyword and keyword not in item["match"]:
            continue
        analysis = analyze_and_predict(item["match"], item["team"], item["odds"])
        text += f"{item['sport']}\n🕓 {item['time']}｜{item['match']}\n推薦：{item['team']} {item['odds']}\n分析：{analysis}\n\n"

    return text.strip()
