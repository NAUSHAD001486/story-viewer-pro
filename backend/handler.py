import json, os, time, requests, random
import boto3
from botocore.exceptions import ClientError

# --- Common Functions ---
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

# --- Scraping Logic ---
def call_api(url, params, api_name):
    print(f"Attempting: {api_name}...")
    try:
        response = requests.get(url, params=params, timeout=28)
        response.raise_for_status()
        if not response.text: raise ScraperError("Empty response")
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ScraperError(f"Request failed: {e}")
    except json.JSONDecodeError:
        raise ScraperError("Non-JSON response")

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
        
        response_json = None
        try:
            # 1. Primary: ScrapingBee Classic
            params = {'api_key': secrets['scraperbeeApiKey'], 'url': f"https://www.instagram.com/{username}/?__a=1&__d=dis"}
            response_json = call_api('https://app.scrapingbee.com/api/v1', params, "ScrapingBee Classic")
        except ScraperError as e:
            print(f"ScrapingBee Classic failed: {e}. Falling back to Scrapingdog.")
            try:
                # 2. Backup: Scrapingdog
                params = {'api_key': secrets['scrapingdogApiKey'], 'username': username} # Yahan sirf username bhej rahe hain
                response_json = call_api("https://api.scrapingdog.com/instagram/profile", params, "Scrapingdog")
            except ScraperError as e2:
                print(f"Scrapingdog also failed: {e2}. Falling back to ScrapingBee Premium.")
                params = {'api_key': secrets['scraperbeeApiKey'], 'url': f"https://www.instagram.com/{username}/?__a=1&__d=dis", 'premium_proxy': 'true'}
                response_json = call_api('https://app.scrapingbee.com/api/v1', params, "ScrapingBee Premium")

        data = response_json.get('graphql', {}).get('user', {}) if 'graphql' in response_json else response_json
        if not data or not data.get('username'): raise ScraperError("Valid user data not found from any scraper.")
        
        formatted_data = {"data": {"avatar_url": data.get('profile_pic_url_hd'), "name": data.get('full_name'), "username": data.get('username'), "bio": data.get('biography'), "stats": {"posts": data.get('edge_owner_to_timeline_media', {}).get('count'), "followers": data.get('edge_followed_by', {}).get('count'), "following": data.get('edge_follow', {}).get('count')}}, "status": "ok"}
        set_in_cache(username, formatted_data, cache_table, ttl)
        return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps(formatted_data)}
    except ScraperError as e:
        return {'statusCode': 404, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': str(e)})}
    except Exception as e:
        print(f"FATAL Error in getProfile: {e}")
        return {'statusCode': 500, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'Internal server error.'})}

def get_content_data(event, context):
    try:
        secrets = get_secrets()
        content_url = event.get('queryStringParameters', {}).get('url')
        if not content_url: return {'statusCode': 400, 'body': json.dumps({'error': 'Content URL is required.'})}
        
        # Content ke liye, hum sirf ScrapingBee ka istemal karenge kyunki Scrapingdog ko User ID chahiye
        try:
            params = {'api_key': secrets['scraperbeeApiKey'], 'url': f"{content_url}?__a=1&__d=dis"}
            response_json = call_api('https://app.scrapingbee.com/api/v1', params, "ScrapingBee Classic")
        except ScraperError as e:
            print(f"ScrapingBee Classic failed: {e}. Falling back to Premium.")
            params = {'api_key': secrets['scraperbeeApiKey'], 'url': f"{content_url}?__a=1&__d=dis", 'premium_proxy': 'true'}
            response_json = call_api('https://app.scrapingbee.com/api/v1', params, "ScrapingBee Premium")

        shortcode_media = response_json.get('graphql', {}).get('shortcode_media', {})
        if not shortcode_media: raise ScraperError("Content data not found.")
        
        formatted_data = {"data": {"media_type": "video" if shortcode_media.get('is_video') else "image", "media_url": shortcode_media.get('video_url') or shortcode_media.get('display_url'), "thumbnail_url": shortcode_media.get('display_url'), "caption": shortcode_media.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node',{}).get('text', ''), "author": { "username": shortcode_media.get('owner', {}).get('username'), "avatar_url": shortcode_media.get('owner', {}).get('profile_pic_url')}}, "status": "ok"}
        return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps(formatted_data)}
    except ScraperError as e:
        return {'statusCode': 404, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': str(e)})}
    except Exception as e:
        print(f"FATAL Error in getContent: {e}")
        return {'statusCode': 500, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'Internal server error.'})}
