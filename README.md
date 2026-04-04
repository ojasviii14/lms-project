📌 Project Title

Serverless Learning Management System (LMS) using AWS

🎯 Objective

To design and implement a scalable serverless LMS that enables course creation, assignment, tracking, and integration with other learning modules.

🧩 Module Implemented (Member 1)

Course Management & Assignment Module

🛠️ Technologies Used
AWS Lambda
Amazon API Gateway
Amazon DynamoDB
Python (Boto3)
HTML, CSS, JavaScript (Frontend)
🗄️ Database Design (DynamoDB Tables)
1. Courses Table
course_id (Primary Key)
title
description
external_video_url
passing_score
assigned_roles
2. Employees Table
employee_id (Primary Key)
name
email
role
department
3. Assignments Table
assignment_id (Primary Key)
employee_id
course_id
status
due_date
4. Completions Table
completion_id
employee_id
course_id
score
result
5. Questions Table
question_id
course_id
question
options
correct_answer (hashed)
🔗 APIs Implemented
1. Create Course
Endpoint: POST /courses
Function: Adds a new course to DynamoDB
2. Get Courses
Endpoint: GET /courses
Function: Retrieves all available courses
3. Assign Course (Role-Based)
Endpoint: POST /assign-course
Function: Assigns course to employees based on role
4. Assign Course (Individual)
Endpoint: POST /assign-course-individual
Function: Assigns course to a specific employee
🔄 System Workflow
Admin creates a course
Course is stored in DynamoDB
Admin assigns course (role/individual)
Employees are filtered
Assignments are created
Data stored in assignments table
🧪 Testing
APIs tested using Postman
DynamoDB data verified
End-to-end flow validated
💻 Frontend
Basic Admin Dashboard created using HTML, CSS, JavaScript
Features:
View courses
Assign courses
Interactive UI with dropdowns
