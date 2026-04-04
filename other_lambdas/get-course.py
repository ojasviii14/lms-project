import json
import boto3
import os
from decimal import Decimal
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['COURSES_TABLE'])
def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj)
    else:
        return obj
def lambda_handler(event, context):
    try:
        response = table.scan()
        items = response.get('Items', [])
        items = convert_decimal(items)
        print("COURSES:", items)
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': json.dumps({'courses': items})
        }
    except Exception as e:
        print("ERROR:", str(e))
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }