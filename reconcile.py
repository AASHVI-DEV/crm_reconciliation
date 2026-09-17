import requests
import json
from scraper import scrape_locations
from rapidfuzz import fuzz

API_BASE = "https://analyst-assessment-production.up.railway.app/api/v1"
HEADERS = {"Authorization": "Bearer bh_lCSyghnRNXlOjPrHHEM--A"}

def fetch_crm_accounts():
    response = requests.get(f"{API_BASE}/accounts", headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    
    # Handle both direct lists and wrapped dictionary responses
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return data.get("items", data.get("accounts", data.get("data", [])))
    return []

def run_reconciliation():
    scraped_locations = scrape_locations()
    crm_accounts = fetch_crm_accounts()
    
    proposals = {}
    
    for loc in scraped_locations:
        name = loc["facility_name"]
        best_match = None
        best_score = 0
        
        # Fuzzy match against existing CRM accounts
        for acc in crm_accounts:
            if not isinstance(acc, dict):
                continue
                
            acc_name = acc.get("name", "")
            if not acc_name:
                continue
                
            score = fuzz.ratio(name.lower(), acc_name.lower())
            if score > best_score:
                best_score = score
                best_match = acc
                
        # 1. Confident Match (>85%)
        if best_score >= 85 and best_match:
            proposals[name] = {
                "status": "PENDING",
                "action": "NO_CHANGE" if best_match.get("name") == name else "UPDATE",
                "crm_account_id": best_match.get("id"),
                "payload": {"name": name, "status": "Active"},
                "reason": f"Matched with '{best_match.get('name')}' (Score: {best_score}%)."
            }
        # 2. Potential Match requiring CHOW or Parent fix (50% - 84%)
        elif best_score >= 50 and best_match:
            rev = best_match.get("lifetime_revenue", 0) or 0
            ar = best_match.get("outstanding_ar", 0) or 0
            
            # CHOW SOP Rule: Preserve old account if revenue AND AR > 0
            if rev > 0 and ar > 0:
                proposals[name] = {
                    "status": "PENDING",
                    "action": "CHOW_SPLIT",
                    "old_account_id": best_match.get("id"),
                    "payload": {"name": name, "status": "Active"},
                    "reason": f"CHOW Triggered: Matched '{best_match.get('name')}' with AR=${ar} and Rev=${rev}. Preserving old account."
                }
            else:
                proposals[name] = {
                    "status": "PENDING",
                    "action": "UPDATE",
                    "crm_account_id": best_match.get("id"),
                    "payload": {"name": name, "status": "Active"},
                    "reason": f"Direct update allowed (Score: {best_score}%)."
                }
        # 3. New Facility (No Match)
        else:
            proposals[name] = {
                "status": "PENDING",
                "action": "CREATE",
                "payload": {"name": name, "status": "Active", "parent_id": None},
                "reason": f"No confident CRM match found (Best Score: {best_score}%)."
            }

    with open("pipeline_db.json", "w") as f:
        json.dump(proposals, f, indent=2)
        
    print("Reconciliation complete. Proposals updated in pipeline_db.json.")

if __name__ == "__main__":
    run_reconciliation()
