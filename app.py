# app.py
import json
import streamlit as st
import pandas as pd
from collections import Counter
from preprocess import clean_text, detect_language
from sentiment_model import analyze_sentiment
from fetch_data import fetch_twitter_data, fetch_youtube_by_keyword, fetch_youtube_by_channel
from visualize import plot_sentiment_pie, plot_platform_bar

st.set_page_config(page_title="Sentiment Dashboard", layout="wide")

# ---- Load translations ----
with open("translations.json", "r", encoding="utf-8") as f:
    I18N = json.load(f)

def t(lang, key, fallback=None):
    return I18N.get(lang, {}).get(key, fallback or key)

# ---- Sidebar controls ----
st.sidebar.title("📊 Sentiment Dashboard")
lang = st.sidebar.selectbox("🌐 Language", ["English", "Tamil", "Hindi"], index=0)
menu = st.sidebar.radio(
    t(lang, "menu", "Menu"),
    [t(lang,"product_analysis","Product / Feedback Analysis"),
     t(lang,"creator_insights","Content Creator Insights")]
)

st.title(t(lang, "app_title", "Sentiment Analysis Dashboard"))
st.caption(t(lang, "tagline", "Fast, multilingual (Tamil/English/Hindi), emoji-aware"))

# ---- Home section (Quick Live Check) ----
with st.expander(t(lang, "live_quick_check", "Live Quick Check"), expanded=True):
    st.write(t(lang, "quick_check_desc", "Type a keyword to preview a few latest items quickly."))

# ====== PRODUCT / FEEDBACK ANALYSIS ======
if menu == t(lang,"product_analysis","Product / Feedback Analysis"):
    st.subheader(t(lang, "select_product", "Enter Product Name / Keyword"))
    col1, col2 = st.columns([2,1])
    with col1:
        keyword = st.text_input(t(lang, "product_name", "Product / Topic Name"), placeholder="e.g., iPhone 15")
    with col2:
        max_items = st.number_input(t(lang, "items_per_platform", "Items per platform"), min_value=50, max_value=400, value=200, step=50)

    if st.button(t(lang, "analyze_button", "Analyze"), use_container_width=True) and keyword.strip():
        with st.spinner(t(lang, "fetching_data", "Fetching latest data…")):
            tweets = fetch_twitter_data(keyword, limit=max_items)
            yt_comments = fetch_youtube_by_keyword(keyword, max_videos=5, max_comments_per_video=max_items//5)

        # Shape unified records
        records = []
        for txt in tweets:
            cleaned = clean_text(txt)
            lg = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lg)
            records.append({"text": txt, "clean": cleaned, "lang": lg, "sent": sent, "src": "Twitter", "views": 1}) # views fallback

        for item in yt_comments:
            cleaned = clean_text(item["text"])
            lg = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lg)
            records.append({"text": item["text"], "clean": cleaned, "lang": lg, "sent": sent, "src": "YouTube", "videoTitle": item.get("videoTitle",""), "views": item.get("viewCount", 0)})

        # ----- Charts -----
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_sentiment_pie(records), use_container_width=True)
        with c2:
            # Platform comparison based on total views
            df = pd.DataFrame(records)
            platform_views = df.groupby("src")["views"].sum().reset_index()
            st.bar_chart(data=platform_views, x="src", y="views", height=400)

        # ----- What people actually think -----
        st.markdown(f"### {t(lang,'results','What people actually think about')} {keyword}:")
        if df.empty:
            st.write("No comments found.")
        else:
            pros_comments = df[df["sent"]=="Positive"]["clean"].tolist()
            cons_comments = df[df["sent"]=="Negative"]["clean"].tolist()

            def get_top_comments(lst, n=5):
                from collections import Counter
                counter = Counter(lst)
                top = counter.most_common(n)
                return [c for c,_ in top]

            st.markdown("**Pros:**")
            top_pros = get_top_comments(pros_comments)
            if top_pros:
                for p in top_pros:
                    st.write(f"- {p}")
            else:
                st.write("No positive comments found.")

            st.markdown("**Cons:**")
            top_cons = get_top_comments(cons_comments)
            if top_cons:
                for c in top_cons:
                    st.write(f"- {c}")
            else:
                st.write("No negative comments found.")

# ====== CONTENT CREATOR INSIGHTS (YOUTUBE) ======
if menu == t(lang,"creator_insights","Content Creator Insights"):
    st.subheader(t(lang, "select_channel", "Enter YouTube Channel ID"))
    col1, col2 = st.columns([2,1])
    with col1:
        channel_id = st.text_input(t(lang, "channel_id", "Channel ID"), placeholder="e.g., UC_x5XG1OV2P6uZZ5FSM9Ttw")
    with col2:
        max_videos = st.number_input(t(lang, "videos_to_analyze", "Videos to analyze"), min_value=5, max_value=50, value=20, step=5)
    max_comments = st.slider(t(lang, "comments_per_video", "Comments per video"), 50, 300, 200, 50)

    if st.button(t(lang, "analyze_channel", "Analyze Channel"), use_container_width=True) and channel_id.strip():
        with st.spinner(t(lang, "fetching_channel", "Fetching channel comments…")):
            yt_comments = fetch_youtube_by_channel(channel_id, max_videos=max_videos, max_comments_per_video=max_comments)

        records = []
        for item in yt_comments:
            cleaned = clean_text(item["text"])
            lg = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lg)
            rec = {"text": item["text"], "clean": cleaned, "lang": lg, "sent": sent, "src": "YouTube",
                   "videoTitle": item.get("videoTitle",""), "views": item.get("viewCount",0)}
            records.append(rec)

        st.plotly_chart(plot_sentiment_pie(records), use_container_width=True)
        st.plotly_chart(plot_platform_bar(records), use_container_width=True)

        # Quick KPIs
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
st.caption("Tip: Set your YT API key as env var or in Streamlit secrets. Twitter uses snscrape fallback if no API keys.")
