import json
import boto3
import uuid
import os
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
assignments_table = dynamodb.Table('assignments')
employees_table = dynamodb.Table(os.environ['EMPLOYEES_TABLE'])

ses = boto3.client('ses', region_name='ap-south-1')
SENDER = os.environ['SES_SENDER_EMAIL']


def lambda_handler(event, context):
    try:
        print("EVENT:", event)

        body = json.loads(event.get('body', '{}'))
        employee_id = body.get('employee_id')
        course_id = body.get('course_id')

        if not employee_id or not course_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'message': 'employee_id and course_id are required'})
            }

        # Check duplicate (kept your logic)
        response = assignments_table.scan()
        for item in response.get('Items', []):
            if item['employee_id'] == employee_id and item['course_id'] == course_id:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'message': 'Already assigned'})
                }

        assignment_id = str(uuid.uuid4())

        # FIX: due date = +7 days
        due_date = (datetime.utcnow() + timedelta(days=7)).isoformat()

        assignments_table.put_item(
            Item={
                'assignment_id': assignment_id,
                'employee_id': employee_id,
                'course_id': course_id,
                'status': 'not_started',
                'due_date': due_date
            }
        )

        # 🔥 NEW: Send Email
        emp = employees_table.get_item(Key={'employee_id': employee_id}).get('Item')

        if emp and 'email' in emp:
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
            'body': json.dumps({
                'message': 'Course assigned successfully',
                'assignment_id': assignment_id
            })
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
