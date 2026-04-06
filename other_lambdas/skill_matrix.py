import json
import boto3
import os
from decimal import Decimal
from datetime import datetime  # 🔥 NEW

dynamodb = boto3.resource('dynamodb')

employees_table = dynamodb.Table(os.environ['EMPLOYEES_TABLE'])
courses_table = dynamodb.Table(os.environ['COURSES_TABLE'])
assignments_table = dynamodb.Table(os.environ['ASSIGNMENTS_TABLE'])
completions_table = dynamodb.Table(os.environ['COMPLETIONS_TABLE'])

CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': '*'
}

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError


def lambda_handler(event, context):
    try:
        employees = employees_table.scan().get('Items', [])
        courses = courses_table.scan().get('Items', [])
        assignments = assignments_table.scan().get('Items', [])
        completions = completions_table.scan().get('Items', [])

        # 🔥 NEW: current time
        now = datetime.utcnow()

        completion_map = {}
        for c in completions:
            emp_id = c['employee_id']
            crs_id = c['course_id']
            if emp_id not in completion_map:
                completion_map[emp_id] = {}

            existing = completion_map[emp_id].get(crs_id)
            if not existing or c['result'] == 'pass':
                completion_map[emp_id][crs_id] = c['result']

        # 🔥 UPDATED: store full assignment (not just course_id)
        assignment_map = {}
        for a in assignments:
            emp_id = a['employee_id']
            if emp_id not in assignment_map:
                assignment_map[emp_id] = []

            assignment_map[emp_id].append(a)  # 🔥 store full object

        matrix = []

        for emp in employees:
            emp_id = emp['employee_id']

            row = {
                'employee_id': emp_id,
                'name': emp['name'],
                'department': emp.get('department', 'N/A'),
                'courses': {}
            }

            for course in courses:
                crs_id = course['course_id']

                # 🔥 find assignment object
                emp_assignments = assignment_map.get(emp_id, [])
                assignment_obj = next(
                    (a for a in emp_assignments if a['course_id'] == crs_id),
                    None
                )

                assigned = assignment_obj is not None
                result = completion_map.get(emp_id, {}).get(crs_id)

                # 🔥 status logic (same as yours)
                if result == 'pass':
                    status = 'passed'
                elif result == 'fail':
                    status = 'failed'
                elif assigned:
                    status = 'in_progress'
                else:
                    status = 'not_started'

                # 🔥 NEW: overdue logic
                overdue = False
                if assignment_obj and 'due_date' in assignment_obj:
                    due = datetime.fromisoformat(assignment_obj['due_date'])
                    if status != 'passed' and due < now:
                        overdue = True

                row['courses'][crs_id] = {
                    'course_name': course['title'],
                    'status': status,
                    'overdue': overdue  # 🔥 NEW FIELD
                }

            matrix.append(row)

        # 🔥 Skill matrix (unchanged)
        dept_map = {}
        for emp in employees:
            dept = emp.get('department', 'Unknown')
            emp_id = emp['employee_id']

            if dept not in dept_map:
                dept_map[dept] = {'total': 0, 'passed': 0}

            dept_map[dept]['total'] += 1

            emp_completions = completion_map.get(emp_id, {})
            if any(v == 'pass' for v in emp_completions.values()):
                dept_map[dept]['passed'] += 1

        skill_matrix = []
        for dept, data in dept_map.items():
            pct = int((data['passed'] / data['total']) * 100) if data['total'] > 0 else 0

            skill_matrix.append({
                'department': dept,
                'total_employees': data['total'],
                'completed_mandatory': data['passed'],
                'completion_percentage': pct
            })

        return {
            'statusCode': 200,
            'headers': CORS,
            'body': json.dumps({
                'matrix': matrix,
                'courses': [{'course_id': c['course_id'], 'title': c['title']} for c in courses],
                'skill_matrix': skill_matrix
            }, default=decimal_default)
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            'statusCode': 500,
            'headers': CORS,
            'body': json.dumps({'error': str(e)})
        }
