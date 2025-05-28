from flask import Flask, render_template, request, jsonify
import json
import requests
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("TOGETHER_API_KEY")

app = Flask(__name__)

# Load buyer data
with open("buyers.json") as f:
    buyers = json.load(f)

API_URL = "https://api.together.xyz/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
MODEL = "mistralai/Mistral-7B-Instruct-v0.1"

def find_buyer(name=None, phone=None):
    for buyer in buyers:
        if (name and buyer["name"].lower() == name.lower()) or (phone and buyer["phone"] == phone):
            return buyer
    return None

def build_system_prompt(buyer):
    prefs = buyer["preferences"]
    return f"""
You are a friendly real estate assistant. The buyer's name is {buyer['name']}. Their preferences are:
- Locations: {prefs['locations']}
- Property Type: {prefs['property_type']}
- Budget: {prefs['budget']}
- Purpose: {prefs['purpose']}
- Additional comments: {prefs['comments']}

Based on this, ask personalized, helpful, and engaging questions. Only one question at a time. Use natural, human-like tone.
"""

def chat_with_llm(messages):
    body = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 300
    }
    response = requests.post(API_URL, headers=HEADERS, json=body)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

@app.route("/")
def index():
    buyer_options = [{"name": b["name"], "phone": b["phone"]} for b in buyers]
    return render_template("index.html", buyer_options=buyer_options)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data["message"]
    buyer_info = data["buyer_id"]  # dict with name & phone

    if "messages" not in data:
        buyer = find_buyer(name=buyer_info.get("name"), phone=buyer_info.get("phone"))
        if not buyer:
            return jsonify({"error": "Buyer not found."})
        system_prompt = build_system_prompt(buyer)
        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Please begin asking questions."}]
    else:
        messages = data["messages"]

    messages.append({"role": "user", "content": user_input})
    reply = chat_with_llm(messages)
    messages.append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply, "messages": messages})

# if __name__ == "__main__":
#     app.run(debug=True)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
