from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat")
def chat_page():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.json.get("message")  # Use JSON for request body
        if not user_message:
            return jsonify({"response": "No message received"}), 400

        # Send the message to Rasa server
        rasa_response = requests.post(
            "http://localhost:5005/webhooks/rest/webhook",  # Rasa server URL
            json={"sender": "user", "message": user_message}
        )

        if rasa_response.status_code == 200:
            bot_message = rasa_response.json()[0].get("text", "Sorry, I couldn't understand.")
            return jsonify({"response": bot_message})
        else:
            return jsonify({"response": "Sorry, something went wrong with Rasa."}), 500
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
