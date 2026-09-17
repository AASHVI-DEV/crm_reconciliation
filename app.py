import streamlit as st
import json
import requests
from config import API_URL, HEADERS

DB_FILE = "pipeline_db.json"

def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def execute_action(item):
    action = item["action"]
    if action == "CREATE":
        requests.post(f"{API_URL}/accounts", headers=HEADERS, json=item["payload"]).raise_for_status()
    elif action == "UPDATE_PARENT":
        acc_id = item["target_account_id"]
        requests.patch(f"{API_URL}/accounts/{acc_id}", headers=HEADERS, json=item["payload"]).raise_for_status()
    elif action == "CHOW_SPLIT":
        res = requests.post(f"{API_URL}/accounts", headers=HEADERS, json=item["new_account_payload"])
        res.raise_for_status()
        new_id = res.json()["id"]
        old_id = item["target_account_id"]
        requests.patch(f"{API_URL}/accounts/{old_id}", headers=HEADERS, json={"chow_current_account": new_id}).raise_for_status()

st.title("CRM Reconciliation Review UI")
data = load_db()
pending = {k: v for k, v in data.items() if v.get("status") == "PENDING"}

st.write(f"### Pending Review Items ({len(pending)})")

for name, item in list(pending.items()):
    with st.expander(f"{item['action']}: {name}"):
        st.write("**Reason:**", item["reason"])
        col1, col2 = st.columns(2)
        if col1.button("Approve", key=f"app_{name}"):
            execute_action(item)
            data[name]["status"] = "APPROVED"
            save_db(data)
            st.success("Changes successfully applied to CRM!")
            st.rerun()
        if col2.button("Reject", key=f"rej_{name}"):
            data[name]["status"] = "REJECTED"
            save_db(data)
            st.info("Proposal rejected.")
            st.rerun()
