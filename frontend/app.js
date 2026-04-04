const BASE_URL = "YOUR_API_GATEWAY_URL_HERE";
let courses = [];
function show(section) {
    ['courses', 'create', 'assign'].forEach(s => {
        document.getElementById(s).style.display = 'none';
    });
    document.getElementById(section).style.display = 'block';
}
async function getCourses() {
    try {
        const res = await fetch(BASE_URL + "/courses");
        const result = await res.json();
        courses = result.courses;
        const list = document.getElementById("courseList");
        list.innerHTML = "";
        if (courses.length === 0) {
            list.innerHTML = "<li>No courses found.</li>";
            return;
        }
        courses.forEach(c => {
            list.innerHTML += `
                <li>
                    <strong>${c.title}</strong><br>
                    <span class="status">${c.description} | Passing Score: ${c.passing_score}</span>
                </li>`;
        });
    } catch (err) {
        console.error("Error loading courses:", err);
    }
}
async function loadCoursesForAssign() {
    try {
        const res = await fetch(BASE_URL + "/courses");
        const result = await res.json();
        courses = result.courses;
        const dropdown = document.getElementById("courseDropdown");
        dropdown.innerHTML = "";
        courses.forEach(c => {
            dropdown.innerHTML += `<option value="${c.course_id}">${c.title}</option>`;
        });
    } catch (err) {
        console.error("Error loading courses for assign:", err);
    }
}
async function createCourse() {
    try {
        const data = {
            title: document.getElementById("title").value,
            description: document.getElementById("description").value,
            external_video_url: document.getElementById("video_url").value,
            passing_score: parseInt(document.getElementById("passing_score").value),
            assigned_roles: document.getElementById("assigned_roles").value
                .split(",").map(r => r.trim())
        };
        const res = await fetch(BASE_URL + "/courses", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        document.getElementById("createMsg").innerText = result.message || "Course created!";
    } catch (err) {
        document.getElementById("createMsg").innerText = "Error creating course.";
        console.error(err);
    }
}
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
        document.getElementById("assignMsg").innerText = result.message || "Assigned!";
    } catch (err) {
        document.getElementById("assignMsg").innerText = "Error assigning course.";
        console.error(err);
    }
}