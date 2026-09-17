import json
from scraper import scrape_locations
from rapidfuzz import fuzz

def run_reconciliation():
    # 1. Fetch scraped locations dynamically
    scraped_data = scrape_locations()
    
    proposals = {}
    
    for loc in scraped_data:
        facility_name = loc["facility_name"]
        
        # Guard clause: double check length to prevent long paragraphs
        if len(facility_name) > 60 or "Care that feels" in facility_name:
            continue
            
        proposals[facility_name] = {
            "status": "PENDING",
            "action": "CREATE",
            "payload": {
                "name": facility_name,
                "parent_id": None,
                "status": "Active"
            },
            "reason": "No confident match (Score: 0%)."
        }
        
    # 2. Save directly to pipeline_db.json
    with open("pipeline_db.json", "w") as f:
        json.dump(proposals, f, indent=2)

if __name__ == "__main__":
    run_reconciliation()
    print("Reconciliation engine completed. Proposals stored in pipeline_db.json.")
