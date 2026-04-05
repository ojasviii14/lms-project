import json
import boto3
import uuid
import os
import hashlib
from datetime import datetime
from boto3.dynamodb.conditions import Attr
from decimal import Decimal  
dynamodb = boto3.resource('dynamodb') 
questions_table = dynamodb.Table(os.environ['QUESTIONS_TABLE'])
completions_table = dynamodb.Table(os.environ['COMPLETIONS_TABLE'])
assignments_table = dynamodb.Table(os.environ['ASSIGNMENTS_TABLE'])
courses_table = dynamodb.Table(os.environ['COURSES_TABLE']) 
CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': '*'
} 
MAX_ATTEMPTS = 3 
def hash_answer(answer):
    return hashlib.sha256(answer.strip().lower().encode()).hexdigest()
def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        employee_id = body.get('employee_id')
        course_id = body.get('course_id')
        answers = body.get('answers', {})  # {question_id: selected_answer}
 
        if not employee_id or not course_id or not answers:
            return {'statusCode': 400, 'headers': CORS, 'body': json.dumps({'message': 'employee_id, course_id and answers are required'})}
        existing = completions_table.scan(
            FilterExpression=Attr('employee_id').eq(employee_id) & Attr('course_id').eq(course_id)
        )
        attempts = len(existing.get('Items', []))
        if attempts >= MAX_ATTEMPTS:
            return {'statusCode': 400, 'headers': CORS, 'body': json.dumps({'message': f'Maximum {MAX_ATTEMPTS} attempts reached'})}
        questions = questions_table.scan(
            FilterExpression=Attr('course_id').eq(course_id)
        ).get('Items', [])
        if not questions:
            return {'statusCode': 404, 'headers': CORS, 'body': json.dumps({'message': 'No questions found for this course'})}
        correct = 0
        for q in questions:
            question_id = q['question_id']
            submitted = answers.get(question_id, '')
            hashed_submitted = hash_answer(submitted)
            if hashed_submitted == q['correct_answer']:
                correct += 1
        total = len(questions)
        score = int((correct / total) * 100)
        course = courses_table.get_item(Key={'course_id': course_id}).get('Item')
        passing_score = int(course.get('passing_score', 70)) if course else 70
        result = 'pass' if score >= passing_score else 'fail'
        completion_id = str(uuid.uuid4())
        completions_table.put_item(Item={
            'completion_id': completion_id,
            'employee_id': employee_id,
            'course_id': course_id,
            'score': Decimal(str(score)),
            'result': result,
            'attempt': attempts + 1,
            'submitted_at': datetime.utcnow().isoformat()
        })
        assignment_scan = assignments_table.scan(
            FilterExpression=Attr('employee_id').eq(employee_id) & Attr('course_id').eq(course_id)
        )
        for item in assignment_scan.get('Items', []):
            assignments_table.update_item(
                Key={'assignment_id': item['assignment_id']},
                UpdateExpression='SET #s = :s',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':s': 'passed' if result == 'pass' else 'failed'}
            )
        return {
            'statusCode': 200,
            'headers': CORS,
            'body': json.dumps({
                'message': f'Quiz submitted. You {"passed" if result == "pass" else "failed"}!',
                'score': score,
                'result': result,
                'correct': correct,
                'total': total,
                'attempts_remaining': MAX_ATTEMPTS - (attempts + 1),
                'completion_id': completion_id
            })
        }
    except Exception as e:
        print("ERROR:", str(e))
        return {'statusCode': 500, 'headers': CORS, 'body': json.dumps({'error': str(e)})}