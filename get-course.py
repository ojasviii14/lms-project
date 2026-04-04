import json
import boto3
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('courses')

# Convert Decimal to int/float
def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj)  # convert Decimal to int
    else:
        return obj


def lambda_handler(event, context):
    try:
        # Fetch data from DynamoDB
        response = table.scan()
        items = response.get('Items', [])

        # Convert Decimal values
        items = convert_decimal(items)

        # Debug print (optional)
        print("COURSES:", items)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'courses': items
            })
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
