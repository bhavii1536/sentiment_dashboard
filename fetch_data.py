import os
from typing import List, Dict
import snscrape.modules.twitter as snt
import streamlit as st
from googleapiclient.discovery import build

# ---- Twitter snscrape ----
def fetch_twitter_data(keyword: str, limit: int = 200) -> List[str]:
    texts = []
    for i, tweet in enumerate(snt.TwitterSearchScraper(f'{keyword} lang:en OR lang:ta OR lang:hi').get_items()):
        texts.append(tweet.content)
        if i+1 >= limit:
            break
    return texts

# ---- YouTube API ----
def _yt_build():
    YT_API_KEY = st.secrets["YOUTUBE_API"]["YOUTUBE_API_KEY"]
    return build("youtube", "v3", developerKey=YT_API_KEY, cache_discovery=False)

def _yt_comments_for_video(service, video_id: str, video_title: str, max_comments=200) -> List[Dict]:
    comments = []
    page = None
    while len(comments) < max_comments:
        req = service.commentThreads().list(
            part="snippet", videoId=video_id, maxResults=min(100, max_comments - len(comments)),
            pageToken=page, textFormat="plainText", order="time"
        )
        resp = req.execute()
        for it in resp.get("items", []):
            top = it["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "text": top.get("textDisplay",""),
                "videoId": video_id,
                "videoTitle": video_title
            })
            if len(comments) >= max_comments:
                break
        page = resp.get("nextPageToken")
        if not page:
            break
    return comments

def fetch_youtube_by_keyword(keyword: str, max_videos=5, max_comments_per_video=100) -> List[Dict]:
    service = _yt_build()
    search = service.search().list(q=keyword, part="snippet", type="video", maxResults=max_videos, order="date").execute()
    videos = [{"videoId": v["id"]["videoId"], "videoTitle": v["snippet"]["title"]} for v in search.get("items",[])]
    all_comments = []
    for v in videos:
        all_comments.extend(_yt_comments_for_video(service, v["videoId"], v["videoTitle"], max_comments=max_comments_per_video))
    return all_comments
