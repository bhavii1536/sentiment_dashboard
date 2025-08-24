import streamlit as st
import json
from preprocess import clean_text, detect_language
from sentiment_model import analyze_sentiment
from fetch_data import fetch_twitter_data, fetch_youtube_by_keyword
from visualize import plot_sentiment_pie, plot_platform_bar
from collections import Counter

st.set_page_config(page_title="Sentiment Dashboard", layout="wide")

# ---- translations ----
with open("translations.json","r",encoding="utf-8") as f:
    I18N = json.load(f)

def t(lang,key):
    return I18N.get(lang,{}).get(key,key)

lang = st.sidebar.selectbox("Language", ["English","Tamil","Hindi"])
menu = st.sidebar.radio(t(lang,"menu"), [t(lang,"product_analysis"), t(lang,"creator_insights")])

st.title(t(lang,"app_title"))
st.caption(t(lang,"tagline"))

if menu == t(lang,"product_analysis"):
    keyword = st.text_input(t(lang,"product_name"), placeholder="e.g., iPhone 15")
    max_items = st.number_input("Items per platform", min_value=50,max_value=400,value=200,step=50)
    if st.button(t(lang,"analyze_button")) and keyword.strip():
        with st.spinner("Fetching data..."):
            tweets = fetch_twitter_data(keyword,limit=max_items)
            yt_comments = fetch_youtube_by_keyword(keyword, max_videos=5, max_comments_per_video=max_items//5)
        records = []
        for txt in tweets:
            cleaned = clean_text(txt)
            lg = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lg)
            records.append({"text":txt,"clean":cleaned,"lang":lg,"sent":sent,"src":"Twitter"})
        for c in yt_comments:
            cleaned = clean_text(c["text"])
            lg = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lg)
            records.append({"text":c["text"],"clean":cleaned,"lang":lg,"sent":sent,"src":"YouTube"})
        st.plotly_chart(plot_sentiment_pie(records), use_container_width=True)
        st.plotly_chart(plot_platform_bar(records), use_container_width=True)

        # Pros & Cons (extract top repeated words)
        all_clean = [r["clean"] for r in records]
        words = []
        for txt in all_clean:
            words.extend([w for w in txt.split() if len(w)>2])
        cnt = Counter(words)
        pos_words = [w for w in cnt if analyze_sentiment(w)=="Positive"]
        neg_words = [w for w in cnt if analyze_sentiment(w)=="Negative"]
        st.subheader("Pros:")
        st.write(", ".join(pos_words[:10]))
        st.subheader("Cons:")
        st.write(", ".join(neg_words[:10]))

if menu == t(lang,"creator_insights"):
    st.write("Content Creator Insights Coming Soon")
