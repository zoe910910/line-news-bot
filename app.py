# app.py

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 引入我們剛剛寫好的爬蟲函式
from crawler import get_brand_news 

app = Flask(__name__)

# ==== 請確保這裡的金鑰是您最新重新發行的 Token ====
# 1. Channel Access Token (long-lived)
# 這是您最新提供的有效 Token
line_bot_api = LineBotApi('K34uCEOUEhVUYr6THN9oV+04VH0Ytyg2l7e5XrsQHa8QPcHtkeoBzOWAzXbC8oRGQ/WI5KazdDSKhQQTBV4cBeA42WGjGkEMFf3tylBOpNhdyxuKRaB4QPz1BRZ7uglGvb4gDDR3NQxEs7vPHTBBagdB04t89/1O/w1cDnyilFU=') 

# 2. Channel Secret
handler = WebhookHandler('72c1dd7da164b7d96ae69d2cc0965f66')
# =======================================

@app.route("/callback", methods=['POST'])
def callback():
    # 接收 LINE 伺服器送來的訊息
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        # 處理訊息
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 取得使用者傳入的品牌名稱
    brand_name = event.message.text
    
    # 呼叫爬蟲函式取得新聞
    news_data = get_brand_news(brand_name)
    
    # 整理回覆訊息
    if news_data:
        # 使用 Markdown 格式化訊息
        reply_text = f"📰 收到關於「**{brand_name}**」的當週新聞 (最近 {len(news_data)} 則)：\n\n"
        for i, news in enumerate(news_data):
            # 格式化標題和連結
            reply_text += f"**{i+1}. {news['title']}**\n"
            reply_text += f"連結: {news['url']}\n"
            reply_text += "----------\n"
        
        reply_text += "（新聞資料來自 Google News 搜尋）"
    else:
        reply_text = f"很抱歉，找不到「{brand_name}」在當週的相關新聞，請嘗試其他關鍵字。"

    # 回覆訊息給 LINE 使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    # 在本地端運行 Flask 服務
    print("Flask 服務啟動中... 請勿關閉此視窗。")
    app.run(port=8000)