import json
import boto3
dynamodb = boto3.resource('dynamodb')
certificates_table = dynamodb.Table('certificates')
def lambda_handler(event, context):
    try:
        print("EVENT:", event)
        cert_id = event['pathParameters']['cert_id']
        response = certificates_table.get_item(Key={'cert_id': cert_id})
        cert = response.get('Item')

        if not cert:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'valid': False,
                    'message': 'Certificate not found'
                })
            }
        return {
            'statusCode': 200,
            'body': json.dumps({
                'valid': True,
                'certificate': dict(cert)
            })
        }
    except Exception as e:
        print("ERROR:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }