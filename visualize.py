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
    # platform wise total + positive rate
    df = pd.DataFrame(records)
    if df.empty:
        return go.Figure()
    by_src = df.groupby(["src","sent"]).size().unstack(fill_value=0)
    by_src = by_src[["Positive","Neutral","Negative"]] if set(["Positive","Neutral","Negative"]).issubset(by_src.columns) else by_src
    fig = go.Figure()
    for col in by_src.columns:
        fig.add_bar(name=col, x=by_src.index, y=by_src[col])
    fig.update_layout(barmode="stack", title="Platform Comparison", xaxis_title="Platform", yaxis_title="Count")
    return fig

def plot_top_items(records: List[Dict], top_n: int = 5):
    # pick top positive & negative examples (simple heuristic: length as proxy)
    df = pd.DataFrame(records)
    if df.empty:
        return go.Figure()
    pos = df[df["sent"]=="Positive"].copy()
    neg = df[df["sent"]=="Negative"].copy()
    pos["score"] = pos["clean"].str.len()
    neg["score"] = neg["clean"].str.len()
    pos_top = pos.nlargest(top_n, "score")[["src","videoTitle","clean"]].fillna("")
    neg_top = neg.nlargest(top_n, "score")[["src","videoTitle","clean"]].fillna("")

    # build tables as one figure with two bar traces of counts (fallback)
    labels = [f"{r.src}: {r.videoTitle}"[:40] if r.videoTitle else r.src for r in pos_top.itertuples()]
    labels = labels + [f"{r.src}: {r.videoTitle}"[:40] if r.videoTitle else r.src for r in neg_top.itertuples()]
    kinds  = ["Top Positive"]*len(pos_top) + ["Top Negative"]*len(neg_top)
    vals   = [len(txt) for txt in list(pos_top["clean"]) + list(neg_top["clean"])]
    fig = go.Figure()
    fig.add_bar(name="Top Positive", x=labels[:len(pos_top)], y=vals[:len(pos_top)])
    fig.add_bar(name="Top Negative", x=labels[len(pos_top):], y=vals[len(pos_top):])
    fig.update_layout(barmode="group", title="Top Items (proxy by text length)", xaxis_title="", yaxis_title="Text length")
    return fig
