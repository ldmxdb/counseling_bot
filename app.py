from flask import Flask, render_template, request, jsonify
import openai
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")  # 이제 HTML을 반환!

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "메시지를 입력하세요."}), 400

    # OpenAI API 호출
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "친절하고 유머러스한 상담 챗봇입니다."},
                      {"role": "user", "content": user_message}],
            max_tokens=150
        )
        chatbot_response = response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return jsonify({"error": f"OpenAI API 오류: {str(e)}"}), 500

    return jsonify({"response": chatbot_response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
