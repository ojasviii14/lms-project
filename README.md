# LMS Project – Course Management Module (Member 1)

## Overview
This module handles course creation, retrieval, and assignment in a serverless Learning Management System (LMS) using AWS.

---

## Technologies Used
- AWS Lambda
- Amazon DynamoDB
- API Gateway

---

## APIs Implemented

### 1. Create Course
POST /courses  
Creates a new course and stores it in DynamoDB

---

### 2. Get Courses
GET /courses  
Fetches all available courses

---

### 3. Assign Course
POST /assign-course  
Assigns a course to employees based on role

---

## Database Tables

### courses
- course_id
- title
- description
- external_video_url
- passing_score
- assigned_roles

### employees
- employee_id
- name
- role
- department

### assignments
- assignment_id
- employee_id
- course_id
- status
- due_date

---

## Sample Output

GET /courses

{
  "courses": [
    {
      "course_id": "course1",
      "title": "Safety Training"
    }
  ]
}
