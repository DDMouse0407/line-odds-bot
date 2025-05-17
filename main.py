from flask import Flask, request, abort
from linebot.v3.webhooks import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import TextMessage
from linebot.v3.webhooks.models import MessageEvent, TextMessageContent

import os

# 讀取環境變數（建議在 Replit 或 Railway 的環境變數設定中輸入）
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

# 初始化 LINE Messaging API
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
handler = WebhookHandler(CHANNEL_SECRET)

# 初始化 Flask 應用
app = Flask(__name__)

# Webhook 接收處理
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("LINE Webhook 錯誤:", str(e))
        abort(400)

    return 'OK'

# 處理文字訊息事件
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    reply_text = f"你說的是：{user_message}"
    line_bot_api.reply_message(
        event.reply_token,
        messages=[TextMessage(text=reply_text)]
    )

# 測試用網址路徑（可在瀏覽器上直接觸發）
@app.route("/test", methods=["GET"])
def test_push():
    # 替換為你的 LINE 使用者 ID（或抓取 event.source.user_id）
    user_id = "YOUR_USER_ID"
    try:
        line_bot_api.push_message(
            to=user_id,
            messages=[TextMessage(text="這是 /test 測試推播訊息")]
        )
        return "已推播測試訊息"
    except Exception as e:
        return f"推播失敗: {e}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)
