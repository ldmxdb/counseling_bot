from flask import Flask, request, jsonify, render_template
from flask_caching import Cache
import openai

app = Flask(__name__)  # Flask 애플리케이션 생성

# 간단한 캐싱 설정 (메모리 캐시 사용)
cache = Cache(app, config={"CACHE_TYPE": "simple"})

# HTML 페이지 렌더링 (메인 페이지)
@app.route("/")
def home():
    return render_template("index.html")  # templates/index.html 파일을 사용

# 챗봇 API 엔드포인트
@app.route("/chat", methods=["POST"])
@cache.cached(timeout=60, query_string=True)  # 동일한 요청은 60초 동안 캐싱
def chat():
    """챗봇 대화 API"""

    data = request.json
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "메시지를 입력하세요."}), 400

    # OpenAI API 호출
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "넌 유머러스하고 현실적인 조언을 주는 친절한 상담사야."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150  # 응답 길이 제한
        )
        chatbot_response = response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return jsonify({"error": f"OpenAI API 오류: {str(e)}"}), 500

    return jsonify({"response": chatbot_response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # Render 배포용 설정
