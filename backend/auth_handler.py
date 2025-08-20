# backend/auth_handler.py
import jwt, os, time, json, boto3

JWT_SECRET = None
def get_jwt_secret():
    global JWT_SECRET
    if JWT_SECRET: return JWT_SECRET
    secret_name = "instagram-tool-secrets"
    region_name = os.environ.get('AWS_REGION')
    # Badlav yahan hai
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(get_secret_value_response['SecretString'])
        JWT_SECRET = secret['jwtSecretKey']
        print("JWT Secret successfully fetched.")
        return JWT_SECRET
    except Exception as e:
        print(f"Error fetching JWT secret: {e}")
        raise e

# Baaki saara code (generate_token, authorize, generate_policy) bilkul same rahega
# ...
def generate_token(event, context):
    try:
        jwt_secret = get_jwt_secret()
        payload = {'exp': int(time.time()) + 3600}
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'token': token})}
    except Exception as e:
        print(f"ERROR in generate_token: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Could not generate token.'})}

def authorize(event, context):
    try:
        jwt_secret = get_jwt_secret()
        token = event['headers'].get('authorization', '').split(' ')[-1]
        jwt.decode(token, jwt_secret, algorithms=['HS256'])
        return generate_policy('user', 'Allow', event['routeArn'])
    except Exception as e:
        print(f"Authorization error: {e}")
        return generate_policy('user', 'Deny', event['routeArn'])

def generate_policy(principal_id, effect, resource):
    return {'principalId': principal_id, 'policyDocument': {'Version': '2012-10-17', 'Statement': [{'Action': 'execute-api:Invoke', 'Effect': effect, 'Resource': resource}]}}