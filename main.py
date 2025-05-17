import os
from flask import Flask, request, abort
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import TextMessage, PushMessageRequest, ReplyMessageRequest

from scraper import fetch_all_odds_report
from predict import analyze_and_predict

# 載入環境變數
load_dotenv()
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
USER_ID = os.getenv("USER_ID")

app = Flask(__name__)
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/")
def home():
    return "✅ LINE Odds Bot 正常運作中"

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Webhook error:", e)
        abort(400)
    return "OK"

@app.route("/test", methods=["GET"])
def test_push():
    text = fetch_all_odds_report()
    line_bot_api.push_message(PushMessageRequest(to=USER_ID, messages=[TextMessage(text=text)]))
    return "✅ 測試推播完成"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()
    if text.startswith("/查詢"):
        keyword = text.replace("/查詢", "").strip()
        reply_text = fetch_all_odds_report(keyword)
    else:
        reply_text = "✅ 支援指令：\n/test（推播測試）\n/查詢 [隊伍或聯賽名稱]"
    line_bot_api.reply_message(
        ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=reply_text)])
    )

# 每小時自動推播
scheduler = BackgroundScheduler()
@scheduler.scheduled_job('cron', minute='0')
def auto_push():
    try:
        text = fetch_all_odds_report()
        line_bot_api.push_message(PushMessageRequest(to=USER_ID, messages=[TextMessage(text=text)]))
        print("✅ 自動推播完成")
    except Exception as e:
        print("❌ 自動推播錯誤:", e)

scheduler.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
