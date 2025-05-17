from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import schedule
import time
import threading
import requests

app = Flask(__name__)

# 用環境變數管理密鑰
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
USER_ID = os.getenv("USER_ID")  # 你的 LINE 個人 ID，用於推播

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/")
def home():
    return "LINE Bot 已部署成功！"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# 處理文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == "/test":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="你好，我收到你的訊息了！")
        )

# 🕒 自動推播函式（每小時）
def push_odds_data():
    try:
        # 範例：你之後可以換成爬蟲或 API 整合
        message = "🏀 賠率推播測試\n\n📅 開賽時間：今晚 8:00\n對戰隊伍：湖人 vs 勇士\n推薦下注：勇士 -3.5"
        line_bot_api.push_message(USER_ID, TextSendMessage(text=message))
    except Exception as e:
        print("推播失敗：", e)

def schedule_thread():
    schedule.every().hour.do(push_odds_data)
    while True:
        schedule.run_pending()
        time.sleep(1)

# 啟動排程線程
threading.Thread(target=schedule_thread, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
