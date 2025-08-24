import streamlit as st
from fetch_data import fetch_twitter_data, fetch_youtube_comments
from preprocess import clean_text, detect_language
from sentiment_model import analyze_sentiment
from visualize import plot_sentiment_pie, plot_platform_comparison
import json

# Load translations
with open("translations.json", "r", encoding="utf-8") as f:
    translations = json.load(f)

# Sidebar UI
st.sidebar.title("📊 Sentiment Dashboard")
menu = st.sidebar.radio("Menu", ["Product/Feedback Analysis", "Content Creator Insights"])
lang = st.sidebar.radio("🌐 Language", ["English", "Tamil", "Hindi"])

# Translator helper
def t(key):
    return translations[lang].get(key, key)

st.title(t("Sentiment Analysis Dashboard"))

# Home Page: Trending
if menu == "Product/Feedback Analysis":
    st.subheader(t("Enter Product Name / Keyword"))
    keyword = st.text_input(t("Product / Topic Name"), "")

    if st.button(t("Analyze")) and keyword:
        with st.spinner("Fetching data..."):
            tweets = fetch_twitter_data(keyword)
            youtube_comments = fetch_youtube_comments(keyword)

        all_texts = tweets + youtube_comments
        results = [analyze_sentiment(clean_text(text), detect_language(text)) for text in all_texts]

        # Visualization
        st.plotly_chart(plot_sentiment_pie(results))
        st.plotly_chart(plot_platform_comparison(results, tweets, youtube_comments))

elif menu == "Content Creator Insights":
    st.subheader(t("Enter YouTube Channel ID"))
    channel_id = st.text_input(t("Channel ID"), "")

    if st.button(t("Analyze")) and channel_id:
        with st.spinner("Fetching YouTube data..."):
            youtube_comments = fetch_youtube_comments(channel_id, channel_mode=True)

        results = [analyze_sentiment(clean_text(text), detect_language(text)) for text in youtube_comments]
        st.plotly_chart(plot_sentiment_pie(results))
