import json
import boto3
import uuid
import os
from datetime import datetime
dynamodb = boto3.resource('dynamodb')
employees_table = dynamodb.Table(os.environ['EMPLOYEES_TABLE'])
assignments_table = dynamodb.Table(os.environ['ASSIGNMENTS_TABLE'])
def lambda_handler(event, context):
    try:
        print("EVENT:", event)
        body = json.loads(event['body'])
        print("BODY:", body)
        course_id = body['course_id']
        role = body['role']
        response = employees_table.scan()
        employees = response.get('Items', [])
        filtered_employees = [emp for emp in employees if emp.get('role') == role]
        for emp in filtered_employees:
            assignments_table.put_item(
                Item={
                    'assignment_id': str(uuid.uuid4()),
                    'employee_id': emp['employee_id'],
                    'course_id': course_id,
                    'due_date': datetime.utcnow().isoformat(),
                    'status': 'not_started'
                }
            )
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': json.dumps({'message': 'Course assigned successfully'})
        }
    except Exception as e:
        print("ERROR:", str(e))
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }