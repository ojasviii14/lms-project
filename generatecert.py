import json
import boto3
import uuid
from datetime import datetime
from reportlab.pdfgen import canvas
from io import BytesIO
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
ses_client = boto3.client('ses')
completions_table = dynamodb.Table('completions')
certificates_table = dynamodb.Table('certificates')
employees_table = dynamodb.Table('employees')
courses_table = dynamodb.Table('courses')
BUCKET_NAME = 'lms-certificates-bucket'
SES_SENDER = 'admin@example.com'
def get_employee(employee_id):
    response = employees_table.get_item(Key={'employee_id': employee_id})
    return response.get('Item')
def get_course(course_id):
    response = courses_table.get_item(Key={'course_id': course_id})
    return response.get('Item')
def generate_pdf(employee_name, course_name, completion_date, cert_id):
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "Certificate of Completion")
    c.drawString(100, 700, f"Name: {employee_name}")
    c.drawString(100, 680, f"Course: {course_name}")
    c.drawString(100, 660, f"Date: {completion_date}")
    c.drawString(100, 640, f"Cert ID: {cert_id}")
    c.save()
    buffer.seek(0)
    return buffer
def lambda_handler(event, context):
    try:
        print("EVENT:", event)
        body = json.loads(event.get('body', '{}'))
        employee_id = body.get('employee_id')
        course_id = body.get('course_id')
        employee = get_employee(employee_id)
        course = get_course(course_id)
        cert_id = str(uuid.uuid4())
        completion_date = datetime.utcnow().strftime('%B %d, %Y')

        pdf_buffer = generate_pdf(
            employee_name=employee['name'],
            course_name=course['title'],
            completion_date=completion_date,
            cert_id=cert_id
        )
        s3_key = f"certificates/{employee_id}/{course_id}.pdf"
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=pdf_buffer.read(),
            ContentType='application/pdf'
        )
        certificates_table.put_item(
            Item={
                'cert_id': cert_id,
                'employee_id': employee_id,
                'course_id': course_id,
                'employee_name': employee['name'],
                'course_name': course['title'],
                'completion_date': completion_date,
                's3_key': s3_key,
                'issued_at': datetime.utcnow().isoformat()
            }
        )
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Certificate generated',
                'cert_id': cert_id,
                's3_key': s3_key
            })
        }
    except Exception as e:
        print("ERROR:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }