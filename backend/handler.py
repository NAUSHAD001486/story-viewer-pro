import json
import os
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
import boto3

SECRETS = None

def get_secrets():
    global SECRETS
    if SECRETS: return SECRETS
    
    secret_name = os.environ.get('SECRET_NAME', "instagram-tool-secrets")
    region_name = os.environ.get('AWS_REGION', "ap-south-1")
    client = boto3.client(service_name='secretsmanager', region_name=region_name)
    
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        SECRETS = json.loads(get_secret_value_response['SecretString'])
        return SECRETS
    except Exception as e:
        raise e

dynamodb = boto3.resource('dynamodb')
CACHE_TABLE_NAME = os.environ.get('CACHE_TABLE_NAME')
CACHE_TTL_SECONDS = int(os.environ.get('CACHE_TTL_SECONDS', 1500))
cache_table = dynamodb.Table(CACHE_TABLE_NAME)

class ScraperError(Exception): pass

def get_profile_from_cache(username):
    try:
        r = cache_table.get_item(Key={'username': username})
        if 'Item' in r and r['Item']['ttl'] > int(time.time()): return json.loads(r['Item']['data'])
    except Exception: pass
    return None

def set_profile_in_cache(username, data):
    try:
        ttl = int(time.time()) + CACHE_TTL_SECONDS
        cache_table.put_item(Item={'username': username, 'data': json.dumps(data), 'ttl': ttl})
    except Exception: pass

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
def call_primary_scraper(profile_url, api_key):
    if not api_key: raise ScraperError("ScraperAPI key nahi hai.")
    api_url = f'http://api.scraperapi.com?api_key={api_key}&url={profile_url}'
    response = requests.get(api_url, timeout=25)
    if response.status_code != 200:
        raise ScraperError("ScraperAPI se data nahi mila.")
    print("ScraperAPI safal raha (lekin abhi sample data bhej rahe hain).")
    username = profile_url.split(".com/")[-1].replace('/', '')
    return { "data": { "avatar_url": "https://images.pexels.com/photos/220453/pexels-photo-220453.jpeg", "name": f"{username}", "username": username, "bio": "Yeh ek safal response hai ScraperAPI se.", "stats": { "posts": 123, "followers": 456, "following": 789}}, "status": "ok"}

def call_backup_scraper(profile_url, api_key):
    if not api_key: raise ScraperError("Scrapingdog API key nahi hai.")
    api_url = f'https://api.scrapingdog.com/scrape?api_key={api_key}&url={profile_url}'
    response = requests.get(api_url, timeout=25)
    if response.status_code != 200:
        raise ScraperError("Scrapingdog se data nahi mila.")
    print("Scrapingdog safal raha (lekin abhi sample data bhej rahe hain).")
    username = profile_url.split(".com/")[-1].replace('/', '')
    return { "data": { "avatar_url": "https://images.pexels.com/photos/220453/pexels-photo-220453.jpeg", "name": f"{username}", "username": username, "bio": "Yeh ek safal response hai Scrapingdog se.", "stats": { "posts": 123, "followers": 456, "following": 789}}, "status": "ok"}

def fetch_fresh_data(profile_url, secrets):
    try:
        return call_primary_scraper(profile_url, secrets['scraperApiKey'])
    except RetryError:
        return call_backup_scraper(profile_url, secrets['scrapingdogApiKey'])

def get_instagram_profile(event, context):
    try:
        secrets = get_secrets()
        profile_url_input = event.get('queryStringParameters', {}).get('url')
        if not profile_url_input: return {'statusCode': 400, 'headers': {'Access-Control-Allow-Origin': '*'},'body': json.dumps({'error': 'URL/username is required.'})}
        
        username = profile_url_input.split("?")[0]
        
        profile_url = f"https://www.instagram.com/{username}/"
        cached_data = get_profile_from_cache(username)
        if cached_data: return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps(cached_data)}
        
        fresh_data = fetch_fresh_data(profile_url, secrets)
        set_profile_in_cache(username, fresh_data)
        return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps(fresh_data)}
    except Exception as e:
        return {'statusCode': 500, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': f'An error occurred: {str(e)}'})}