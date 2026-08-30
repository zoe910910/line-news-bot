# app.py

import os
import json
from flask import Flask, request, abort
import requests
import urllib.parse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# --- 1. 凭证设定 (请替换成您自己的凭证) ---
# 请使用您的真实凭证。由于 Render 部署的稳定性已确认，此处的凭证是正确的。
YOUR_CHANNEL_ACCESS_TOKEN = "41Ttrh6kR+4bOSbjIzQCbz0OAmjMnkp+5L0yeFbusiWHqee79jwaW+n5IT3hkrB+yXUday/pcc6N9xqSUnTHiBxit9TD6GkF6aFnNjvsciIxwmtTlV74gGbAqMFeqUZTGM4KsLhAEIdoszUa6gpCNAdB04t89/1O/w1cDnyilFU="
YOUR_CHANNEL_SECRET = "4c6e1abd743d80750ae6d52ca6a98e6a"
# ---------------------------------------------

# Gemini API 配置
# Note: 在 Render 环境中，您不需要实际填写 API Key，Canvas 会在运行时注入。
API_KEY = "" 
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={API_KEY}"

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
    """处理来自 LINE 的 Webhook 请求"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/secret.")
        abort(400)
    
    return 'OK'

# --- 3. 事件处理器：处理用户发送的文本消息 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """处理用户发送的文字消息"""
    user_brand = event.message.text.strip()
    
    # 调用生成摘要的函数
    reply_text = generate_news_summary(user_brand)
    
    # 发送回复
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# --- 4. 核心逻辑：使用 Google Search 和 Gemini API 生成摘要 ---
def generate_news_summary(brand_name):
    """
    1. 使用 Google Search 工具获取当周新闻。
    2. 将搜索结果传递给 Gemini 模型生成摘要和格式化链接。
    """
    
    # 构造查询，限定在过去一周 (當週新聞)
    # Note: 搜索工具会自动包含英文查询
    user_query = f"請搜尋過去一周內，品牌 '{brand_name}' 的相關新聞。請提供 5 個最相關的中文新聞連結及摘要。"

    # --- 1. 构造 Gemini API 请求 Payload ---
    system_prompt = (
        f"你是一个专业的品牌新闻分析师。你的任务是根据用户提供的品牌名称，调用 Google Search 工具，"
        f"然后根据搜索结果（限定为当周新闻），提供一份简洁的摘要和完整的可点击链接清单。"
        f"请使用繁体中文回复，且回复内容必须包含：\n"
        f"1. 标题：'{brand_name} 當週新聞摘要'\n"
        f"2. 簡潔摘要：针对本周新闻的重点整理（2-3句话）。\n"
        f"3. 新闻链接：将所有找到的新闻标题和 URL 整理成 LINE 可点击的 Markdown 链接格式。确保每个链接都是可点击的。"
        f"範例格式: [新聞标题](URL)"
    )

    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "tools": [{"google_search": {}}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
    }
    
    # --- 2. 发送请求到 Gemini API ---
    try:
        response = requests.post(
            GEMINI_API_URL, 
            headers={"Content-Type": "application/json"}, 
            json=payload,
            # 设置一个较长的超时时间，因为包含搜索和 LLM 生成
            timeout=30 
        )
        response.raise_for_status() # 如果状态码不是 200, 则抛出异常
        
        result = response.json()
        
        # 提取模型生成的文本
        candidate = result.get('candidates', [{}])[0]
        generated_text = candidate.get('content', {}).get('parts', [{}])[0].get('text', "")

        if generated_text:
            return generated_text
        else:
            return f"❌ 抱歉，模型未能为 '{brand_name}' 生成摘要，请稍后重试。"
    
    except requests.exceptions.Timeout:
        return "❌ 抱歉，生成新聞摘要超時了，請再試一次。"
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Gemini API Request Failed: {e}")
        return f"❌ 抱歉，Gemini API 调用失败，错误信息: {e}"
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}")
        return f"❌ 发生未知错误：{e}"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)

### 📦 文件依赖更新：`requirements.txt`

#由于我们使用了 `requests` 库来调用 Gemini API，您的 `requirements.txt` 已经是正确的了：


# requirements.txt

