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