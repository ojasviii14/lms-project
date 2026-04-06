import json
import boto3
import uuid
import os
from datetime import datetime
from boto3.dynamodb.conditions import Attr
from fpdf import FPDF
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
ses = boto3.client('ses', region_name=os.environ.get('AWS_REGION_NAME', 'ap-south-1'))
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
def create_certificate_pdf(emp_name, course_title, date, cert_id, filepath):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_line_width(2)
    pdf.rect(10, 10, 277, 190)
    pdf.set_line_width(0.5)
    pdf.rect(12, 12, 273, 186)
    pdf.set_y(40)
    pdf.set_font("Arial", "B", 28)
    pdf.set_text_color(30, 58, 138) # Dark blue
    pdf.cell(0, 15, "CERTIFICATE OF COMPLETION", ln=True, align="C")
    pdf.set_y(70)
    pdf.set_font("Arial", "", 16)
    pdf.set_text_color(75, 85, 99)
    pdf.cell(0, 10, "This is to certify that", ln=True, align="C")
    pdf.set_y(90)
    pdf.set_font("Arial", "B", 34)
    pdf.set_text_color(37, 99, 235) # Bright blue
    pdf.cell(0, 15, emp_name, ln=True, align="C")
    pdf.set_y(120)
    pdf.set_font("Arial", "", 16)
    pdf.set_text_color(75, 85, 99)
    pdf.cell(0, 10, "has successfully completed the requirements for", ln=True, align="C")
    pdf.set_y(135)
    pdf.set_font("Arial", "B", 22)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 15, course_title, ln=True, align="C")
    pdf.set_y(170)
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(138, 10, f"Date Issued: {date}", ln=False, align="C")
    pdf.cell(138, 10, f"Certificate ID: {cert_id}", ln=True, align="C")
    pdf.output(filepath)
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
                        <p><a href="{url}">Download Your Personalized Certificate</a></p>
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
            FilterExpression=Attr('employee_id').eq(employee_id) & Attr('course_id').eq(course_id)
        ) 
        items = status.get('Items', [])
        passed = any(i.get('result') == 'pass' or i.get('status') == 'pass' for i in items)
        if not passed:
            return {'statusCode': 400, 'headers': CORS, 'body': json.dumps({'message': 'No passing completion found'})}
        cert_id = str(uuid.uuid4())
        completion_date = datetime.utcnow().strftime('%d %B %Y')
        local_pdf_path = f"/tmp/{cert_id}.pdf"
        cert_key = f"certificates/{employee_id}/{course_id}.pdf"
        create_certificate_pdf(emp['name'], course['title'], completion_date, cert_id, local_pdf_path)
        s3.upload_file(
            local_pdf_path, 
            BUCKET, 
            cert_key,
            ExtraArgs={'ContentType': 'application/pdf'}
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
        if 'email' in emp:
            send_email(emp['email'], emp['name'], course['title'], url)
        return {
            'statusCode': 200,
            'headers': CORS,
            'body': json.dumps({'message': 'Certificate generated and emailed successfully', 'cert_id': cert_id, 'download_url': url})
        }
    except Exception as e:
        print("ERROR:", str(e))
        return {'statusCode': 500, 'headers': CORS, 'body': json.dumps({'error': str(e)})}