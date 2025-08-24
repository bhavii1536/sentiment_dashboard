# app.py
import json
import streamlit as st
from collections import Counter
from preprocess import clean_text, detect_language
from sentiment_model import analyze_sentiment
from fetch_data import fetch_twitter_data, fetch_youtube_by_keyword, fetch_youtube_by_channel
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Sentiment Dashboard", layout="wide")

# ---- Load translations ----
with open("translations.json", "r", encoding="utf-8") as f:
    I18N = json.load(f)

def t(lang, key, fallback=None):
    return I18N.get(lang.lower()[:2], {}).get(key, fallback or key)

# ---- Sidebar ----
st.sidebar.title("📊 Sentiment Dashboard")
lang = st.sidebar.selectbox("🌐 Language", ["English", "Tamil", "Hindi"])
menu = st.sidebar.radio(
    t(lang, "Menu", "Menu"),
    [t(lang,"Product/Feedback Analysis","Product/Feedback Analysis"),
     t(lang,"Content Creator Insights","Content Creator Insights")]
)

st.title(t(lang, "app_title", "Sentiment Analysis Dashboard"))
st.caption(t(lang, "tagline", "Fast, multilingual (Tamil/English/Hindi), emoji-aware"))

# ========================= PRODUCT / FEEDBACK ANALYSIS =========================
if menu == t(lang,"Product/Feedback Analysis","Product/Feedback Analysis"):
    st.subheader(t(lang, "select_product","Enter Product Name / Keyword"))
    col1, col2 = st.columns([2,1])
    with col1:
        keyword = st.text_input(t(lang,"product_name","Product / Topic Name"), placeholder="e.g., iPhone 15")
    with col2:
        max_items = st.number_input(t(lang,"items_per_platform","Items per platform"), min_value=50, max_value=400, value=200, step=50)

    if st.button(t(lang,"analyze_button","Analyze"), use_container_width=True) and keyword.strip():
        with st.spinner(t(lang,"fetching_data","Fetching latest data…")):
            # Fetch data
            tweets = fetch_twitter_data(keyword, limit=max_items)
            yt_comments = fetch_youtube_by_keyword(keyword, max_videos=5, max_comments_per_video=max_items//5)

        # ---- Analyze Sentiment ----
        records = []
        platform_views = {"Twitter": len(tweets), "YouTube": sum([c.get("viewCount",0) for c in yt_comments])}
        for txt in tweets:
            cleaned = clean_text(txt)
            lang_detected = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lang_detected)
            records.append({"text": txt, "clean": cleaned, "lang": lang_detected, "sent": sent, "src": "Twitter"})

        for c in yt_comments:
            cleaned = clean_text(c["text"])
            lang_detected = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lang_detected)
            records.append({"text": c["text"], "clean": cleaned, "lang": lang_detected, "sent": sent, "src": "YouTube"})

        # ---- Sentiment Pie Chart ----
        cnt = Counter([r["sent"] for r in records])
        labels = ["Positive","Neutral","Negative"]
        values = [cnt.get("Positive",0), cnt.get("Neutral",0), cnt.get("Negative",0)]
        fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.35)])
        fig_pie.update_layout(title="Overall Sentiment Distribution")

        # ---- Platform Comparison Bar ----
        fig_bar = go.Figure(data=[go.Bar(x=list(platform_views.keys()), y=list(platform_views.values()), text=list(platform_views.values()), textposition='auto')])
        fig_bar.update_layout(title="Platform Comparison (Total Views / Mentions)", xaxis_title="Platform", yaxis_title="Views / Mentions")

        # ---- Display Charts ----
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            st.plotly_chart(fig_bar, use_container_width=True)

        # ---- What Users Actually Think ----
        st.markdown(f"### {t(lang,'results','What people actually think about')} {keyword}:")
        df = pd.DataFrame(records)
        if not df.empty:
            pros = df[df["sent"]=="Positive"]["clean"].tolist()
            cons = df[df["sent"]=="Negative"]["clean"].tolist()

            from collections import Counter
            def get_top_phrases(lst, n=5):
                all_words = " ".join(lst).split()
                freq = Counter(all_words)
                return [word for word, count in freq.most_common(n)]

            st.markdown("**Pros:**")
            for p in get_top_phrases(pros):
                st.write(f"- {p}")

            st.markdown("**Cons:**")
            for c in get_top_phrases(cons):
                st.write(f"- {c}")
        else:
            st.write("No comments found.")

# ========================= CONTENT CREATOR INSIGHTS =========================
if menu == t(lang,"Content Creator Insights","Content Creator Insights"):
    st.subheader(t(lang, "select_channel","Enter YouTube Channel ID"))
    col1, col2 = st.columns([2,1])
    with col1:
        channel_id = st.text_input(t(lang, "channel_id", "Channel ID"), placeholder="e.g., UC_x5XG1OV2P6uZZ5FSM9Ttw")
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
                   "videoTitle": item.get("videoTitle",""), "views": item.get("viewCount", 0)}
            records.append(rec)

        # ---- Visualizations
        cnt = Counter([r["sent"] for r in records])
        labels = ["Positive","Neutral","Negative"]
        values = [cnt.get("Positive",0), cnt.get("Neutral",0), cnt.get("Negative",0)]
        fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.35)])
        fig_pie.update_layout(title="Overall Sentiment Distribution")

        fig_bar = go.Figure()
        df = pd.DataFrame(records)
        if not df.empty:
            total_views = df.groupby("src")["views"].sum()
            fig_bar.add_bar(x=total_views.index, y=total_views.values, text=total_views.values, textposition='auto')
        fig_bar.update_layout(title="Platform Comparison (Total Views)", xaxis_title="Platform", yaxis_title="Views")

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            st.plotly_chart(fig_bar, use_container_width=True)

        # Quick KPIs
        pos = sum(1 for r in records if r["sent"] == "Positive")
        neg = sum(1 for r in records if r["sent"] == "Negative")
        neu = sum(1 for r in records if r["sent"] == "Neutral")
        total = max(1, len(records))
        colA, colB, colC, colD = st.columns(4)
        colA.metric("Total Comments", f"{total}")
        colB.metric("Positive %", f"{(pos/total)*100:0.1f}%")
        colC.metric("Neutral %", f"{(neu/total)*100:0.1f}%")
        colD.metric("Negative %", f"{(neg/total)*100:0.1f}%")
