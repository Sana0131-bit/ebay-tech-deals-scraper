from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
from datetime import datetime

url = "https://www.ebay.com/globaldeals/tech"

def scrape_ebay():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--log-level=3")  
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    products = driver.find_elements(By.CSS_SELECTOR, ".dne-itemtile")
    data = []
    timestamp = datetime.now().isoformat()

    for product in products:
        try:
            title = product.find_element(By.CSS_SELECTOR, ".dne-itemtile-title").text
            price = product.find_element(By.CSS_SELECTOR, ".dne-itemtile-price .first").text
            try:
                original_price = product.find_element(By.CSS_SELECTOR, ".itemtile-price-strikethrough").text
            except:
                original_price = "N/A"
            try:
                shipping = product.find_element(By.CSS_SELECTOR, ".dne-itemtile-shipping").text
            except:
                shipping = "N/A"
            item_url = product.find_element(By.CSS_SELECTOR, "a").get_attribute("href")

            data.append([timestamp, title, price, original_price, shipping, item_url])
        except Exception:
            continue
#Get Data
    with open("ebay_tech_deals.csv", "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for row in data:
            writer.writerow(row)

    print(f"Scraped {len(data)} items.")
    driver.quit()

if __name__ == "__main__":
    scrape_ebay()


# clean_data.py
import pandas as pd

df = pd.read_csv("ebay_tech_deals.csv", header=None, names=[
    "timestamp", "title", "price", "original_price", "shipping", "item_url"], dtype=str)

df["price"] = df["price"].str.replace("US $", "", regex=False).str.replace(",", "", regex=False).str.strip()
df["original_price"] = df["original_price"].str.replace("US $", "", regex=False).str.replace(",", "", regex=False).str.strip()
df["original_price"] = df.apply(lambda x: x["price"] if pd.isna(x["original_price"]) or x["original_price"] in ["", "N/A"] else x["original_price"], axis=1)
df["shipping"] = df["shipping"].apply(lambda x: "Shipping info unavailable" if pd.isna(x) or x.strip() in ["", "N/A"] else x.strip())
df["price"] = pd.to_numeric(df["price"], errors='coerce')
df["original_price"] = pd.to_numeric(df["original_price"], errors='coerce')
df["discount_percentage"] = round((1 - df["price"] / df["original_price"]) * 100, 2).fillna(0)
df.to_csv("cleaned_ebay_deals.csv", index=False)


# EDA.ipynb (Python code cells only)
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style="whitegrid")

df = pd.read_csv("cleaned_ebay_deals.csv")
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp")

# Time Series Analysis
df["hour"] = df["timestamp"].dt.hour
deals_per_hour = df.groupby("hour").size()
deals_per_hour.plot(kind='bar', title='Number of Deals per Hour', figsize=(10, 6))
plt.xlabel("Hour")
plt.ylabel("Count")
plt.tight_layout()
plt.show()

# Price and Discount Analysis
sns.histplot(df["price"], bins=30).set_title("Price Distribution")
plt.tight_layout()
plt.show()
sns.boxplot(x=df["price"]).set_title("Boxplot of Prices")
plt.tight_layout()
plt.show()
sns.scatterplot(x=df["original_price"], y=df["price"]).set_title("Original vs Discounted Price")
plt.tight_layout()
plt.show()
sns.histplot(df["discount_percentage"], bins=30).set_title("Discount Percentage Distribution")
plt.tight_layout()
plt.show()

# Shipping Analysis
shipping_counts = df["shipping"].value_counts()
shipping_counts.plot(kind='bar', title='Shipping Options Frequency', figsize=(10, 6))
plt.ylabel("Count")
plt.tight_layout()
plt.show()

# Text Analysis
keywords = ["Apple", "Samsung", "Laptop", "iPhone", "Tablet", "Gimbal"]
keyword_counts = {k: df["title"].str.contains(k, case=False).sum() for k in keywords}
plt.bar(keyword_counts.keys(), keyword_counts.values())
plt.title("Keyword Frequency in Titles")
plt.tight_layout()
plt.show()

# Price Difference Analysis
df["price_difference"] = df["original_price"] - df["price"]
sns.histplot(df["price_difference"], bins=30).set_title("Price Differences")
plt.tight_layout()
plt.show()

# Top Discounts
top_discounts = df.sort_values("discount_percentage", ascending=False).head(5)
print(top_discounts[["title", "price", "original_price", "discount_percentage"]])

