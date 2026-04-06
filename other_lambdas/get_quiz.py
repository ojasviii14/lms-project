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
        # Get course_id (optional now)
        course_id = (
            event.get('pathParameters', {}).get('course_id') or
            event.get('queryStringParameters', {}).get('course_id')
        )

        response = questions_table.scan()
        items = response.get('Items', [])

        while 'LastEvaluatedKey' in response:
            response = questions_table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))

        safe_questions = []

        for q in items:

            # ✅ Handle both question formats
            question_text = q.get('question_text') or q.get('question')

            # ❌ Skip if question is missing
            if not question_text:
                continue

            # ✅ Filter by course_id if provided
            if course_id and str(q.get('course_id')) != str(course_id):
                continue

            safe_questions.append({
                'question_id': q.get('question_id'),
                'course_id': q.get('course_id'),
                'question': question_text,
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
