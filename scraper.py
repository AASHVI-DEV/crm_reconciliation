import requests
from bs4 import BeautifulSoup

def scrape_locations():
    url = "https://analyst-assessment-production.up.railway.app"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    
    locations = []
    cards = soup.find_all("div", class_="location-card") or soup.find_all("article") or soup.find_all("div")
    
    for card in cards:
        text = card.get_text(strip=True)
        if "Bellhaven" in text and len(text) < 300:
            locations.append({
                "facility_name": text.split("-")[0].strip() if "-" in text else text[:30],
                "raw_details": text
            })
    return locations

if __name__ == "__main__":
    locs = scrape_locations()
    print(f"Scraped {len(locs)} locations.")
