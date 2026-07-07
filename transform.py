import os 
import json
import pandas as pd
import boto3
from dotenv import load_dotenv

load_dotenv()


def download_from_s3(bucket_name, file_name, object_name=None):
    if object_name is None:
        object_name = f'raw/{file_name}'

    s3_client = boto3.client(
        's3', 
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY'), 
        region_name = os.getenv('AWS_REGION')
    )
    try:
        print(f"Tentativo di scaricamento da S3: s3://{bucket_name}/{object_name}")
        s3_client.download_file(bucket_name, object_name, file_name)
        print("Scaricamento completato con successo!")
        return True
    except Exception as e:
        print(f"Error during downloading on AWS: {e}")
        return False
    

def clean_youtube_data(local_file_name):
    with open(local_file_name, 'r', encoding = 'utf-8') as f:
        data = json.load(f)

    videos = data.get('items', [])
    df = pd.json_normalize(videos)
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
    df_clean = df[key_columns].copy()
    df_clean.columns = [
        'video_id',
        'published_at',
        'video_title', 
        'channel_name',
        'video_tags',
        'video_duration',
        'tot_views', 
        'tot_likes', 
        'tot_comments',
        'video_topic',
        'has_paid_product_placement'
    ]
    
    df_clean['published_at'] = pd.to_datetime(df_clean['published_at'], errors = 'coerce').fillna(pd.Timestamp('1900-01-01'))
    df_clean['tot_views'] = pd.to_numeric(df_clean['tot_views'], errors = 'coerce').fillna(0).astype(int)
    df_clean['tot_likes'] = pd.to_numeric(df_clean['tot_likes'], errors = 'coerce').fillna(0).astype(int)
    df_clean['tot_comments'] = pd.to_numeric(df_clean['tot_comments'], errors = 'coerce').fillna(0).astype(int)
    df_clean['publishing_hour'] = df_clean['published_at'].dt.hour
    df_clean['publishing_day'] = df_clean['published_at'].dt.day_name()
    df_clean['main_topic'] = df_clean['video_topic'].apply(lambda x: x[0].split('/')[-1].replace('_',' ') if isinstance(x, list) and len(x)>0 else 'Unknown')

    df_clean['engagement_rate'] = ((df_clean['tot_likes'] + df_clean['tot_comments']) / df_clean['tot_views'] * 100).fillna(0).round(2)
    df_clean['like_ratio'] = (df_clean['tot_likes'] / df_clean['tot_views'] * 100).fillna(0).round(2)
    df_clean['controversy_score'] = (df_clean['tot_comments'] / df_clean['tot_likes']).fillna(0).round(4)
    df_clean = df_clean.drop(columns=['published_at', 'video_topic'])
    return df_clean

def calculate_topic_metric(df):
    df = df.groupby('main_topic').agg(
        num_videos = ('video_id', 'count'),
        views_avg = ('tot_views', 'mean'),
        engagement_avg = ('engagement_rate', 'mean'),
        controversy_avg = ('controversy_score', 'mean')
    ).round(2).sort_values(by = 'num_videos')
    return df

def calculate_duration_engagement_correlation(df):
    timedeltas = pd.to_timedelta(df['video_duration'], errors = 'coerce').fillna(pd.Timedelta(seconds=0))
    df['duration_seconds'] = timedeltas.dt.total_seconds().astype(int)
    correlazione = df['duration_seconds'].corr(df['engagement_rate'])
    if abs(correlazione)<0.1:
        print(f"Correlazione pari a {correlazione}, non c'è correlazione lineare")
    if correlazione > 0:
        print(f"Correlazione pari a {correlazione}, è positiva, i video lunghi tendono ad avere più engagement.")
    else:
        print(f"Correlazione pari a {correlazione}, è negativa, i video corti tendono ad avere meno engagement.")
    return correlazione

def analyze_temporal_patterns(df):
    day_summary = df.groupby('publishing_day').agg(
        num_videos=('video_id', 'count'),
        views_avg=('tot_views', 'mean')
    ).reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']).round(2)
    print(day_summary)

    hour_summary = df.groupby('publishing_hour').size().reset_index(name='num_videos')
    hour_summary = hour_summary.sort_values(by='num_videos', ascending=False).head(5)
    print(hour_summary.to_string(index=False))
    

def upload_processed_data_to_s3(file_name, bucket_name, object_name=None):
    if object_name is None:
        object_name = file_name
    object_name = f"processed/{object_name}"
    
    s3_client = boto3.client(
        's3', 
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY'), 
        region_name = os.getenv('AWS_REGION')
    )
    try:
        print(f"Trying to upload on S3: s3://{bucket_name}/{object_name}")
        s3_client.upload_file(file_name, bucket_name, object_name)
        return True
    except Exception as e:
        print(f"Error during uploading processed data to AWS: {e}")
        return False





if __name__ == "__main__":
    name_bucket = "claudia-youtube-insight"
    local_file = "youtube_trending_data.json"
    clean_local_csv = "youtube_trending_clean.csv"
 

    if download_from_s3(name_bucket, local_file):
        
        df_clean = clean_youtube_data(local_file)
        print(df_clean.head(2))

        df_topics = calculate_topic_metric(df_clean)
        print(df_topics)
        calculate_duration_engagement_correlation(df_clean)
        analyze_temporal_patterns(df_clean)


        df_clean.to_csv("youtube_trending_clean.csv", index=False)
        
        if upload_processed_data_to_s3(clean_local_csv, name_bucket):
            if os.path.exists(clean_local_csv):
                os.remove(clean_local_csv)
        if os.path.exists(local_file):
            os.remove(local_file)