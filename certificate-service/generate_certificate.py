import json
import boto3
import uuid
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from io import BytesIO
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
ses_client = boto3.client('ses', region_name=os.environ['AWS_REGION_NAME'])
completions_table = dynamodb.Table(os.environ['COMPLETIONS_TABLE'])
certificates_table = dynamodb.Table(os.environ['CERTIFICATES_TABLE'])
employees_table = dynamodb.Table(os.environ['EMPLOYEES_TABLE'])
courses_table = dynamodb.Table(os.environ['COURSES_TABLE'])
BUCKET_NAME = os.environ['CERTIFICATE_BUCKET']
SES_SENDER = os.environ['SES_SENDER_EMAIL']
def get_employee(employee_id):
    response = employees_table.get_item(Key={'employee_id': employee_id})
    return response.get('Item')
def get_course(course_id):
    response = courses_table.get_item(Key={'course_id': course_id})
    return response.get('Item')
def generate_pdf(employee_name, course_name, completion_date, cert_id):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFillColor(colors.HexColor('#f0f4ff'))
    c.rect(0, 0, width, height, fill=True, stroke=False)
    c.setStrokeColor(colors.HexColor('#2563eb'))
    c.setLineWidth(4)
    c.rect(30, 30, width - 60, height - 60, fill=False, stroke=True)
    c.setLineWidth(1.5)
    c.rect(40, 40, width - 80, height - 80, fill=False, stroke=True)
    c.setFillColor(colors.HexColor('#1e3a8a'))
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width / 2, height - 130, "Certificate of Completion")
    c.setStrokeColor(colors.HexColor('#2563eb'))
    c.setLineWidth(1)
    c.line(100, height - 150, width - 100, height - 150)
    c.setFillColor(colors.HexColor('#374151'))
    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, height - 200, "This is to certify that")
    c.setFillColor(colors.HexColor('#1e3a8a'))
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, height - 250, employee_name)
    c.setFillColor(colors.HexColor('#374151'))
    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, height - 295, "has successfully completed the course")
    c.setFillColor(colors.HexColor('#2563eb'))
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2, height - 340, course_name)
    c.setFillColor(colors.HexColor('#374151'))
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 400, f"Date of Completion: {completion_date}")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor('#6b7280'))
    c.drawCentredString(width / 2, height - 430, f"Certificate ID: {cert_id}")
    c.setStrokeColor(colors.HexColor('#2563eb'))
    c.setLineWidth(1)
    c.line(100, 120, width - 100, 120)
    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(colors.HexColor('#374151'))
    c.drawCentredString(width / 2, 95, "F13 Technologies — Employee Learning & Skill Certification")
    c.save()
    buffer.seek(0)
    return buffer
def send_email(employee_email, employee_name, course_name, presigned_url):
    subject = f"Your Certificate for {course_name} is Ready!"
    body_html = f"""
    <html>
    <body>
        <p>Hi {employee_name},</p>
        <p>Congratulations on successfully completing <strong>{course_name}</strong>!</p>
        <p>Your certificate is ready. You can download it using the link below:</p>
        <p><a href="{presigned_url}">Download Certificate</a></p>
        <p><em>Note: This link expires in 7 days.</em></p>
        <br>
        <p>Best regards,<br>F13 Technologies LMS</p>
    </body>
    </html>
    """
    ses_client.send_email(
        Source=SES_SENDER,
        Destination={'ToAddresses': [employee_email]},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Html': {'Data': body_html}}
        }
    )
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
        employee = get_employee(employee_id)
        course = get_course(course_id)
        if not employee or not course:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'message': 'Employee or course not found'})
            }
        scan_response = completions_table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('employee_id').eq(employee_id) &
                             boto3.dynamodb.conditions.Attr('course_id').eq(course_id) &
                             boto3.dynamodb.conditions.Attr('result').eq('pass')
        )
        if not scan_response.get('Items', []):
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'message': 'No passing completion found for this employee and course'})
            }
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
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=604800
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
        send_email(
            employee_email=employee['email'],
            employee_name=employee['name'],
            course_name=course['title'],
            presigned_url=presigned_url
        )
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': json.dumps({
                'message': 'Certificate generated and emailed successfully',
                'cert_id': cert_id,
                'download_url': presigned_url
            })
        }
    except Exception as e:
        print("ERROR:", str(e))
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }