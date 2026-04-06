const BASE_URL = "https://xk25uvcuf3.execute-api.ap-south-1.amazonaws.com";

let courses = [];
let quizData = [];
let currentQuizCourse = '';
let currentQuizEmployee = '';

function show(section) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById(section).classList.add('active');
}

function setMsg(id, text, isError = false) {
    const el = document.getElementById(id);
    el.innerText = text;
    el.className = 'msg ' + (isError ? 'error' : 'success');
}

// ---------------- COURSES ----------------
async function getCourses() {
    try {
        const res = await fetch(BASE_URL + "/courses");
        const result = await res.json();

        courses = result.courses || [];

        const list = document.getElementById("courseList");
        list.innerHTML = "";

        if (!courses.length) {
            list.innerHTML = "<li>No courses found.</li>";
            return;
        }

        courses.forEach(c => {
            list.innerHTML += `
                <li>
                    <strong>${c.title}</strong> (${c.course_id})<br>
                    <small style="color:#6b7280">${c.description} | Passing Score: ${c.passing_score}</small>
                </li>`;
        });

    } catch (err) {
        console.error("Error loading courses:", err);
    }
}

// ---------------- LOAD FOR ASSIGN ----------------
async function loadCoursesForAssign() {
    try {
        const res = await fetch(BASE_URL + "/courses");
        const result = await res.json();

        courses = result.courses || [];

        const dropdown = document.getElementById("courseDropdown");
        dropdown.innerHTML = "";

        courses.forEach(c => {
            dropdown.innerHTML += `<option value="${c.course_id}">${c.title}</option>`;
        });

    } catch (err) {
        console.error("Error loading courses for assign:", err);
    }
}

