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
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return data.get("items", data.get("accounts", data.get("data", [])))
    return []

def run_reconciliation():
    scraped_locations = scrape_locations()
    crm_accounts = fetch_crm_accounts()
    
    proposals = {}
    matched_crm_ids = set()
    
    # 1. Process Scraped Web Locations against CRM
    for loc in scraped_locations:
        name = loc["facility_name"]
        best_match = None
        best_score = 0
        
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
                
        if best_match:
            matched_crm_ids.add(best_match.get("id"))

        # Category A: Confident Match (>85%)
        if best_score >= 85 and best_match:
            proposals[name] = {
                "status": "PENDING",
                "action": "NO_CHANGE" if best_match.get("name") == name else "UPDATE",
                "crm_account_id": best_match.get("id"),
                "payload": {"name": name, "status": "Active"},
                "reason": f"Confident match with '{best_match.get('name')}' (Score: {best_score}%)."
            }
        # Category B: Match Needs Fix / CHOW SOP (50% - 84%)
        elif best_score >= 50 and best_match:
            rev = best_match.get("lifetime_revenue", 0) or 0
            ar = best_match.get("outstanding_ar", 0) or 0
            
            if rev > 0 and ar > 0:
                proposals[name] = {
                    "status": "PENDING",
                    "action": "CHOW_SPLIT",
                    "old_account_id": best_match.get("id"),
                    "payload": {"name": name, "status": "Active"},
                    "reason": f"CHOW Triggered: Matched '{best_match.get('name')}' with AR=${ar} & Rev=${rev}. Preserving old account."
                }
            else:
                proposals[name] = {
                    "status": "PENDING",
                    "action": "UPDATE",
                    "crm_account_id": best_match.get("id"),
                    "payload": {"name": name, "status": "Active"},
                    "reason": f"Match needing update (Score: {best_score}%)."
                }
        # Category C: New Location (No CRM Account Yet)
        else:
            proposals[name] = {
                "status": "PENDING",
                "action": "CREATE",
                "payload": {"name": name, "status": "Active", "parent_id": None},
                "reason": f"New location found on website. No confident CRM match (Best Score: {best_score}%)."
            }

    # 2. Category D: Flag Bellhaven CRM Accounts Missing from Website / Duplicate Check
    for acc in crm_accounts:
        if not isinstance(acc, dict):
            continue
        acc_id = acc.get("id")
        acc_name = acc.get("name", "")
        
        if "bellhaven" in acc_name.lower() and acc_id not in matched_crm_ids:
            proposals[f"CRM_UNMATCHED_{acc_id}"] = {
                "status": "PENDING",
                "action": "MARK_INACTIVE_OR_DUPLICATE",
                "crm_account_id": acc_id,
                "payload": {"status": "Needs Review", "notes": "Account exists in CRM under Bellhaven but no longer appears on website."},
                "reason": f"Account '{acc_name}' exists in CRM under Bellhaven but no longer appears on the live website."
            }

    with open("pipeline_db.json", "w") as f:
        json.dump(proposals, f, indent=2)
        
    print("Reconciliation complete. All matching categories covered.")

if __name__ == "__main__":
    run_reconciliation()
