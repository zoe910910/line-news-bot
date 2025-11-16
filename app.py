# app.py

import os
from flask import Flask, request, abort
import requests
import urllib.parse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# --- 1. 凭证设定 (请替换成您自己的凭证) ---
YOUR_CHANNEL_ACCESS_TOKEN = "K34uCEOUEhVUYr6THN9oV+04VH0Ytyg2l7e5XrsQHa8QPcHtkeoBzOWAzXbC8oRGQ/WI5KazdDSKhQQTBV4cBeA42WGjGkEMFf3tylBOpNhdyxuKRaB4QPz1BRZ7uglGvb4gDDR3NQxEs7vPHTBBagdB04t89/1O/w1cDnyilFU=" # 请替换为您的 Access Token
YOUR_CHANNEL_SECRET = "72c1dd7da164b7d96ae69d2cc0965f66" # 请替换为您的 Channel Secret
# ---------------------------------------------

# Flask 应用程序初始化
app = Flask(__name__)

# LINE Bot API 初始化
line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

# 端口设定（Render 需要）
port = int(os.environ.get('PORT', 5000))

# --- 2. 路由：接收 LINE Webhook 的唯一入口 ---
@app.route("/callback", methods=['POST'])
def callback():
    # 获取请求头中的签名
    signature = request.headers['X-Line-Signature']

    # 获取请求体中的数据
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        # 处理 Webhook 事件
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/secret.")
        abort(400)
    
    # 成功处理后，返回 200 OK
    return 'OK'

# --- 3. 事件处理器：处理用户发送的文本消息 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_brand = event.message.text.strip()
    
    # 调用新闻摘要生成函数
    reply_text = generate_news_summary(user_brand)
    
    # 发送回复
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# --- 4. 核心逻辑：生成新闻摘要和链接 ---
def generate_news_summary(brand_name):
    # 使用 urllib.parse.quote 对品牌名称进行 URL 编码
    encoded_brand_name = urllib.parse.quote(brand_name)
    
    # qdr:w 参数表示搜索结果限定在“过去一周” (Past week)
    news_search_url = f"https://www.google.com/search?q={encoded_brand_name}+新闻&tbs=qdr:w&hl=zh-TW"
    
    # 撰写回复内容
    summary = f"🤖 **{brand_name} 当周新闻摘要** 整理如下：\n\n"
    summary += f"**1. 简单摘要：** 针对 {brand_name}，本周市场关注点可能在... (此为预设文字)\n\n"
    summary += f"**2. 当周新闻网址：**\n"
    summary += f"🔗 [点击查看 {brand_name} 最新当周新闻]({news_search_url})\n\n"
    summary += f"(资讯来源：Google 搜索，时间范围：过去一周)"

    return summary


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)