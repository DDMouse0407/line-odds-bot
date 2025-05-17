import os
import json
import requests
from flask import Flask, request, abort
from dotenv import load_dotenv

from linebot.v3.messaging import MessagingApiClient, ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError

# 載入環境變數
load_dotenv()

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

app = Flask(__name__)

# 初始化 LINE Bot v3 客戶端
line_bot_api = MessagingApiClient(channel_access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(channel_secret=CHANNEL_SECRET)

@app.route("/")
def home():
    return "LINE Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@app.route("/test", methods=["GET"])
def test_push():
    user_id = os.getenv("USER_ID")  # 測試推播目標
    message = "✅ 測試成功：LINE Bot 正常推播。"
    line_bot_api.reply_message(
        ReplyMessageRequest(
            to=user_id,
            messages=[TextMessage(text=message)]
        )
    )
    return "測試訊息已送出"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()

    if text == "/test":
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="這是 /test 指令回覆。✅ Bot 正常運作！")]
            )
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
