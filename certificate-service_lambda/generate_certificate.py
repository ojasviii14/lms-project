import json
import boto3
import uuid
import os
from datetime import datetime
from boto3.dynamodb.conditions import Attr
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
ses = boto3.client('ses', region_name='ap-south-1')
employees_table = dynamodb.Table(os.environ['EMPLOYEES_TABLE'])
courses_table = dynamodb.Table(os.environ['COURSES_TABLE'])
completions_table = dynamodb.Table(os.environ['COMPLETIONS_TABLE'])
certificates_table = dynamodb.Table(os.environ['CERTIFICATES_TABLE'])
BUCKET = os.environ['CERTIFICATE_BUCKET']
SENDER = os.environ['SES_SENDER_EMAIL']
CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': '*'
}
def send_email(to_email, name, course, url):
    ses.send_email(
        Source=SENDER,
        Destination={'ToAddresses': [to_email]},
        Message={
            'Subject': {'Data': f'Your Certificate for {course} is Ready!'},
            'Body': {
                'Html': {
                    'Data': f"""
                    <html><body>
                        <p>Hi {name},</p>
                        <p>Congratulations on completing <b>{course}</b>!</p>
                        <p><a href="{url}">Download Your Certificate</a></p>
                        <p><em>Link expires in 7 days.</em></p>
                        <p>Best regards,<br>F13 Technologies LMS</p>
                    </body></html>
                    """
                }
            }
        }
    )
def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        employee_id = body.get('employee_id')
        course_id = body.get('course_id') 
        if not employee_id or not course_id:
            return {'statusCode': 400, 'headers': CORS, 'body': json.dumps({'message': 'employee_id and course_id are required'})}
        emp = employees_table.get_item(Key={'employee_id': employee_id}).get('Item')
        course = courses_table.get_item(Key={'course_id': course_id}).get('Item')
        if not emp or not course:
            return {'statusCode': 404, 'headers': CORS, 'body': json.dumps({'message': 'Employee or course not found'})}
        status = completions_table.scan(
            FilterExpression=Attr('employee_id').eq(employee_id) &
                             Attr('course_id').eq(course_id) &
                             Attr('status').eq('pass')
        ) 
        if not status.get('Items'):
            return {'statusCode': 400, 'headers': CORS, 'body': json.dumps({'message': 'No passing completion found'})}
        cert_id = str(uuid.uuid4())
        completion_date = datetime.utcnow().strftime('%d %B %Y')
        sample_key = "certificates/sample/certificate.pdf"
        cert_key = f"certificates/{employee_id}/{course_id}.pdf"
        s3.copy_object(
            Bucket=BUCKET,
            CopySource={'Bucket': BUCKET, 'Key': sample_key},
            Key=cert_key
        )
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET, 'Key': cert_key, 'ResponseContentDisposition': 'attachment; filename=certificate.pdf'},
            ExpiresIn=604800
        )
        certificates_table.put_item(Item={
            'cert_id': cert_id,
            'employee_id': employee_id,
            'course_id': course_id,
            'employee_name': emp['name'],
            'course_name': course['title'],
            'completion_date': completion_date,
            's3_key': cert_key,
            'issued_at': datetime.utcnow().isoformat()
        })
        send_email(emp['email'], emp['name'], course['title'], url)
        return {
            'statusCode': 200,
            'headers': CORS,
            'body': json.dumps({'message': 'Certificate generated and emailed successfully', 'cert_id': cert_id, 'download_url': url})
        }
    except Exception as e:
        print("ERROR:", str(e))
        return {'statusCode': 500, 'headers': CORS, 'body': json.dumps({'error': str(e)})}