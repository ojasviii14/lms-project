import json
import boto3
import uuid
import os
dynamodb = boto3.resource('dynamodb')
courses_table = dynamodb.Table(os.environ['COURSES_TABLE'])
def lambda_handler(event, context):
    try:
        print("EVENT:", event)
        body = json.loads(event['body'])
        print("BODY:", body)

        item = {
            'course_id': str(uuid.uuid4()),
            'title': body['title'],
            'description': body['description'],
            'external_video_url': body['external_video_url'],
            'passing_score': body['passing_score'],
            'assigned_roles': body['assigned_roles']
        }
        courses_table.put_item(Item=item)
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': json.dumps({'message': 'Course created', 'course_id': item['course_id']})
        }
    except Exception as e:
        print("ERROR:", str(e))
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }