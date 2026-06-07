# tools.py
import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd

AV_KEY = st.secrets["ALPHA_VANTAGE_KEY"]
AV_BASE = "https://www.alphavantage.co/query"

def get_stock_fundamentals(ticker: str) -> str:
    try:
        clean_ticker = ticker.split('.')[0]
        params = {
            "function": "OVERVIEW",
            "symbol": clean_ticker,
            "apikey": AV_KEY
        }
        response = requests.get(AV_BASE, params=params, timeout=8)
        data = response.json()

        if not data or "Note" in data or "Information" in data:
            return _fallback_fundamentals(ticker)

        fundamentals = {
            "Company Name": data.get("Name"),
            "Sector": data.get("Sector"),
            "Industry": data.get("Industry"),
            "Market Cap": data.get("MarketCapitalization"),
            "PE Ratio": data.get("PERatio"),
            "Forward PE": data.get("ForwardPE"),
            "EPS": data.get("EPS"),
            "52 Week High": data.get("52WeekHigh"),
            "52 Week Low": data.get("52WeekLow"),
            "Profit Margin": data.get("ProfitMargin"),
            "Dividend Yield": data.get("DividendYield"),
            "Analyst Target Price": data.get("AnalystTargetPrice"),
        }
        return str(fundamentals)
    except Exception:
        return _fallback_fundamentals(ticker)


def _fallback_fundamentals(ticker: str) -> str:
    try:
        clean_ticker = ticker.split('.')[0]
        url = f"https://news.google.com/rss/search?q={clean_ticker}+financial+summary&hl=en-US&gl=US&ceid=US:en"
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.content, "lxml-xml")
        items = soup.find_all("item")[:3]
        snippets = [item.title.text for item in items]
        return f"Ticker: {ticker}. Market Context (fallback): {'; '.join(snippets)}"
    except Exception:
        return f"Fundamentals temporarily unavailable for {ticker}."


def get_price_history(ticker: str) -> pd.DataFrame:
    try:
        clean_ticker = ticker.split('.')[0]
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": clean_ticker,
            "outputsize": "compact",
            "apikey": AV_KEY
        }
        response = requests.get(AV_BASE, params=params, timeout=10)
        data = response.json()

        if "Time Series (Daily)" not in data:
            return pd.DataFrame()

        ts = data["Time Series (Daily)"]
        df = pd.DataFrame.from_dict(ts, orient="index")
        df.index = pd.to_datetime(df.index)
        df = df.rename(columns={
            "1. open": "Open",
            "2. high": "High",
            "3. low": "Low",
            "4. close": "Close",
            "5. volume": "Volume"
        }).astype(float).sort_index()
        return df
    except Exception:
        return pd.DataFrame()


def get_recent_news(ticker: str) -> list:
    try:
        url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.content, "lxml-xml")
        items = soup.find_all("item")[:5]
        news_list = []
        for item in items:
            # Safely extract link — handle both text and tag formats
            try:
                link = item.find("link").next_sibling.strip()
            except Exception:
                try:
                    link = item.link.text.strip()
                except Exception:
                    link = "#"

            news_list.append({
                "title": item.title.text,
                "link": link,
                "pubDate": item.pubDate.text
            })

        return news_list or [{"title": "No recent news found.", "link": "#", "pubDate": "N/A"}]
    except Exception as e:
        return [{"title": f"News fetch error: {str(e)}", "link": "#", "pubDate": "N/A"}]
    
def get_technical_indicators(df: pd.DataFrame) -> dict:
    """Calculate RSI and Moving Averages from price history dataframe."""
    try:
        if df.empty or len(df) < 20:
            return {}

        close = df["Close"]

        # Moving Averages
        ma_20 = close.rolling(window=20).mean().iloc[-1]
        ma_50 = close.rolling(window=50).mean().iloc[-1]
        current_price = close.iloc[-1]

        # RSI (14-period)
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(window=14).mean()
        loss = -delta.clip(upper=0).rolling(window=14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]

        # Trend signal
        if current_price > ma_20 > ma_50:
            trend = "Bullish — price above both MA20 and MA50"
        elif current_price < ma_20 < ma_50:
            trend = "Bearish — price below both MA20 and MA50"
        else:
            trend = "Mixed — price between moving averages"

        # RSI signal
        if rsi > 70:
            rsi_signal = "Overbought (RSI > 70) — potential pullback risk"
        elif rsi < 30:
            rsi_signal = "Oversold (RSI < 30) — potential bounce opportunity"
        else:
            rsi_signal = "Neutral range"

        return {
            "Current Price": round(float(current_price), 2),
            "MA20": round(float(ma_20), 2),
            "MA50": round(float(ma_50), 2),
            "RSI (14)": round(float(rsi), 2),
            "Trend Signal": trend,
            "RSI Signal": rsi_signal,
        }
    except Exception as e:
        return {"error": f"Technical indicator calculation failed: {str(e)}"}