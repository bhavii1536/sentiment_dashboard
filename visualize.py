from collections import Counter
from typing import List, Dict
import plotly.graph_objects as go
import pandas as pd

def plot_sentiment_pie(records: List[Dict]):
    cnt = Counter([r["sent"] for r in records])
    labels = ["Positive","Neutral","Negative"]
    values = [cnt.get("Positive",0), cnt.get("Neutral",0), cnt.get("Negative",0)]
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.35)])
    fig.update_layout(title="Sentiment Distribution")
    return fig

def plot_platform_bar(records: List[Dict]):
    df = pd.DataFrame(records)
    if df.empty: return go.Figure()
    views = df.groupby("src").size()  # Number of comments as proxy for engagement
    fig = go.Figure([go.Bar(x=views.index, y=views.values)])
    fig.update_layout(title="Platform Comparison", xaxis_title="Platform", yaxis_title="Number of Comments")
    return fig
