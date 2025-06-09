import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re

def get_exchange_rate(base: str, target: str) -> float:
    url = f"https://api.frankfurter.app/latest?from={base}&to={target}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if target in data['rates']:
            return data['rates'][target]
        else:
            print(f"[Error] Currency '{target}' not supported or invalid.")
    except requests.exceptions.RequestException as e:
        print(f"[Error] Failed to fetch exchange rate: {e}")
    except Exception as e:
        print(f"[Unexpected Error] {e}")
    return None

def parse_price(price_str):
    try:
        match = re.search(r"(\d+\.\d+)", price_str)
        if match:
            return float(match.group(1))
        else:
            print(f"Couldn't extract numeric price from '{price_str}'")
            return 0.0
    except Exception as e:
        print(f"[Error] parse_price failed for '{price_str}': {e}")
        return 0.0

def scrape_books():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get("https://books.toscrape.com/", headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[Error] Connection failed: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    books = soup.select("article.product_pod")[:10]  # First 10 books

    results = []
    for book in books:
        title = book.h3.a["title"].strip()
        price_text = book.select_one(".price_color").text.strip()
        price = parse_price(price_text)
        results.append({
            "name": title,
            "price_original": price
        })

    return results

def main():
    print("📘 Scraping book prices from https://books.toscrape.com/\n")

    ogcurrency = "GBP"  # Source currency is GBP on the site
    newcurrency = input("Enter target currency (e.g., USD, EUR, ): ").strip().upper()

    if len(ogcurrency) != 3 or not newcurrency.isalpha():
        print("❌ Currency code must be a 3-letter alphabetic code (e.g., USD, EUR)")
        return

    rate = get_exchange_rate(ogcurrency, newcurrency)
    if not rate:
        return

    print(f"\n💱 Exchange Rate: 1 {ogcurrency} = {rate:.4f} {newcurrency}\n")

    books = scrape_books()
    if not books:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = []

    for book in books:
        book.update({
            "converted_price": round(book["price_original"] * rate, 2),
            "from_currency": ogcurrency,
            "to_currency": newcurrency,
            "conversion_time": timestamp
        })
        results.append(book)

    df = pd.DataFrame(results)
    print("📊 Converted Prices:\n")
    print(df[["name", "price_original", "converted_price", "to_currency", "conversion_time"]])

    # Add timestamp to filename to avoid overwriting
    file_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = "Bscapper.csv"
    df.to_csv(filename, index=False)
    print(f"\n✅ Data saved to '{filename}'")

if __name__ == "__main__":
    main()
