import jwt
import os
import time
import json
import boto3

JWT_SECRET = None 

def get_jwt_secret():
    global JWT_SECRET
    if JWT_SECRET: return JWT_SECRET
    
    secret_name = os.environ.get('SECRET_NAME')
    region_name = os.environ.get('AWS_REGION')
    client = boto3.client(service_name='secretsmanager', region_name=region_name)
    
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(get_secret_value_response['SecretString'])
        JWT_SECRET = secret['jwtSecretKey']
        return JWT_SECRET
    except Exception as e:
        raise e

def generate_token(event, context):
    try:
        jwt_secret = get_jwt_secret()
        payload = {'exp': int(time.time()) + 3600}
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': json.dumps({'token': token})
        }
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

def authorize(event, context):
    try:
        jwt_secret = get_jwt_secret()
        token = event['headers'].get('authorization', ' ').split(' ')[1]
        jwt.decode(token, jwt_secret, algorithms=['HS256'])
        return generate_policy('user', 'Allow', event['routeArn'])
    except Exception as e:
        return generate_policy('user', 'Deny', event['routeArn'])

def generate_policy(p, e, r):
    return {'principalId': p, 'policyDocument': {'Version': '2012-10-17', 'Statement': [{'Action': 'execute-api:Invoke', 'Effect': e, 'Resource': r}]}}