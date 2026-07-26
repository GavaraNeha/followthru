import json
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

DATA_FILE = "data/items.json"
LOG_FILE = "data/agent_log.json"

def load_items():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_items(items):
    with open(DATA_FILE, "w") as f:
        json.dump(items, f, indent=2)

def load_log():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        return json.load(f)

def add_log(message, log_type="info"):
    log = load_log()
    log.append({
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "type": log_type
    })
    log = log[-50:]
    os.makedirs("data", exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

def check_overdue_items():
    items = load_items()
    now = datetime.now()
    changed = False
    for item in items:
        if item.get("status") == "pending" and item.get("deadline_date"):
            try:
                deadline = datetime.fromisoformat(item["deadline_date"])
            except ValueError:
                continue
            if deadline < now:
                last_reminded = item.get("last_reminded")
                should_remind = True
                if last_reminded:
                    last_dt = datetime.fromisoformat(last_reminded)
                    if (now - last_dt).total_seconds() < 3600:
                        should_remind = False
                if should_remind:
                    item["last_reminded"] = now.isoformat()
                    item["reminder_count"] = item.get("reminder_count", 0) + 1
                    add_log(f"Reminder sent to {item['owner']} — \"{item['task']}\" is overdue.", "reminder")
                    changed = True
    if changed:
        save_items(items)

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_overdue_items, 'interval', seconds=30)
    scheduler.start()
    add_log("Agent started monitoring action items.", "system")
    return scheduler