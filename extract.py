import os
import json
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    raise ValueError("No YOUTUBE_API_KEY found.")

def get_trending_videos(region_code, max_results):
    youtube = build("youtube", "v3", developerKey=API_KEY)
    request = youtube.videos().list(
        part= "snippet, statistics, contentDetails, paidProductPlacementDetails, topicDetails",
        chart = "mostPopular", 
        regionCode = region_code, 
        maxResults = max_results
    )
    response = request.execute()
    return response


if __name__ == "__main__":
    try:
        raw_data = get_trending_videos("IT", 100)
        output_file = "youtube_trending_data.json"
        with open(output_file, "w") as f:
            json.dump(raw_data, f, ensure_ascii = False, indent = 4)
    except Exception as e:
        print(f"Problem during the extraction. {e}")
        