import os
import openai
import sqlite3
from flask import Flask, request, jsonify
from flask_caching import Cache
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Flask 앱 생성 (한 번만)
app = Flask(__name__)

# 캐싱 설정 (응답 속도 향상)
app.config["CACHE_TYPE"] = "simple"
cache = Cache(app)

# SQLite 데이터베이스 설정 (사용 제한 기능)
DB_PATH = "user_data.db"

def init_db():
    """SQLite 데이터베이스 초기화 (처음 실행 시 1회 필요)"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                device_id TEXT PRIMARY KEY,
                request_count INTEGER DEFAULT 0,
                last_request_date TEXT
            )
        ''')
        conn.commit()

init_db()  # 서버 시작 시 DB 생성

def check_request_limit(device_id):
    """하루 최대 10회 요청 제한 확인"""
    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT request_count, last_request_date FROM users WHERE device_id = ?", (device_id,))
        row = cursor.fetchone()

        if row:
            request_count, last_request_date = row
            if last_request_date == today:
                if request_count >= 10:
                    return False  # 요청 초과
                cursor.execute("UPDATE users SET request_count = request_count + 1 WHERE device_id = ?", (device_id,))
            else:
                cursor.execute("UPDATE users SET request_count = 1, last_request_date = ? WHERE device_id = ?", (today, device_id))
        else:
            cursor.execute("INSERT INTO users (device_id, request_count, last_request_date) VALUES (?, 1, ?)", (device_id, today))
        
        conn.commit()
    
    return True  # 요청 가능

# ✅ "/" 경로 추가
@app.route("/")
def home():
    return "상담 챗봇이 정상적으로 실행 중입니다! /chat 엔드포인트를 사용하세요."

# ✅ "/chat" 엔드포인트 (챗봇)
@app.route("/chat", methods=["POST"])
@cache.cached(timeout=60, query_string=True)  # 캐싱 적용 (60초 유지)
def chat():
    """챗봇 대화 API"""
    data = request.json
    device_id = data.get("device_id", "unknown_device")  # 기기 ID (프론트에서 전달)
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "메시지를 입력하세요."}), 400

    if not check_request_limit(device_id):
        return jsonify({"error": "오늘의 상담 횟수를 초과하였습니다. 내일 다시 시도하세요!"}), 429

    # OpenAI API 호출
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "친절하고 유머러스한 상담 챗봇입니다."},
                      {"role": "user", "content": user_message}],
            max_tokens=150  # 응답 길이 제한
        )
        chatbot_response = response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return jsonify({"error": f"OpenAI API 오류: {str(e)}"}), 500

    return jsonify({"response": chatbot_response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
