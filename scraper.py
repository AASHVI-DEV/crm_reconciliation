import requests
from bs4 import BeautifulSoup

def scrape_locations():
    url = "https://analyst-assessment-production.up.railway.app"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    
    locations = []
    
    # Extract candidate text elements across containers, headings, and links
    elements = soup.find_all(["h1", "h2", "h3", "h4", "div", "a", "span", "p"])

    # Non-facility phrases to exclude explicitly
    banned_keywords = [
        "find a community", "our promise", "care that feels", 
        "new this year", "welcome", "about us", "contact", 
        "home", "services", "privacy policy", "terms"
    ]

    for el in elements:
        text = el.get_text(strip=True)
        text_lower = text.lower()
        
        # Check if text contains a facility identifier (e.g., "Senior Living", "Living", "Center", "Bellhaven")
        is_facility = any(kw in text_lower for kw in ["senior living", "bellhaven", "care center", "assisted living"])
        
        # Check against banned phrase list
        is_banned = any(banned in text_lower for banned in banned_keywords)
        
        if is_facility and not is_banned and len(text) < 60:
            clean_name = text.split("-")[0].split(":")[0].strip()
            locations.append({
                "facility_name": clean_name,
                "raw_details": text
            })

    # Deduplicate facility names
    seen = set()
    unique_locations = []
    for loc in locations:
        if loc["facility_name"] not in seen:
            seen.add(loc["facility_name"])
            unique_locations.append(loc)

    return unique_locations

if __name__ == "__main__":
    locs = scrape_locations()
    print(f"Scraped {len(locs)} unique location(s):")
    for loc in locs:
        print(f" - {loc['facility_name']}")
