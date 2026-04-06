import json
import boto3
import os
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb')
questions_table = dynamodb.Table(os.environ['QUESTIONS_TABLE']) 

CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': '*'
}

def lambda_handler(event, context):
    try:
        course_id = (
            event.get('pathParameters', {}).get('course_id') or
            event.get('queryStringParameters', {}).get('course_id')
        )

        if not course_id:
            return {
                'statusCode': 400,
                'headers': CORS,
                'body': json.dumps({'message': 'course_id is required'})
            }

        course_id = str(course_id)

        response = questions_table.scan(
            FilterExpression=Attr('course_id').eq(course_id)
        )

        items = response.get('Items', [])

        while 'LastEvaluatedKey' in response:
            response = questions_table.scan(
                FilterExpression=Attr('course_id').eq(course_id),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))

        safe_questions = []
        for q in items:
            safe_questions.append({
                'question_id': q.get('question_id'),
                'question': q.get('question'),
                'options': q.get('options', [])
            })

        return {
            'statusCode': 200,
            'headers': CORS,
            'body': json.dumps({'questions': safe_questions})
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            'statusCode': 500,
            'headers': CORS,
            'body': json.dumps({'error': str(e)})
        }
