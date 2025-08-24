# visualize.py
from collections import Counter
from typing import List, Dict
import plotly.graph_objects as go
import pandas as pd

def _sent_counts(records: List[Dict]) -> Counter:
    return Counter([r["sent"] for r in records])

def plot_sentiment_pie(records: List[Dict]):
    cnt = _sent_counts(records)
    labels = ["Positive","Neutral","Negative"]
    values = [cnt.get("Positive",0), cnt.get("Neutral",0), cnt.get("Negative",0)]
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.35)])
    fig.update_layout(title="Sentiment Distribution")
    return fig

def plot_platform_bar(records: List[Dict]):
    # Compare total impact (views for YouTube, count for Twitter) per platform
    df = pd.DataFrame(records)
    if df.empty:
        return go.Figure()
    df["impact"] = df.apply(lambda x: x.get("viewCount", 1) if x["src"]=="YouTube" else 1, axis=1)
    platform_impact = df.groupby("src")["impact"].sum()
    fig = go.Figure()
    fig.add_bar(x=platform_impact.index, y=platform_impact.values, marker_color=['blue','orange'])
    fig.update_layout(title="Platform Comparison (Total Impact / Views)", xaxis_title="Platform", yaxis_title="Impact")
    return fig

def plot_top_items(records: List[Dict], top_n: int = 5):
    df = pd.DataFrame(records)
    if df.empty:
        return go.Figure()
    
    # Calculate impact per record
    df["impact"] = df.apply(lambda x: x.get("viewCount", 1) if x["src"]=="YouTube" else 1, axis=1)
    
    # Positive and negative separately
    pos = df[df["sent"]=="Positive"].copy()
    neg = df[df["sent"]=="Negative"].copy()
    
    # Sort by impact
    pos_top = pos.nlargest(top_n, "impact")[["src","videoTitle","clean","impact"]].fillna("")
    neg_top = neg.nlargest(top_n, "impact")[["src","videoTitle","clean","impact"]].fillna("")

    # Build x labels
    pos_labels = [f"{r.src}: {r.videoTitle}"[:40] if r.videoTitle else r.src for r in pos_top.itertuples()]
    neg_labels = [f"{r.src}: {r.videoTitle}"[:40] if r.videoTitle else r.src for r in neg_top.itertuples()]

    # Build y values (impact)
    pos_vals = list(pos_top["impact"])
    neg_vals = list(neg_top["impact"])

    # Create grouped bar chart
    fig = go.Figure()
    fig.add_bar(name="Top Positive", x=pos_labels, y=pos_vals, marker_color="green")
    fig.add_bar(name="Top Negative", x=neg_labels, y=neg_vals, marker_color="red")
    fig.update_layout(barmode="group", title="Top Positive & Negative Items (by Impact)", xaxis_title="", yaxis_title="Impact / Views")
    
    return fig
