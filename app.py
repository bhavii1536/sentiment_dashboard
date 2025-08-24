import streamlit as st
import json
from preprocess import clean_text, detect_language
from sentiment_model import analyze_sentiment
from fetch_data import fetch_twitter_data, fetch_youtube_by_keyword, fetch_youtube_by_channel
from visualize import plot_sentiment_pie, plot_platform_bar
from collections import Counter
import pandas as pd

st.set_page_config(page_title="Sentiment Dashboard", layout="wide")

# ---- Load translations ----
with open("translations.json","r",encoding="utf-8") as f:
    I18N = json.load(f)

def t(lang,key):
    return I18N.get(lang,{}).get(key,key)

# ---- Language selector ----
lang = st.sidebar.selectbox("Language", ["English","Tamil","Hindi"])
menu = st.sidebar.radio(t(lang,"menu"), [t(lang,"product_analysis"), t(lang,"creator_insights")])

st.title(t(lang,"app_title"))
st.caption(t(lang,"tagline"))

# --- Product / Feedback Analysis ---
if menu == t(lang,"product_analysis"):
    keyword = st.text_input(t(lang,"product_name"), placeholder="e.g., iPhone 15")
    max_items = st.number_input(t(lang,"items_per_platform"), min_value=50,max_value=400,value=200,step=50)
    if st.button(t(lang,"analyze_button")) and keyword.strip():
        with st.spinner(t(lang,"fetching_data")):
            # Fetch data
            tweets = fetch_twitter_data(keyword,limit=max_items)
            yt_comments = fetch_youtube_by_keyword(keyword, max_videos=5, max_comments_per_video=max_items//5)
        
        records = []
        # Twitter
        for txt in tweets:
            cleaned = clean_text(txt)
            lg = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lg)
            records.append({"text":txt,"clean":cleaned,"lang":lg,"sent":sent,"src":"Twitter","views":1})
        # YouTube
        for c in yt_comments:
            cleaned = clean_text(c["text"])
            lg = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lg)
            records.append({"text":c["text"],"clean":cleaned,"lang":lg,"sent":sent,"src":"YouTube","views":c.get("viewCount",1)})

        # --- Visualizations ---
        st.subheader(t(lang,"results"))
        st.plotly_chart(plot_sentiment_pie(records), use_container_width=True)
        st.plotly_chart(plot_platform_bar(records), use_container_width=True)

        # --- Pros & Cons extraction (frequent phrases) ---
        all_clean = [r["clean"] for r in records]
        # Create 2-word phrases
        phrases = []
        for txt in all_clean:
            words = txt.split()
            phrases.extend([f"{words[i]} {words[i+1]}" for i in range(len(words)-1)])
        cnt = Counter(phrases)
        # Separate positive and negative
        pos_phrases = [p for p in cnt if analyze_sentiment(p)=="Positive"]
        neg_phrases = [p for p in cnt if analyze_sentiment(p)=="Negative"]
        st.subheader("Pros:")
        st.write(", ".join(pos_phrases[:10]))
        st.subheader("Cons:")
        st.write(", ".join(neg_phrases[:10]))

# --- Content Creator Insights ---
if menu == t(lang,"creator_insights"):
    channel_id = st.text_input(t(lang,"channel_id"), placeholder="e.g., UC_x5XG1OV2P6uZZ5FSM9Ttw")
    max_videos = st.number_input(t(lang,"videos_to_analyze"), min_value=5,max_value=50,value=20,step=5)
    max_comments = st.number_input(t(lang,"comments_per_video"), min_value=50,max_value=300,value=100,step=50)
    if st.button(t(lang,"analyze_channel")) and channel_id.strip():
        with st.spinner(t(lang,"fetching_channel")):
            yt_comments = fetch_youtube_by_channel(channel_id, max_videos=max_videos, max_comments_per_video=max_comments)
        
        records = []
        for c in yt_comments:
            cleaned = clean_text(c["text"])
            lg = detect_language(cleaned)
            sent = analyze_sentiment(cleaned, lg)
            records.append({"text":c["text"],"clean":cleaned,"lang":lg,"sent":sent,"src":"YouTube","videoTitle":c.get("videoTitle",""),"views":c.get("viewCount",0)})

        df = pd.DataFrame(records)
        # Overall sentiment
        st.subheader(t(lang,"overall_sentiment"))
        st.plotly_chart(plot_sentiment_pie(records), use_container_width=True)
        # Platform not needed (YouTube only), but video-wise comparison
        video_group = df.groupby("videoTitle")["sent"].apply(list).to_dict()
        video_pos_rate = {v:(sum(1 for s in lst if s=="Positive")/len(lst))*100 for v,lst in video_group.items()}
        video_neg_rate = {v:(sum(1 for s in lst if s=="Negative")/len(lst))*100 for v,lst in video_group.items()}
        video_df = pd.DataFrame({"video":list(video_pos_rate.keys()),"Positive":list(video_pos_rate.values()),"Negative":list(video_neg_rate.values())})
        st.subheader("Video Sentiment Comparison")
        st.bar_chart(video_df.set_index("video"))
        # Channel summary
        total_comments = len(records)
        total_positive = sum(1 for r in records if r["sent"]=="Positive")
        total_negative = sum(1 for r in records if r["sent"]=="Negative")
        total_neutral = sum(1 for r in records if r["sent"]=="Neutral")
        st.subheader("Channel Summary")
        st.write(f"Total Comments Analyzed: {total_comments}")
        st.write(f"Positive: {total_positive} ({total_positive/total_comments*100:.1f}%)")
        st.write(f"Negative: {total_negative} ({total_negative/total_comments*100:.1f}%)")
        st.write(f"Neutral: {total_neutral} ({total_neutral/total_comments*100:.1f}%)")
