# app.py
import json
import streamlit as st
from collections import Counter
from preprocess import clean_text, detect_language
from sentiment_model import analyze_sentiment
from fetch_data import fetch_twitter_data, fetch_youtube_by_keyword
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
    [t(lang,"Product/Feedback Analysis","Product/Feedback Analysis")]
)

st.title(t(lang, "app_title", "Sentiment Analysis Dashboard"))
st.caption(t(lang, "tagline", "Fast, multilingual (Tamil/English/Hindi), emoji-aware"))

# ---- PRODUCT / FEEDBACK ANALYSIS ----
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
            # Extract common pros (positive) and cons (negative)
            pros = df[df["sent"]=="Positive"]["clean"].tolist()
            cons = df[df["sent"]=="Negative"]["clean"].tolist()

            # Simple frequency-based top phrases
            from collections import Counter
            def get_top_phrases(lst, n=5):
                all_words = " ".join(lst).split()
                freq = Counter(all_words)
                return [word for word, count in freq.most_common(n)]

            st.markdown("**Pros:**")
            pros_top = get_top_phrases(pros)
            for p in pros_top:
                st.write(f"- {p}")

            st.markdown("**Cons:**")
            cons_top = get_top_phrases(cons)
            for c in cons_top:
                st.write(f"- {c}")
        else:
            st.write("No comments found.")
