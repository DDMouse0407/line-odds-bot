# ... (前略，import 與變數不變)

@app.route("/")
def home():
    return "✅ LINE Bot 全功能啟動中（v3 SDK）"

@app.route("/callback", methods=["POST"])  # ✅ LINE 預設路徑
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Webhook Error:", e)
        abort(400)

    return "OK"

@app.route("/test", methods=["GET"])
def test_push():
    text = generate_odds_report()
    message = TextMessage(text=text)
    line_bot_api.push_message(PushMessageRequest(to=USER_ID, messages=[message]))
    return "✅ 已手動推播測試內容"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()
    
    if text.startswith("/查詢"):
        query = text.replace("/查詢", "").strip()
        reply_text = query_odds(query)
    else:
        reply_text = "✅ 指令成功！目前支援：\n/test（手動推播）\n/查詢 [隊伍或聯賽]"

    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
    )

# === 推播分析邏輯 ===

def generate_odds_report():
    try:
        now = datetime.now().strftime("%m/%d %H:%M")
        text = f"📊 賠率分析更新時間：{now}\n\n"

        text += "⚽ 各國足球\n"
        text += "🕓 18:00｜利物浦 vs 曼城\n推薦：利物浦 +1.5\n分析：主隊近期連勝，客隊傷兵多\n\n"

        text += "🏀 美國籃球\n"
        text += "🕓 20:30｜湖人 vs 勇士\n推薦：大分 228.5\n分析：兩隊對戰常爆分 + 防守鬆散\n\n"

        text += "⚾ 台韓日美棒球\n"
        text += "🕓 17:00｜阪神虎 vs 巨人\n推薦：巨人 -1.5\n分析：主投ERA極低 + 主場優勢明顯\n\n"

        return text
    except Exception as e:
        return f"❌ 賠率分析錯誤：{str(e)}"

def query_odds(keyword):
    if "湖人" in keyword:
        return "🏀 湖人賽事推薦：\n🕓 20:30｜湖人 vs 勇士\n推薦：大分 228.5\n分析：高得分趨勢 + 對戰歷史爆分"
    return f"❌ 查無 {keyword} 相關資料"

# === 定時推播 ===

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', minute='0')  # 每小時整點推播一次
def auto_push():
    try:
        text = generate_odds_report()
        message = TextMessage(text=text)
        line_bot_api.push_message(PushMessageRequest(to=USER_ID, messages=[message]))
        print("✅ 自動推播完成")
    except Exception as e:
        print("❌ 自動推播失敗：", e)

scheduler.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
