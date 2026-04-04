import json
import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')

employees_table = dynamodb.Table('employees')
assignments_table = dynamodb.Table('assignments')


def lambda_handler(event, context):
    try:
        print("EVENT:", event)  # 👈 DEBUG

        body = json.loads(event['body'])
        print("BODY:", body)  # 👈 DEBUG

        course_id = body['course_id']
        role = body['role']

        response = employees_table.scan()
        employees = response.get('Items', [])
        print("EMPLOYEES:", employees)  # 👈 DEBUG

        filtered_employees = [emp for emp in employees if emp.get('role') == role]
        print("FILTERED:", filtered_employees)  # 👈 DEBUG

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
            'body': json.dumps({'message': 'Course assigned successfully'})
        }

    except Exception as e:
        print("ERROR:", str(e))  # 👈 DEBUG
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
