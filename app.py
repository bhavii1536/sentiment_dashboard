# app.py
import json
import streamlit as st
from preprocess import clean_text, detect_language
from sentiment_model import analyze_sentiment
from fetch_data import fetch_twitter_data, fetch_youtube_by_keyword, fetch_youtube_by_channel
from visualize import plot_sentiment_pie
import plotly.graph_objects as go
from collections import Counter

st.set_page_config(page_title="Sentiment Dashboard", layout="wide")

# ---- Load translations ----
with open("translations.json", "r", encoding="utf-8") as f:
    I18N = json.load(f)

def t(lang, key, fallback=None):
    return I18N.get(lang, {}).get(key, fallback or key)

# ---- Sidebar ----
st.sidebar.title("📊 " + t("en", "app_title"))
lang = st.sidebar.selectbox("🌐 Language", ["English", "Tamil", "Hindi"], index=0)
menu = st.sidebar.radio(
    t(lang, "menu", "Menu"),
    [t(lang, "product_analysis", "Product / Feedback Analysis"),
     t(lang, "creator_insights", "Content Creator Insights")]
)

st.title(t(lang, "app_title", "Sentiment Analysis Dashboard"))
st.caption(t(lang, "tagline", "Fast, multilingual (Tamil/English/Hindi), emoji-aware"))

# ---- Helper functions ----
def extract_feedback_comments(records, top_n=5, sentiment="Positive"):
    """Extract top N meaningful comments by sentiment"""
    filtered = [r["text"] for r in records if r["sent"]==sentiment and len(r["text"].strip())>5]
    filtered = list(dict.fromkeys(filtered))  # remove duplicates
    return filtered[:top_n]

# ===== PRODUCT / FEEDBACK ANALYSIS =====
if menu == t(lang,"product_analysis","Product / Feedback Analysis"):
    st.subheader(t(lang, "select_product","Enter Product Name / Keyword"))
    col1, col2 = st.columns([2,1])
    with col1:
        keyword = st.text_input(t(lang, "product_name","Product / Topic Name"), placeholder="e.g., iPhone 15")
    with col2:
        max_items = st.number_input(t(lang, "items_per_platform","Items per platform"), min_value=50, max_value=400, value=200, step=50)

    if st.button(t(lang,"analyze_button","Analyze"), use_container_width=True) and keyword.strip():
        with st.spinner(t(lang,"fetching_data","Fetching latest data…")):
            tweets = fetch_twitter_data(keyword, limit=max_items)
            yt_comments = fetch_youtube_by_keyword(keyword, max_videos=5, max_comments_per_video=max_items//5)

        # ---- unify and analyze
        records = []
        for txt in tweets:
            cleaned = clean_text(txt)
            lg = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lg)
            records.append({"text": txt, "clean": cleaned, "lang": lg, "sent": sent, "src": "Twitter", "views": 1})

        for item in yt_comments:
            cleaned = clean_text(item["text"])
            lg = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lg)
            records.append({"text": item["text"], "clean": cleaned, "lang": lg, "sent": sent,
                            "src": "YouTube", "views": item.get("viewCount",0)})

        # ---- Charts ----
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_sentiment_pie(records), use_container_width=True)

        # Platform comparison by total views / mentions
        platforms = ["Twitter","YouTube"]
        values = [
            sum(r.get("views",1) for r in records if r["src"]=="Twitter"),
            sum(r.get("views",1) for r in records if r["src"]=="YouTube")
        ]
        fig = go.Figure([go.Bar(x=platforms, y=values, text=values, textposition="auto")])
        fig.update_layout(title="Platform Comparison (Total Views / Mentions)", xaxis_title="Platform", yaxis_title="Count / Views")
        with col2:
            st.plotly_chart(fig, use_container_width=True)

        # ---- Pros / Cons comments
        st.markdown("### Pros / Cons (User Opinions)")
        pros = extract_feedback_comments(records, top_n=5, sentiment="Positive")
        cons = extract_feedback_comments(records, top_n=5, sentiment="Negative")
        st.markdown("**Pros:**")
        for p in pros:
            st.markdown(f"- {p}")
        st.markdown("**Cons:**")
        for c in cons:
            st.markdown(f"- {c}")

# ===== CONTENT CREATOR INSIGHTS =====
if menu == t(lang,"creator_insights","Content Creator Insights"):
    st.subheader(t(lang, "select_channel","Enter YouTube Channel ID"))
    col1, col2 = st.columns([2,1])
    with col1:
        channel_id = st.text_input(t(lang,"channel_id","Channel ID"), placeholder="e.g., UC_x5XG1OV2P6uZZ5FSM9Ttw")
    with col2:
        max_videos = st.number_input(t(lang,"videos_to_analyze","Videos to analyze"), min_value=5, max_value=50, value=20, step=5)
    max_comments = st.slider(t(lang,"comments_per_video","Comments per video"), 50, 300, 200, 50)

    if st.button(t(lang,"analyze_channel","Analyze Channel"), use_container_width=True) and channel_id.strip():
        with st.spinner(t(lang,"fetching_channel","Fetching channel comments…")):
            yt_comments = fetch_youtube_by_channel(channel_id, max_videos=max_videos, max_comments_per_video=max_comments)

        records = []
        for item in yt_comments:
            cleaned = clean_text(item["text"])
            lg = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lg)
            rec = {"text": item["text"], "clean": cleaned, "lang": lg, "sent": sent, "src": "YouTube",
                   "videoTitle": item.get("videoTitle",""), "views": item.get("viewCount",0)}
            records.append(rec)

        # Charts
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_sentiment_pie(records), use_container_width=True)
        with col2:
            platforms = ["YouTube"]
            values = [sum(r.get("views",0) for r in records)]
            fig = go.Figure([go.Bar(x=platforms, y=values, text=values, textposition="auto")])
            fig.update_layout(title="Channel Views", xaxis_title="Platform", yaxis_title="Views")
            st.plotly_chart(fig, use_container_width=True)

        # KPIs
        pos = sum(1 for r in records if r["sent"]=="Positive")
        neg = sum(1 for r in records if r["sent"]=="Negative")
        neu = sum(1 for r in records if r["sent"]=="Neutral")
        total = max(1,len(records))
        colA, colB, colC, colD = st.columns(4)
        colA.metric("Total Comments", f"{total}")
        colB.metric("Positive %", f"{(pos/total)*100:0.1f}%")
        colC.metric("Neutral %", f"{(neu/total)*100:0.1f}%")
        colD.metric("Negative %", f"{(neg/total)*100:0.1f}%")

st.write("")
st.caption("Tip: Set your YT API key in Streamlit secrets as YOUTUBE_API_KEY. Twitter uses snscrape fallback if API keys are missing.")
