import json, os, time, requests, random
import boto3
from botocore.exceptions import ClientError

# ... (get_secrets, ScraperError, caching functions bilkul same rahenge) ...
SECRETS = None
def get_secrets():
    global SECRETS
    if SECRETS: return SECRETS
    try:
        secret_name = "instagram-tool-secrets"
        client = boto3.client(service_name='secretsmanager', region_name=os.environ.get('AWS_REGION'))
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        SECRETS = json.loads(get_secret_value_response['SecretString'])
        return SECRETS
    except Exception as e:
        print(f"ERROR fetching secrets: {e}")
        raise e

dynamodb = boto3.resource('dynamodb')
class ScraperError(Exception): pass

# --- Caching ---
def get_from_cache(key, table):
    try:
        response = table.get_item(Key={'id': key})
        if 'Item' in response and response['Item']['ttl'] > int(time.time()): return json.loads(response['Item']['data'])
    except ClientError: pass
    return None

def set_in_cache(key, data, table, ttl_seconds):
    try:
        ttl = int(time.time()) + ttl_seconds
        table.put_item(Item={'id': key, 'data': json.dumps(data), 'ttl': ttl})
    except ClientError: pass

# --- Scraping Logic with better error handling ---
def call_scraping_api(url, params, api_name):
    print(f"Attempting to fetch from {api_name}...")
    try:
        response = requests.get(url, params=params, timeout=28)
        response.raise_for_status() # HTTP errors (4xx or 5xx) ke liye error raise karega
        
        # Check for empty or non-JSON response
        if not response.text:
            raise ScraperError(f"{api_name} returned an empty response.")
            
        return response.json()
    except requests.exceptions.JSONDecodeError:
        raise ScraperError(f"{api_name} returned a non-JSON response.")
    except requests.exceptions.RequestException as e:
        raise ScraperError(f"{api_name} request failed: {e}")


def fetch_fresh_data(target_url, secrets):
    time.sleep(random.uniform(0.5, 1.5))
    
    # Try 1: ScrapingBee Classic
    try:
        params_bee = {'api_key': secrets['scraperbeeApiKey'], 'url': target_url}
        return call_scraping_api('https://app.scrapingbee.com/api/v1', params_bee, "ScrapingBee Classic")
    except ScraperError as e:
        print(f"ScrapingBee Classic failed: {e}. Falling back...")

    # Try 2: ScrapingBee Premium (Final Backup)
    try:
        params_bee_premium = {'api_key': secrets['scraperbeeApiKey'], 'url': target_url, 'premium_proxy': 'true'}
        return call_scraping_api('https://app.scrapingbee.com/api/v1', params_bee_premium, "ScrapingBee Premium")
    except ScraperError as e:
        print(f"ScrapingBee Premium also failed: {e}")
        raise ScraperError("All scrapers failed to fetch the data.")


# --- Lambda Handlers ---
def get_instagram_profile(event, context):
    try:
        secrets = get_secrets()
        cache_table = dynamodb.Table(os.environ.get('CACHE_TABLE_NAME'))
        ttl = int(os.environ.get('CACHE_TTL_SECONDS'))
        username = event.get('queryStringParameters', {}).get('url')
        if not username: return {'statusCode': 400, 'body': json.dumps({'error': 'Username is required.'})}
        
        cached_data = get_from_cache(username, cache_table)
        if cached_data: return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps(cached_data)}
        
        profile_url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
        response_json = fetch_fresh_data(profile_url, secrets)
        data = response_json.get('graphql', {}).get('user', {})
        if not data or not data.get('username'): raise ScraperError("Valid user data not found.")
        
        formatted_data = {"data": {"avatar_url": data.get('profile_pic_url_hd'), "name": data.get('full_name'), "username": data.get('username'), "bio": data.get('biography'), "stats": {"posts": data.get('edge_owner_to_timeline_media', {}).get('count'), "followers": data.get('edge_followed_by', {}).get('count'), "following": data.get('edge_follow', {}).get('count')}}, "status": "ok"}
        
        set_in_cache(username, formatted_data, cache_table, ttl)
        return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps(formatted_data)}
    except ScraperError as e:
        return {'statusCode': 404, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': str(e)})}
    except Exception as e:
        print(f"FATAL Error in getProfile: {e}")
        return {'statusCode': 500, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'Internal server error.'})}

def get_content_data(event, context):