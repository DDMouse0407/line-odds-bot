from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

# 從環境變數取得金鑰
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# webhook 接收訊息的路由
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 接收文字訊息並回覆
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"你說的是：{user_msg}")
    )

# 測試推播用的路由（可以瀏覽器訪問）
@app.route("/test", methods=["GET"])
def test_push():
    try:
        line_bot_api.push_message(
            to="YOUR_USER_ID",  # 換成你自己的 LINE 使用者 ID
            messages=TextSendMessage(text="這是測試推播訊息")
        )
        return "推播成功"
    except Exception as e:
        return f"推播失敗: {e}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
