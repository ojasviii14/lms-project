import json
import boto3
import os
dynamodb = boto3.resource('dynamodb')
def lambda_handler(event, context):
    try:
        print("EVENT:", event)
        table_name = os.environ.get('CERTIFICATES_TABLE', 'certificates')
        certificates_table = dynamodb.Table(table_name)
        path_params = event.get('pathParameters') or {}
        cert_id = path_params.get('cert_id')

        if not cert_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'message': 'cert_id is required'})
            }
        response = certificates_table.get_item(Key={'cert_id': cert_id})
        cert = response.get('Item')
        if not cert:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'valid': False,
                    'message': 'Certificate not found. This certificate ID is invalid.'
                })
            }
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': json.dumps({
                'valid': True,
                'message': 'Certificate is valid',
                'certificate': {
                    'cert_id': cert['cert_id'],
                    'employee_name': cert.get('employee_name', 'Unknown'),
                    'course_name': cert.get('course_name', 'Unknown'),
                    'completion_date': cert.get('completion_date', 'Unknown')
                }
            })
        }
    except Exception as e:
        print("ERROR:", str(e))
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'message': f"Backend Error: {str(e)}"}) 
        }