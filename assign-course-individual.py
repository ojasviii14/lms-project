import json
import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
assignments_table = dynamodb.Table('assignments')

def lambda_handler(event, context):
    try:
        print("EVENT:", event)

        body = json.loads(event.get('body', '{}'))
        
        employee_id = body.get('employee_id')
        course_id = body.get('course_id')

        if not employee_id or not course_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'employee_id and course_id are required'})
            }

        response = assignments_table.scan()
        for item in response.get('Items', []):
            if item['employee_id'] == employee_id and item['course_id'] == course_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'message': 'Already assigned'})
                }

        assignment_id = str(uuid.uuid4())

        assignments_table.put_item(
            Item={
                'assignment_id': assignment_id,
                'employee_id': employee_id,
                'course_id': course_id,
                'status': 'not_started',
                'due_date': datetime.utcnow().isoformat()
            }
        )

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': json.dumps({
                'message': 'Course assigned successfully',
                'assignment_id': assignment_id
            })
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
