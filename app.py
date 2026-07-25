from flask import Flask, render_template, request, jsonify
from extractor import extract_action_items
import json
import os
from datetime import datetime

app = Flask(__name__)
DATA_FILE = "data/items.json"

def load_items():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_items(items):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(items, f, indent=2)

@app.route("/")
def index():
    items = load_items()
    return render_template("index.html", items=items)

@app.route("/extract", methods=["POST"])
def extract():
    transcript = request.json.get("transcript", "")
    if not transcript.strip():
        return jsonify({"error": "Empty transcript"}), 400

    new_items = extract_action_items(transcript)
    items = load_items()
    next_id = max([item["id"] for item in items], default=0) + 1
    for item in new_items:
        item["id"] = next_id
        item["status"] = "pending"
        item["created_at"] = datetime.now().isoformat()
        next_id += 1
    items.extend(new_items)
    save_items(items)
    return jsonify({"items": items})

@app.route("/complete/<int:item_id>", methods=["POST"])
def complete_item(item_id):
    items = load_items()
    for item in items:
        if item["id"] == item_id:
            item["status"] = "done"
    save_items(items)
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)