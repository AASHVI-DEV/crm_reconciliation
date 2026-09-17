import requests
import json
import os
from rapidfuzz import fuzz
from config import API_URL, HEADERS
from scraper import scrape_locations

DB_FILE = "pipeline_db.json"

def get_crm_accounts():
    res = requests.get(f"{API_URL}/accounts?limit=200", headers=HEADERS)
    res.raise_for_status()
    return res.json().get("accounts", [])

def run_reconciliation():
    crm_accounts = get_crm_accounts()
    web_locations = scrape_locations()
    
    parent_id = None
    for acc in crm_accounts:
        if "bellhaven" in acc.get("name", "").lower() and acc.get("is_parent"):
            parent_id = acc["id"]
            break

    proposals = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            proposals = json.load(f)

    for loc in web_locations:
        name = loc["facility_name"]
        
        if name in proposals and proposals[name]["status"] in ["APPROVED", "REJECTED"]:
            continue

        best_match = None
        best_score = 0
        for acc in crm_accounts:
            score = fuzz.ratio(name.lower(), acc.get("name", "").lower())
            if score > best_score:
                best_score = score
                best_match = acc

        if best_score < 60:
            proposals[name] = {
                "status": "PENDING",
                "action": "CREATE",
                "payload": {"name": name, "parent_id": parent_id, "status": "Active"},
                "reason": f"No confident match (Score: {best_score}%)."
            }
        else:
            acc_id = best_match["id"]
            if best_match.get("parent_id") != parent_id:
                rev = best_match.get("lifetime_revenue", 0)
                ar = best_match.get("outstanding_ar", 0)

                if rev > 0 and ar > 0:
                    proposals[name] = {
                        "status": "PENDING",
                        "action": "CHOW_SPLIT",
                        "target_account_id": acc_id,
                        "new_account_payload": {"name": name, "parent_id": parent_id, "status": "Active"},
                        "reason": f"Has revenue (${rev}) and AR (${ar}). Preserve old record; created new account under parent."
                    }
                else:
                    proposals[name] = {
                        "status": "PENDING",
                        "action": "UPDATE_PARENT",
                        "target_account_id": acc_id,
                        "payload": {"parent_id": parent_id},
                        "reason": f"No AR barrier (AR: ${ar}). Direct parent update."
                    }

    with open(DB_FILE, "w") as f:
        json.dump(proposals, f, indent=2)
    
    print(f"Reconciliation engine completed. Proposals stored in {DB_FILE}.")

if __name__ == "__main__":
    run_reconciliation()
