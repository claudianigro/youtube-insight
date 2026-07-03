import json
import pandas as pd

with open("youtube_trending_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.json_normalize(data["items"])
print(df.columns.to_list())
key_columns = [
    'id',
    'snippet.publishedAt',
    'snippet.title', 
    'snippet.channelTitle',
    'snippet.tags',
    'contentDetails.duration', 
    'statistics.viewCount', 
    'statistics.likeCount', 
    'statistics.commentCount',
    'topicDetails.topicCategories', 
    'paidProductPlacementDetails.hasPaidProductPlacement'
]
df_clean = df[key_columns]
df_clean.to_html("tabella.html")