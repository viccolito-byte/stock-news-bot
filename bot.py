import os
import smtplib
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

# ================== SECRETS FROM GITHUB ==================
EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ================== CONFIG ==================
STOCKS = {
    "MARA": "Marathon Digital Holdings",
    "RIOT": "Riot Platforms",
    "COIN": "Coinbase"
}

BTC_TICKER = "BTC-USD"

# ================== GEMINI CLIENT ==================
client = genai.Client(api_key=GEMINI_API_KEY)

# ================== FUNCTIONS ==================
def get_price(ticker):
    try:
        hist = yf.Ticker(ticker).history(period="7d")
        if len(hist) >= 2:
            curr = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2]
            change = ((curr - prev) / prev) * 100
            return f"${curr:.2f} ({change:+.2f}%)"
    except:
        pass
    return "Unavailable"

def get_news(company):
    try:
        url = f"https://news.google.com/rss/search?q={company}+stock&hl=en-US&gl=US&ceid=US:en"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.content, "xml")
        items = soup.find_all("item")[:5]
        return "\n".join([f"- {i.title.text}" for i in items])
    except:
        return "- No news found"

# ================== MAIN ==================
def run():
    btc_price = get_price(BTC_TICKER)

    stock_block = ""
    news_block = ""

    for ticker, name in STOCKS.items():
        price = get_price(ticker)
        stock_block += f"{name} ({ticker}): {price}\n"
        news_block += f"\n{name} News:\n{get_news(name)}\n"

    prompt = f"""
You are a professional market analyst writing a daily investor email.

BITCOIN PRICE:
{btc_price}

STOCK PRICES:
{stock_block}

NEWS:
{news_block}

TASK:
1. Summarize the key factual news.
2. Label sentiment for each stock (Bullish / Bearish / Neutral).
3. Explain how Bitcoin price action may affect these stocks.
4. Predict short-term impact (no price targets, no financial advice).
5. Write clearly and professionally.
"""

    response = client.models.generate_content(
        model="gemini-1.5-pro-latest",
        contents=prompt
    )

    analysis = response.text or "AI analysis unavailable today."

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

# ================== RUN ==================
if __name__ == "__main__":
    run()

