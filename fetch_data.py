import os
from typing import List, Dict
import streamlit as st

# YouTube API
YT_API_KEY = st.secrets["YOUTUBE_API_KEY"]

def fetch_youtube_by_keyword(keyword: str, max_videos=5, max_comments_per_video=100) -> List[Dict]:
    from googleapiclient.discovery import build
    service = build("youtube", "v3", developerKey=YT_API_KEY, cache_discovery=False)
    search = service.search().list(q=keyword, part="snippet", type="video", maxResults=max_videos, order="date").execute()
    videos = [{"videoId": it["id"]["videoId"], "videoTitle": it["snippet"]["title"]} for it in search.get("items", [])]
    all_comments = []
    for v in videos:
        page = None
        while len(all_comments) < max_comments_per_video:
            resp = service.commentThreads().list(
                part="snippet", videoId=v["videoId"], maxResults=min(100, max_comments_per_video-len(all_comments)),
                pageToken=page, textFormat="plainText", order="time"
            ).execute()
            for it in resp.get("items", []):
                top = it["snippet"]["topLevelComment"]["snippet"]
                all_comments.append({
                    "text": top.get("textDisplay", ""),
                    "videoTitle": v["videoTitle"]
                })
            page = resp.get("nextPageToken")
            if not page: break
    return all_comments

def fetch_twitter_data(keyword: str, limit: int = 200) -> List[str]:
    try:
        import snscrape.modules.twitter as snt
        return [tweet.content for i, tweet in enumerate(
            snt.TwitterSearchScraper(f'{keyword} lang:en OR lang:ta OR lang:hi').get_items()
        ) if i < limit]
    except:
        return []
