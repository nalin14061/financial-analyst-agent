# agent.py
import streamlit as st
from groq import Groq
from tools import get_stock_fundamentals, get_recent_news, get_price_history, get_technical_indicators

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def run_financial_analysis(ticker: str, technical: dict = None) -> str:
    fundamentals = get_stock_fundamentals(ticker)
    news = get_recent_news(ticker)

    # Format technical block for prompt
    if technical and "error" not in technical:
        technical_block = f"""
Current Price:  ${technical.get('Current Price')}
MA20:           ${technical.get('MA20')}
MA50:           ${technical.get('MA50')}
RSI (14):       {technical.get('RSI (14)')}
Trend Signal:   {technical.get('Trend Signal')}
RSI Signal:     {technical.get('RSI Signal')}
"""
    else:
        technical_block = "Technical indicator data unavailable."

    prompt = f"""
    You are an expert financial analyst combining fundamental, technical, and sentiment analysis.
    Analyze the following data for ticker symbol: {ticker}

    --- FUNDAMENTALS ---
    {fundamentals}

    --- TECHNICAL INDICATORS ---
    {technical_block}

    --- RECENT NEWS HEADLINES ---
    {news}

    Structure your response exactly like this:

    ## Executive Summary
    (Brief overview combining price action, valuation, and sentiment)

    ## Fundamental Analysis
    (Analyze PE, EPS, margins, market cap, and analyst target price)

    ## Technical Analysis
    (Interpret MA20, MA50, RSI. State whether technicals support buying, selling, or waiting)

    ## News Sentiment & Catalyst Analysis
    (Synthesize headlines. State: Bullish, Bearish, or Neutral — and the key catalyst)

    ## Investment Recommendation
    (Combine all three lenses — fundamental + technical + sentiment — for a Buy/Sell/Hold call with risk disclaimer)
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a precise, data-driven financial analyst who combines fundamental, technical, and news sentiment analysis."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content