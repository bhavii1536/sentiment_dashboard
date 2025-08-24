import json, streamlit as st
from preprocess import clean_text, detect_language
from sentiment_model import analyze_sentiment
from fetch_data import fetch_twitter_data, fetch_youtube_by_keyword
from visualize import plot_sentiment_pie, plot_platform_bar
from collections import Counter

st.set_page_config(page_title="Sentiment Dashboard", layout="wide")

# Load translations
with open("translations.json","r",encoding="utf-8") as f: I18N=json.load(f)
def t(lang,key,fallback=None): return I18N.get(lang,{}).get(key,fallback or key)

# Sidebar
st.sidebar.title("📊 Sentiment Dashboard")
lang = st.sidebar.selectbox("🌐 Language", ["English","Tamil","Hindi"])
menu = st.sidebar.radio(t(lang,"Menu","Menu"), [t(lang,"Product/Feedback Analysis","Product/Feedback Analysis"), t(lang,"Content Creator Insights","Content Creator Insights")])

st.title(t(lang,"Sentiment Analysis Dashboard","Sentiment Analysis Dashboard"))

# --- Product / Feedback Analysis ---
if menu == t(lang,"Product/Feedback Analysis","Product/Feedback Analysis"):
    keyword = st.text_input(t(lang,"Product / Topic Name","Product / Topic Name"))
    max_items = st.number_input(t(lang,"Items per platform","Items per platform"),50,400,200,50)
    if st.button(t(lang,"Analyze","Analyze")) and keyword.strip():
        with st.spinner("Fetching data..."):
            tweets = fetch_twitter_data(keyword, max_items)
            yt_comments = fetch_youtube_by_keyword(keyword, max_videos=5, max_comments_per_video=max_items//5)

        records=[]
        # Twitter
        for t in tweets:
            txt=clean_text(t)
            lg=detect_language(txt)
            sent=analyze_sentiment(txt,lg)
            records.append({"text":t,"clean":txt,"lang":lg,"sent":sent,"src":"Twitter"})
        # YouTube
        for yt in yt_comments:
            txt=clean_text(yt["text"])
            lg=detect_language(txt)
            sent=analyze_sentiment(txt,lg)
            records.append({"text":yt["text"],"clean":txt,"lang":lg,"sent":sent,"src":"YouTube","videoTitle":yt.get("videoTitle","")})

        # Pie chart
        st.plotly_chart(plot_sentiment_pie(records), use_container_width=True)
        # Platform bar
        st.plotly_chart(plot_platform_bar(records), use_container_width=True)

        # Pros / Cons extraction
        all_texts = [r["clean"] for r in records]
        pos_words = [r["text"] for r in records if r["sent"]=="Positive"]
        neg_words = [r["text"] for r in records if r["sent"]=="Negative"]

        st.markdown("### Pros:")
        st.write(pos_words[:10] or "No positive comments")
        st.markdown("### Cons:")
        st.write(neg_words[:10] or "No negative comments")

# --- Content Creator Insights ---
if menu == t(lang,"Content Creator Insights","Content Creator Insights"):
    channel_id = st.text_input(t(lang,"Channel ID","Channel ID"))
    max_videos = st.number_input(t(lang,"Videos to analyze","Videos to analyze"),5,50,20,5)
    max_comments = st.slider(t(lang,"Comments per video","Comments per video"),50,300,200,50)
    if st.button(t(lang,"Analyze Channel","Analyze Channel")) and channel_id.strip():
        yt_comments = fetch_youtube_by_keyword(channel_id, max_videos=max_videos, max_comments_per_video=max_comments)
        records=[]
        for yt in yt_comments:
            txt=clean_text(yt["text"])
            lg=detect_language(txt)
            sent=analyze_sentiment(txt,lg)
            records.append({"text":yt["text"],"clean":txt,"lang":lg,"sent":sent,"src":"YouTube","videoTitle":yt.get("videoTitle","")})
        st.plotly_chart(plot_sentiment_pie(records), use_container_width=True)
        st.plotly_chart(plot_platform_bar(records), use_container_width=True)
