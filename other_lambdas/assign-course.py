import json
import boto3
import uuid
import os
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')

employees_table = dynamodb.Table(os.environ['EMPLOYEES_TABLE'])
assignments_table = dynamodb.Table(os.environ['ASSIGNMENTS_TABLE'])

ses = boto3.client('ses', region_name='ap-south-1')
SENDER = os.environ['SES_SENDER_EMAIL']


def lambda_handler(event, context):
    try:
        print("EVENT:", event)

        body = json.loads(event['body'])
        course_id = body['course_id']
        role = body['role']

        response = employees_table.scan()
        employees = response.get('Items', [])

        filtered_employees = [emp for emp in employees if emp.get('role') == role]

        due_date = (datetime.utcnow() + timedelta(days=7)).isoformat()

        for emp in filtered_employees:

            # Duplicate check
            existing = assignments_table.scan()
            already_assigned = False

            for item in existing.get('Items', []):
                if item['employee_id'] == emp['employee_id'] and item['course_id'] == course_id:
                    already_assigned = True
                    break

            if already_assigned:
                continue

            assignments_table.put_item(
                Item={
                    'assignment_id': str(uuid.uuid4()),
                    'employee_id': emp['employee_id'],
                    'course_id': course_id,
                    'due_date': due_date,
                    'status': 'not_started'
                }
            )

            # 🔥 Send Email
            if 'email' in emp:
                ses.send_email(
                    Source=SENDER,
                    Destination={'ToAddresses': [emp['email']]},
                    Message={
                        'Subject': {'Data': 'New Course Assigned'},
                        'Body': {
                            'Html': {
                                'Data': f"""
                                <p>Hi {emp.get('name','User')},</p>
                                <p>You have been assigned a new course.</p>
                                <p><b>Course ID:</b> {course_id}</p>
                                <p><b>Due Date:</b> {due_date}</p>
                                """
                            }
                        }
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
