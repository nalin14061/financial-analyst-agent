# app.py
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from agent import run_financial_analysis
from tools import get_recent_news, get_price_history, get_technical_indicators
from pdf_exporter import generate_pdf
from datetime import datetime

st.set_page_config(page_title="AI Financial Analyst Agent", layout="wide")
st.title("📈 Real-Time AI Financial Analyst Agent")
st.caption("Powered by Groq Llama 3.3 · Alpha Vantage · Google News RSS")

# --- MODE SELECTOR ---
mode = st.sidebar.radio(
    "Analysis Mode",
    ["Single Ticker", "Multi-Ticker Comparison"],
    index=0
)

# ─────────────────────────────────────────────
# SINGLE TICKER MODE (your existing flow)
# ─────────────────────────────────────────────
if mode == "Single Ticker":
    st.sidebar.header("Asset Monitor")
    ticker_input = st.sidebar.text_input(
        "Enter Ticker (e.g., AAPL, NVDA, RELIANCE.NS):",
        value="AAPL"
    ).upper().strip()

    if st.sidebar.button("Run Analysis"):
        if ticker_input:
            with st.spinner(f"Analyzing {ticker_input}..."):

                hist = get_price_history(ticker_input)
                technical = get_technical_indicators(hist)

                st.subheader("📊 Price Action + Technical Indicators")

                if not hist.empty:
                    hist["MA20"] = hist["Close"].rolling(window=20).mean()
                    hist["MA50"] = hist["Close"].rolling(window=50).mean()
                    delta = hist["Close"].diff()
                    gain = delta.clip(lower=0).rolling(window=14).mean()
                    loss = -delta.clip(upper=0).rolling(window=14).mean()
                    hist["RSI"] = 100 - (100 / (1 + gain / loss))

                    fig = make_subplots(
                        rows=2, cols=1,
                        shared_xaxes=True,
                        row_heights=[0.7, 0.3],
                        vertical_spacing=0.05
                    )
                    fig.add_trace(go.Candlestick(
                        x=hist.index,
                        open=hist["Open"], high=hist["High"],
                        low=hist["Low"], close=hist["Close"],
                        name="Price"
                    ), row=1, col=1)
                    fig.add_trace(go.Scatter(
                        x=hist.index, y=hist["MA20"],
                        line=dict(color="cyan", width=1.5), name="MA20"
                    ), row=1, col=1)
                    fig.add_trace(go.Scatter(
                        x=hist.index, y=hist["MA50"],
                        line=dict(color="orange", width=1.5), name="MA50"
                    ), row=1, col=1)
                    fig.add_trace(go.Scatter(
                        x=hist.index, y=hist["RSI"],
                        line=dict(color="violet", width=1.5), name="RSI (14)"
                    ), row=2, col=1)
                    fig.add_hline(y=70, line_dash="dash", line_color="red",
                                  annotation_text="Overbought", row=2, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="green",
                                  annotation_text="Oversold", row=2, col=1)
                    fig.update_layout(
                        xaxis_rangeslider_visible=False,
                        template="plotly_dark",
                        height=550,
                        margin=dict(l=10, r=10, t=10, b=10),
                        legend=dict(orientation="h", y=1.05)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    if technical and "error" not in technical:
                        st.subheader("📐 Technical Snapshot")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Current Price", f"${technical['Current Price']}")
                        c2.metric("MA20", f"${technical['MA20']}")
                        c3.metric("MA50", f"${technical['MA50']}")
                        c4.metric("RSI (14)", technical["RSI (14)"])
                        st.info(f"📊 Trend: {technical['Trend Signal']}")
                        st.info(f"📉 RSI Signal: {technical['RSI Signal']}")
                else:
                    st.warning("⚠️ Chart unavailable — Alpha Vantage may be rate-limited.")

                st.divider()

                col1, col2 = st.columns([2, 3])
                with col1:
                    st.subheader("📰 Live News Feed")
                    news = get_recent_news(ticker_input)
                    for i, article in enumerate(news, 1):
                        st.markdown(f"**{i}. {article.get('title', 'N/A')}**")
                        st.caption(
                            f"{article.get('pubDate', '')} | "
                            f"[Source]({article.get('link', '#')})"
                        )
                        st.divider()

                with col2:
                    st.subheader("🤖 AI Analysis Report")
                    try:
                        report = run_financial_analysis(ticker_input, technical=technical)
                        st.markdown(report)

                        # ── PDF Export Button ──────────────────────────
                        st.divider()
                        news_for_pdf = get_recent_news(ticker_input)
                        pdf_bytes = generate_pdf(
                            ticker=ticker_input,
                            report=report,
                            technical=technical,
                            news=news_for_pdf
                        )
                        st.download_button(
                            label="📄 Download Full Report as PDF",
                            data=pdf_bytes,
                            file_name=f"{ticker_input}_analysis_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"Agent error: {e}")
        else:
            st.warning("Please enter a ticker symbol.")


# ─────────────────────────────────────────────
# MULTI-TICKER COMPARISON MODE
# ─────────────────────────────────────────────
else:
    st.sidebar.header("Comparison Settings")
    st.sidebar.caption("Enter 2 or 3 tickers to compare side by side.")

    t1 = st.sidebar.text_input("Ticker 1", value="AAPL").upper().strip()
    t2 = st.sidebar.text_input("Ticker 2", value="NVDA").upper().strip()
    t3 = st.sidebar.text_input("Ticker 3 (optional)", value="").upper().strip()

    tickers = [t for t in [t1, t2, t3] if t]

    if st.sidebar.button("Run Comparison"):
        if len(tickers) < 2:
            st.warning("Please enter at least 2 tickers.")
        else:
            # ── 1. NORMALISED PRICE OVERLAY CHART ──────────────────────────
            st.subheader(f"📊 Normalised Price Performance — {' vs '.join(tickers)}")
            st.caption("All prices rebased to 100 at start of period for fair comparison.")

            color_map = {0: "cyan", 1: "orange", 2: "violet"}
            overlay_fig = go.Figure()
            price_data = {}   # store for later reuse

            for idx, ticker in enumerate(tickers):
                with st.spinner(f"Fetching price data for {ticker}..."):
                    hist = get_price_history(ticker)
                    price_data[ticker] = hist

                if not hist.empty:
                    normalised = (hist["Close"] / hist["Close"].iloc[0]) * 100
                    overlay_fig.add_trace(go.Scatter(
                        x=hist.index,
                        y=normalised,
                        name=ticker,
                        line=dict(color=color_map[idx], width=2)
                    ))

            overlay_fig.update_layout(
                template="plotly_dark",
                height=400,
                yaxis_title="Rebased Price (Start = 100)",
                legend=dict(orientation="h", y=1.05),
                margin=dict(l=10, r=10, t=10, b=10)
            )
            st.plotly_chart(overlay_fig, use_container_width=True)

            # ── 2. TECHNICAL SNAPSHOT TABLE ────────────────────────────────
            st.subheader("📐 Technical Indicators — Side by Side")

            tech_rows = []
            tech_data = {}
            for ticker in tickers:
                hist = price_data.get(ticker, pd.DataFrame())
                tech = get_technical_indicators(hist)
                tech_data[ticker] = tech
                tech_rows.append({
                    "Ticker": ticker,
                    "Price": f"${tech.get('Current Price', 'N/A')}",
                    "MA20":  f"${tech.get('MA20', 'N/A')}",
                    "MA50":  f"${tech.get('MA50', 'N/A')}",
                    "RSI":   tech.get("RSI (14)", "N/A"),
                    "Trend": tech.get("Trend Signal", "N/A"),
                    "RSI Signal": tech.get("RSI Signal", "N/A"),
                })

            st.dataframe(
                pd.DataFrame(tech_rows).set_index("Ticker"),
                use_container_width=True
            )

            st.divider()

            # ── 3. PER-TICKER AI REPORTS ────────────────────────────────────
            st.subheader("🤖 Individual AI Reports")
            cols = st.columns(len(tickers))

            for idx, ticker in enumerate(tickers):
                with cols[idx]:
                    st.markdown(f"### {ticker}")
                    with st.spinner(f"Generating report for {ticker}..."):
                        try:
                            report = run_financial_analysis(
                                ticker,
                                technical=tech_data.get(ticker, {})
                            )
                            st.markdown(report)
                        except Exception as e:
                            st.error(f"Error for {ticker}: {e}")

            st.divider()

            # ── 4. HEAD-TO-HEAD AI VERDICT ──────────────────────────────────
            st.subheader("⚖️ Head-to-Head AI Verdict")
            with st.spinner("Generating comparative verdict..."):
                try:
                    comparison_prompt = f"""
                    You are a senior portfolio manager comparing multiple stocks for a client.

                    The following tickers have been analyzed: {', '.join(tickers)}

                    Technical snapshot:
                    {pd.DataFrame(tech_rows).to_string(index=False)}

                    Provide a concise head-to-head comparison structured exactly like this:

                    ## Comparative Overview
                    (One paragraph summarizing how these stocks differ in trend and momentum)

                    ## Relative Strengths
                    (For each ticker, one bullet point on its key advantage)

                    ## Relative Weaknesses
                    (For each ticker, one bullet point on its key risk)

                    ## Portfolio Verdict
                    (Which ticker presents the strongest risk-adjusted opportunity right now, and why.
                    Include a professional risk disclaimer.)
                    """

                    from groq import Groq
                    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                    verdict_response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are a senior portfolio manager providing concise, data-driven comparative stock analysis."},
                            {"role": "user", "content": comparison_prompt}
                        ],
                        temperature=0.2
                    )
                    st.markdown(verdict_response.choices[0].message.content)
                except Exception as e:
                    st.error(f"Verdict generation error: {e}")