// ---------------- CREATE COURSE ----------------
async function createCourse() {
    try {
        const data = {
            title: document.getElementById("title").value,
            description: document.getElementById("description").value,
            external_video_url: document.getElementById("video_url").value,
            passing_score: parseInt(document.getElementById("passing_score").value),
            assigned_roles: document.getElementById("assigned_roles").value.split(",").map(r => r.trim())
        };

        const res = await fetch(BASE_URL + "/courses", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await res.json();
        setMsg('createMsg', result.message || "Course created!");

    } catch (err) {
        setMsg('createMsg', "Error creating course.", true);
    }
}

// ---------------- ASSIGN ----------------
async function assign() {
    try {
        const data = {
            course_id: document.getElementById("courseDropdown").value,
            employee_id: document.getElementById("employee_id").value
        };

        const res = await fetch(BASE_URL + "/assign-course-individual", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await res.json();
        setMsg('assignMsg', result.message || "Assigned!");

    } catch (err) {
        setMsg('assignMsg', "Error assigning course.", true);
    }
}

// ---------------- QUIZ ----------------
async function loadQuiz() {
    try {
        currentQuizCourse = document.getElementById("quizCourseId").value;
        currentQuizEmployee = document.getElementById("quizEmployeeId").value;

        if (!currentQuizCourse || !currentQuizEmployee) {
            alert("Please enter both Course ID and Employee ID");
            return;
        }

        const res = await fetch(BASE_URL + "/quiz/" + currentQuizCourse);
        const result = await res.json();

        quizData = result.questions || [];

        const container = document.getElementById("quizQuestions");
        container.innerHTML = "";

        if (!quizData.length) {
            container.innerHTML = "<p style='color:#dc2626'>No questions found for this course.</p>";
            return;
        }

        quizData.forEach((q, i) => {
            let optionsHtml = q.options.map(opt => `
                <label class="quiz-option">
                    <input type="radio" name="q_${q.question_id}" value="${opt.charAt(0).toLowerCase()}" />
                    ${opt}
                </label>`).join('');

            container.innerHTML += `
                <div class="question-block">
                    <p>Q${i + 1}. ${q.question}</p>
                    ${optionsHtml}
                </div>`;
        });

        document.getElementById("submitQuizBtn").style.display = "block";
        setMsg('quizMsg', '');

    } catch (err) {
        console.error(err);
        setMsg('quizMsg', "Error loading quiz.", true);
    }
}

// ---------------- SUBMIT QUIZ ----------------
async function submitQuiz() {
    try {
        const answers = {};

        quizData.forEach(q => {
            const selected = document.querySelector(`input[name="q_${q.question_id}"]:checked`);
            if (selected) answers[q.question_id] = selected.value;
        });

        if (Object.keys(answers).length < quizData.length) {
            setMsg('quizMsg', "Please answer all questions before submitting.", true);
            return;
        }

        const data = {
            employee_id: currentQuizEmployee,
            course_id: currentQuizCourse,
            answers
        };

        const res = await fetch(BASE_URL + "/submit-quiz", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await res.json();

        const isPass = result.result === 'pass';

        setMsg(
            'quizMsg',
            `${result.message} | Score: ${result.score}% | Attempts remaining: ${result.attempts_remaining}`,
            !isPass
        );

    } catch (err) {
        setMsg('quizMsg', "Error submitting quiz.", true);
    }
}

// ---------------- CERTIFICATE ----------------
async function generateCert() {
    try {
        const data = {
            employee_id: document.getElementById("certEmployeeId").value,
            course_id: document.getElementById("certCourseId").value
        };

        setMsg('certMsg', "Generating certificate...");

        const res = await fetch(BASE_URL + "/generate-certificate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await res.json();

        if (result.download_url) {
            setMsg('certMsg', `✅ Certificate generated! Cert ID: ${result.cert_id}`);

            const link = document.getElementById("certLink");
            link.href = result.download_url;
            link.style.display = "block";

        } else {
            setMsg('certMsg', result.message || result.error, true);
        }

    } catch (err) {
        setMsg('certMsg', "Error generating certificate.", true);
    }
}

// ---------------- VERIFY ----------------
async function verifyCert() {
    try {
        const cert_id = document.getElementById("certId").value;

        if (!cert_id) {
            alert("Please enter a Certificate ID");
            return;
        }

        const res = await fetch(BASE_URL + "/verify/" + cert_id);
        const result = await res.json();

        const div = document.getElementById("verifyResult");

        if (result.valid) {
            div.innerHTML = `
                <div style="background:#dcfce7;padding:15px;border-radius:8px;">
                    <p style="color:#16a34a;font-weight:700;margin-bottom:10px;">✅ Valid Certificate</p>
                    <p><strong>Employee:</strong> ${result.certificate.employee_name}</p>
                    <p><strong>Course:</strong> ${result.certificate.course_name}</p>
                    <p><strong>Completed:</strong> ${result.certificate.completion_date}</p>
                    <p><strong>Cert ID:</strong> ${result.certificate.cert_id}</p>
                </div>`;
        } else {
            div.innerHTML = `
                <div style="background:#fee2e2;padding:15px;border-radius:8px;">
                    <p style="color:#dc2626;font-weight:700;">❌ Invalid Certificate</p>
                    <p>${result.message}</p>
                </div>`;
        }

    } catch (err) {
        console.error(err);
    }
}

// ---------------- DASHBOARD (UPDATED) ----------------
async function loadDashboard() {
    try {
        const res = await fetch(BASE_URL + "/dashboard");
        const result = await res.json();

        const matrix = result.matrix || [];
        const courses = result.courses || [];
        const skillMatrix = result.skill_matrix || [];

        let html = '<h3 style="margin-bottom:15px;color:#1e3a8a;">Employee × Course Status</h3>';
        html += '<div style="overflow-x:auto;"><table><tr><th>Employee</th><th>Department</th>';

        courses.forEach(c => {
            html += `<th>${c.title}</th>`;
        });

        html += '</tr>';

        matrix.forEach(emp => {
            html += `<tr><td><strong>${emp.name}</strong></td><td>${emp.department}</td>`;

            courses.forEach(c => {
                const courseData = emp.courses[c.course_id];

                const status = courseData?.status || 'not_started';
                const overdue = courseData?.overdue;

                let displayText = status.replace('_', ' ');
                let className = `status-${status}`;

                if (overdue) {
                    displayText = 'overdue';
                    className = 'status-overdue';
                }

                html += `<td><span class="${className}">${displayText}</span></td>`;
            });

            html += '</tr>';
        });

        html += '</table></div>';

        html += '<h3 style="margin:25px 0 15px;color:#1e3a8a;">Skill Matrix by Department</h3>';

        skillMatrix.forEach(dept => {
            html += `
                <div class="dept-card">
                    <div>
                        <strong>${dept.department}</strong><br>
                        <small style="color:#6b7280">${dept.completed_mandatory}/${dept.total_employees} employees completed mandatory courses</small>
                    </div>
                    <div class="pct">${dept.completion_percentage}%</div>
                </div>`;
        });

        document.getElementById("dashboardContent").innerHTML = html;

    } catch (err) {
        console.error("Error loading dashboard:", err);
    }
}
