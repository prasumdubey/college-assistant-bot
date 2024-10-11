# flask_ui/app.py
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form["message"]
    rasa_response = requests.post(
        "http://localhost:5005/webhooks/rest/webhook",
        json={"sender": "user", "message": user_message}
    )
    bot_message = rasa_response.json()[0]["text"]
    return jsonify({"response": bot_message})

if __name__ == "__main__":
    app.run(debug=True)
