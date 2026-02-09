import os
import smtplib
import yfinance as yf
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ===== ENVIRONMENT VARIABLES (FROM GITHUB SECRETS) =====
EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ===== CONFIG =====
STOCKS = {
    "MARA": "Marathon Digital Holdings",
    "RIOT": "Riot Platforms",
    "COIN": "Coinbase"
}

BTC_TICKER = "BTC-USD"

genai.configure(api_key=GEMINI_API_KEY)

def get_price(ticker):
    hist = yf.Ticker(ticker).history(period="7d")
    if len(hist) >= 2:
        curr = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2]
        change = ((curr - prev) / prev) * 100
        return f"${curr:.2f} ({change:+.2f}%)"
    return "Unavailable"

def get_news(company):
    url = f"https://news.google.com/rss/search?q={company}+stock&hl=en-US&gl=US&ceid=US:en"
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.content, "xml")
    items = soup.find_all("item")[:5]
    return "\n".join([f"- {i.title.text}" for i in items])

def run():
    btc_price = get_price(BTC_TICKER)
    stock_data = ""
    news_data = ""

    for ticker, name in STOCKS.items():
        price = get_price(ticker)
        stock_data += f"{name} ({ticker}): {price}\n"
        news_data += f"\n{name} News:\n{get_news(name)}\n"

    prompt = f"""
You are a professional market analyst.

BITCOIN PRICE:
{btc_price}

STOCK PRICES:
{stock_data}

NEWS:
{news_data}

TASK:
1. Summarize key news factually.
2. Analyze sentiment (Bullish / Bearish / Neutral).
3. Explain how Bitcoin price may impact these stocks.
4. Predict short-term impact (no price targets).
5. Write clearly for an investor email.
"""

    model = genai.GenerativeModel("gemini-1.5-flash")
    analysis = model.generate_content(prompt).text

    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = "Daily Crypto Stock & Bitcoin Analysis"
    msg.attach(MIMEText(analysis, "plain"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL, PASSWORD)
    server.send_message(msg)
    server.quit()

if __name__ == "__main__":
    run()
