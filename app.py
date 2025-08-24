# app.py
import json
import streamlit as st
from preprocess import clean_text, detect_language
from sentiment_model import analyze_sentiment
from fetch_data import fetch_twitter_data, fetch_youtube_by_keyword, fetch_youtube_by_channel
from visualize import plot_sentiment_pie, plot_platform_bar

st.set_page_config(page_title="Sentiment Dashboard", layout="wide")

# ---- load translations ----
with open("translations.json", "r", encoding="utf-8") as f:
    I18N = json.load(f)

def t(lang, key, fallback=None):
    return I18N.get(lang, {}).get(key, fallback or key)

# ---- sidebar ----
st.sidebar.title("📊 Sentiment Dashboard")
lang = st.sidebar.selectbox("🌐 Language", ["English", "Tamil", "Hindi"])
menu = st.sidebar.radio(
    t(lang, "menu", "Menu"),
    [t(lang,"product_analysis","Product / Feedback Analysis"),
     t(lang,"creator_insights","Content Creator Insights")]
)

st.title(t(lang,"app_title","Sentiment Analysis Dashboard"))
st.caption(t(lang,"tagline","Fast, multilingual (Tamil/English/Hindi), emoji-aware"))

# ---- Home / Live Check ----
with st.expander(t(lang,"live_quick_check","Live Quick Check"), expanded=True):
    st.write(t(lang,"quick_check_desc","Type a keyword to preview a few latest items quickly."))

# ===== PRODUCT / FEEDBACK ANALYSIS =====
if menu == t(lang,"product_analysis","Product / Feedback Analysis"):
    st.subheader(t(lang,"select_product","Enter Product Name / Keyword"))
    col1, col2 = st.columns([2,1])
    with col1:
        keyword = st.text_input(t(lang,"product_name","Product / Topic Name"), placeholder="e.g., iPhone 15")
    with col2:
        max_items = st.number_input(t(lang,"items_per_platform","Items per platform"), min_value=50, max_value=400, value=200, step=50)

    if st.button(t(lang,"analyze_button","Analyze")) and keyword.strip():
        with st.spinner(t(lang,"fetching_data","Fetching latest data…")):
            tweets = fetch_twitter_data(keyword, limit=max_items)
            yt_comments = fetch_youtube_by_keyword(keyword, max_videos=5, max_comments_per_video=max_items//5)

        # unify records
        records = []
        twitter_views = len(tweets)
        yt_views = sum([c.get("viewCount",0) for c in yt_comments])
        
        for txt in tweets:
            cleaned = clean_text(txt)
            lang_detected = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lang_detected)
            records.append({"text": txt, "clean": cleaned, "lang": lang_detected, "sent": sent, "src":"Twitter"})

        for item in yt_comments:
            cleaned = clean_text(item["text"])
            lang_detected = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lang_detected)
            records.append({"text": item["text"], "clean": cleaned, "lang": lang_detected, "sent": sent, "src":"YouTube","videoTitle":item.get("videoTitle","")})

        # Charts
        c1,c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_sentiment_pie(records), use_container_width=True)
        with c2:
            st.plotly_chart(plot_platform_bar(twitter_views, yt_views), use_container_width=True)

        # Pros & Cons extraction
        from collections import Counter
        def extract_phrases(records, sentiment):
            phrases = []
            for r in records:
                if r["sent"] == sentiment:
                    phrases.extend([p.strip() for p in r["text"].split('.') if len(p.strip())>3])
            counter = Counter(phrases)
            return [p for p,_ in counter.most_common(5)]
        
        st.markdown("### Pros & Cons")
        pros = extract_phrases(records, "Positive")
        cons = extract_phrases(records, "Negative")
        st.write("**Pros:**")
        for p in pros:
            st.write("- "+p)
        st.write("**Cons:**")
        for c in cons:
            st.write("- "+c)

# ===== CONTENT CREATOR INSIGHTS =====
if menu == t(lang,"creator_insights","Content Creator Insights"):
    st.subheader(t(lang,"select_channel","Enter YouTube Channel ID"))
    col1,col2 = st.columns([2,1])
    with col1:
        channel_id = st.text_input(t(lang,"channel_id","Channel ID"), placeholder="e.g., UC_x5XG1OV2P6uZZ5FSM9Ttw")
    with col2:
        max_videos = st.number_input(t(lang,"videos_to_analyze","Videos to analyze"), min_value=5,max_value=50,value=20,step=5)
    max_comments = st.slider(t(lang,"comments_per_video","Comments per video"),50,300,200,50)

    if st.button(t(lang,"analyze_channel","Analyze Channel")) and channel_id.strip():
        with st.spinner(t(lang,"fetching_channel","Fetching channel comments…")):
            yt_comments = fetch_youtube_by_channel(channel_id,max_videos=max_videos,max_comments_per_video=max_comments)

        records=[]
        for item in yt_comments:
            cleaned = clean_text(item["text"])
            lang_detected = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lang_detected)
            rec = {"text": item["text"], "clean": cleaned, "lang": lang_detected, "sent": sent, "src":"YouTube","videoTitle":item.get("videoTitle",""),"views":item.get("viewCount",0)}
            records.append(rec)

        from collections import Counter
        sent_counts = Counter([r["sent"] for r in records])
        total_comments = len(records)
        pos = sent_counts.get("Positive",0)
        neu = sent_counts.get("Neutral",0)
        neg = sent_counts.get("Negative",0)

        colA,colB,colC,colD = st.columns(4)
        colA.metric("Total Comments", f"{total_comments}")
        colB.metric("Positive %", f"{(pos/total_comments)*100:.1f}%")
        colC.metric("Neutral %", f"{(neu/total_comments)*100:.1f}%")
        colD.metric("Negative %", f"{(neg/total_comments)*100:.1f}%")

        st.plotly_chart(plot_sentiment_pie(records), use_container_width=True)
