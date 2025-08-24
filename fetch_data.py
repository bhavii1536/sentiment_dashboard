import os
from typing import List, Dict
import streamlit as st

# ---- Twitter API keys (if available) ----
TW_BEARER = os.getenv("TW_BEARER")

def _twitter_v2_fetch(keyword: str, limit: int = 200) -> List[str]:
    try:
        import requests
        headers = {"Authorization": f"Bearer {TW_BEARER}"}
        url = "https://api.twitter.com/2/tweets/search/recent"
        params = {
            "query": keyword,
            "max_results": min(100, limit),
            "tweet.fields": "lang,created_at"
        }
        texts=[]
        while True:
            r=requests.get(url, headers=headers, params=params, timeout=10)
            r.raise_for_status()
            data=r.json()
            for t in data.get("data", []):
                texts.append(t.get("text",""))
                if len(texts)>=limit:
                    return texts
            if "next_token" in data.get("meta",{}):
                params["next_token"]=data["meta"]["next_token"]
            else:
                break
        return texts
    except Exception:
        return []

def _twitter_snscrape_fetch(keyword: str, limit: int = 200) -> List[str]:
    try:
        import snscrape.modules.twitter as snt  # <-- lazy import
        texts=[]
        for i,tweet in enumerate(snt.TwitterSearchScraper(f'{keyword} lang:en OR lang:ta OR lang:hi').get_items()):
            texts.append(tweet.content)
            if i+1>=limit: break
        return texts
    except Exception:
        return []

def fetch_twitter_data(keyword: str, limit: int = 200) -> List[str]:
    if TW_BEARER:
        data=_twitter_v2_fetch(keyword, limit=limit)
        if data: return data
    return _twitter_snscrape_fetch(keyword, limit=limit)

# ---- YouTube API ----
YT_API_KEY = st.secrets.get("YOUTUBE_API_KEY", None)

def _yt_build():
    from googleapiclient.discovery import build
    return build("youtube", "v3", developerKey=YT_API_KEY, cache_discovery=False)

def _yt_list_search(service, q: str, max_results=5):
    return service.search().list(
        q=q, part="snippet", type="video", maxResults=max_results, order="date"
    ).execute()

def _yt_list_channel_uploads(service, channel_id: str, max_videos=20):
    ch=service.channels().list(part="contentDetails",id=channel_id).execute()
    items=ch.get("items",[])
    if not items: return []
    uploads=items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    videos=[]
    next_page=None
    while len(videos)<max_videos:
        resp=service.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads,
            maxResults=min(50,max_videos-len(videos)),
            pageToken=next_page
        ).execute()
        for it in resp.get("items",[]):
            videos.append({
                "videoId": it["contentDetails"]["videoId"],
                "videoTitle": it["snippet"]["title"]
            })
            if len(videos)>=max_videos: break
        next_page=resp.get("nextPageToken")
        if not next_page: break
    return videos

def _yt_video_stats(service, video_ids: List[str]) -> Dict[str,int]:
    stats={}
    for i in range(0,len(video_ids),50):
        chunk=video_ids[i:i+50]
        resp=service.videos().list(part="statistics",id=",".join(chunk)).execute()
        for it in resp.get("items",[]):
            stats[it["id"]]=int(it["statistics"].get("viewCount","0"))
    return stats

def _yt_comments_for_video(service, video_id: str, video_title: str, max_comments=200) -> List[Dict]:
    comments=[]
    page=None
    while len(comments)<max_comments:
        req=service.commentThreads().list(
            part="snippet", videoId=video_id,
            maxResults=min(100,max_comments-len(comments)),
            pageToken=page, textFormat="plainText", order="time"
        )
        resp=req.execute()
        for it in resp.get("items",[]):
            top=it["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "text": top.get("textDisplay",""),
                "videoId": video_id,
                "videoTitle": video_title
            })
            if len(comments)>=max_comments: break
        page=resp.get("nextPageToken")
        if not page: break
    return comments

def fetch_youtube_by_keyword(keyword: str, max_videos=5, max_comments_per_video=100) -> List[Dict]:
    if not YT_API_KEY: return []
    service=_yt_build()
    search=_yt_list_search(service, keyword, max_results=max_videos)
    videos=[{"videoId": it["id"]["videoId"],"videoTitle":it["snippet"]["title"]} for it in search.get("items",[])]
    all_comments=[]
    for v in videos:
        all_comments.extend(_yt_comments_for_video(service, v["videoId"], v["videoTitle"], max_comments=max_comments_per_video))
    return all_comments

def fetch_youtube_by_channel(channel_id: str, max_videos=20, max_comments_per_video=200) -> List[Dict]:
    if not YT_API_KEY: return []
    service=_yt_build()
    videos=_yt_list_channel_uploads(service, channel_id, max_videos=max_videos)
    stats=_yt_video_stats(service,[v["videoId"] for v in videos]) if videos else {}
    all_comments=[]
    for v in videos:
        comments=_yt_comments_for_video(service, v["videoId"], v["videoTitle"], max_comments=max_comments_per_video)
        for c in comments:
            c["viewCount"]=stats.get(v["videoId"],0)
        all_comments.extend(comments)
    return all_comments
