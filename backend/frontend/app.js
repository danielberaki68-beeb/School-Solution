// ============================================================
// SCHOOL SOLUTION - MAIN APP.JS
// ============================================================

const API_URL = "http://127.0.0.1:8000";

const TOKEN_KEY = "school_token";
const USER_KEY = "school_user";


// ============================================================
// LOGIN
// ============================================================

document.addEventListener("DOMContentLoaded", function () {

    const loginForm = document.getElementById("loginForm");

    if (loginForm) {
        loginForm.addEventListener("submit", handleLogin);
    }


    // Password show/hide
    const togglePassword =
        document.getElementById("togglePassword");

    if (togglePassword) {

        togglePassword.addEventListener("click", function () {

            const password =
                document.getElementById("password");

            if (!password) {
                return;
            }

            if (password.type === "password") {
                password.type = "text";
            } else {
                password.type = "password";
            }

        });

    }

});


// ============================================================
// LOGIN FUNCTION
// ============================================================

async function handleLogin(event) {

    event.preventDefault();

    const usernameElement =
        document.getElementById("username");

    const passwordElement =
        document.getElementById("password");

    const message =
        document.getElementById("message");

    const loginButton =
        document.getElementById("loginButton");

    const loginText =
        document.getElementById("loginText");

    const loadingText =
        document.getElementById("loadingText");


    const username =
        usernameElement
            ? usernameElement.value.trim()
            : "";

    const password =
        passwordElement
            ? passwordElement.value
            : "";


    if (!username || !password) {

        if (message) {
            message.textContent =
                "Please enter your username and password.";

            message.style.color = "red";
        }

        return;
    }


    if (loginButton) {
        loginButton.disabled = true;
    }

    if (loginText) {
        loginText.classList.add("hidden");
    }

    if (loadingText) {
        loadingText.classList.remove("hidden");
    }


    if (message) {
        message.textContent = "";
    }


    try {

        // ----------------------------------------------------
        // LOGIN REQUEST
        // ----------------------------------------------------

        const response = await fetch(
            API_URL + "/api/auth/login",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },

                body: JSON.stringify({
                    username: username,
                    password: password
                })
            }
        );


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail || "Login failed."
            );

        }


        if (!data.access_token) {

            throw new Error(
                "Login succeeded but no access token was returned."
            );

        }


        // ----------------------------------------------------
        // SAVE TOKEN
        // ----------------------------------------------------

        localStorage.setItem(
            TOKEN_KEY,
            data.access_token
        );


        // ----------------------------------------------------
        // GET CURRENT USER
        // ----------------------------------------------------

        const meResponse = await fetch(
            API_URL + "/api/auth/me",
            {
                method: "GET",

                headers: {
                    "Authorization":
                        "Bearer " + data.access_token,

                    "Accept": "application/json"
                }
            }
        );


        const user = await meResponse.json();


        if (!meResponse.ok) {

            throw new Error(
                user.detail ||
                "Could not load user information."
            );

        }


        // ----------------------------------------------------
        // SAVE USER
        // ----------------------------------------------------

        localStorage.setItem(
            USER_KEY,
            JSON.stringify(user)
        );


        // ----------------------------------------------------
        // OPEN DASHBOARD
        // ----------------------------------------------------

        window.location.href =
            "dashboard.html";


    } catch (error) {

        console.error(
            "LOGIN ERROR:",
            error
        );


        if (message) {

            message.textContent =
                error.message;

            message.style.color =
                "red";

        }


        if (loginButton) {
            loginButton.disabled = false;
        }

        if (loginText) {
            loginText.classList.remove("hidden");
        }

        if (loadingText) {
            loadingText.classList.add("hidden");
        }

    }

}


// ============================================================
// API REQUEST HELPER
// ============================================================

async function apiRequest(
    endpoint,
    options = {}
) {

    const token =
        localStorage.getItem(TOKEN_KEY);


    const headers = {

        "Accept":
            "application/json",

        ...(options.headers || {})

    };


    // Add JSON content type when sending a body
    if (options.body) {

        headers["Content-Type"] =
            "application/json";

    }


    // Add authentication token
    if (token) {

        headers["Authorization"] =
            "Bearer " + token;

    }


    const response =
        await fetch(
            API_URL + endpoint,
            {
                ...options,
                headers: headers
            }
        );


    // --------------------------------------------------------
    // Handle 401
    // --------------------------------------------------------

    if (response.status === 401) {

        localStorage.removeItem(
            TOKEN_KEY
        );

        localStorage.removeItem(
            USER_KEY
        );

        throw new Error(
            "Your session has expired. Please sign in again."
        );

    }


    // --------------------------------------------------------
    // Read response
    // --------------------------------------------------------

    let data;

    const contentType =
        response.headers.get(
            "content-type"
        );


    if (
        contentType &&
        contentType.includes("application/json")
    ) {

        data =
            await response.json();

    } else {

        data =
            await response.text();

    }


    // --------------------------------------------------------
    // Handle errors
    // --------------------------------------------------------

    if (!response.ok) {

        let errorMessage =
            "Request failed.";


        if (
            data &&
            typeof data === "object"
        ) {

            if (data.detail) {

                errorMessage =
                    data.detail;

            }

        } else if (data) {

            errorMessage =
                String(data);

        }


        throw new Error(
            errorMessage
        );

    }


    return data;

}


// ============================================================
// HTML SECURITY HELPERS
// ============================================================

function escapeHtml(value) {

    if (value === null ||
        value === undefined) {

        return "";

    }


    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}


function escapeAttribute(value) {

    return escapeHtml(value);

}


// ============================================================
// ERROR MESSAGE
// ============================================================

function showError(message) {

    const area =
        document.getElementById(
            "contentArea"
        );


    if (!area) {

        alert(message);

        return;

    }


    area.innerHTML = `

        <div class="panel">

            <div
                class="form-message error"
                style="
                    padding:20px;
                    color:#b91c1c;
                    background:#fee2e2;
                    border-radius:8px;
                "
            >

                ${escapeHtml(message)}

            </div>

        </div>

    `;

}


// ============================================================
// SUBJECTS
// ============================================================

async function loadSubjects() {

    const area =
        document.getElementById(
            "contentArea"
        );


    if (!area) {

        console.error(
            "contentArea was not found."
        );

        return;

    }


    area.innerHTML = `

        <div class="page-header">

            <div>

                <h1>
                    Subjects
                </h1>

                <p>
                    Manage unlimited school subjects
                </p>

            </div>


            <button
                class="primary-button"
                onclick="showSubjectForm()"
            >
                + Add Subject
            </button>

        </div>


        <div class="panel">

            <div class="toolbar">

                <input
                    id="subjectSearch"
                    class="search-input"
                    placeholder="Search subjects..."
                >


                <button
                    class="secondary-button"
                    onclick="loadSubjects()"
                >
                    Refresh
                </button>

            </div>


            <div id="subjectsTable">

                Loading subjects...

            </div>

        </div>

    `;


    try {

        const subjects =
            await apiRequest(
                "/api/subjects/"
            );


        renderSubjectsTable(
            subjects
        );


        const searchInput =
            document.getElementById(
                "subjectSearch"
            );


        if (searchInput) {

            searchInput.addEventListener(
                "input",
                function (event) {

                    const search =
                        event.target.value
                            .toLowerCase()
                            .trim();


                    const filtered =
                        subjects.filter(
                            function (subject) {

                                return (

                                    String(
                                        subject.name || ""
                                    )
                                    .toLowerCase()
                                    .includes(search)

                                    ||

                                    String(
                                        subject.code || ""
                                    )
                                    .toLowerCase()
                                    .includes(search)

                                    ||

                                    String(
                                        subject.description || ""
                                    )
                                    .toLowerCase()
                                    .includes(search)

                                );

                            }
                        );


                    renderSubjectsTable(
                        filtered
                    );

                }
            );

        }


    } catch (error) {

        showError(
            "Unable to load subjects: " +
            error.message
        );

    }

}


// ============================================================
// SUBJECT TABLE
// ============================================================

function renderSubjectsTable(
    subjects
) {

    const container =
        document.getElementById(
            "subjectsTable"
        );


    if (!container) {
        return;
    }


    if (
        !subjects ||
        !subjects.length
    ) {

        container.innerHTML = `

            <div class="empty-state">

                <div>
                    📚
                </div>

                <h3>
                    No subjects found
                </h3>

                <p>
                    Add your first subject.
                </p>

            </div>

        `;

        return;

    }


    container.innerHTML = `

        <div class="table-container">

            <table>

                <thead>

                    <tr>

                        <th>
                            ID
                        </th>

                        <th>
                            Subject Name
                        </th>

                        <th>
                            Code
                        </th>

                        <th>
                            Description
                        </th>

                        <th>
                            Actions
                        </th>

                    </tr>

                </thead>


                <tbody>

                    ${subjects.map(
                        subject => `

                        <tr>

                            <td>
                                ${subject.id}
                            </td>


                            <td>

                                <strong>

                                    ${escapeHtml(
                                        subject.name || "-"
                                    )}

                                </strong>

                            </td>


                            <td>

                                ${escapeHtml(
                                    subject.code || "-"
                                )}

                            </td>


                            <td>

                                ${escapeHtml(
                                    subject.description || "-"
                                )}

                            </td>


                            <td>

                                <div
                                    class="action-buttons"
                                >

                                    <button
                                        class="small-button"
                                        onclick="viewSubject(${subject.id})"
                                    >
                                        View
                                    </button>


                                    <button
                                        class="small-button"
                                        onclick="editSubject(${subject.id})"
                                    >
                                        Edit
                                    </button>


                                    <button
                                        class="small-button danger"
                                        onclick="deleteSubject(${subject.id})"
                                    >
                                        Delete
                                    </button>

                                </div>

                            </td>

                        </tr>

                    `
                    ).join("")}

                </tbody>

            </table>

        </div>

    `;

}


// ============================================================
// ADD / EDIT SUBJECT FORM
// ============================================================

function showSubjectForm(
    subject = null
) {

    const editing =
        !!subject;


    const area =
        document.getElementById(
            "contentArea"
        );


    if (!area) {
        return;
    }


    area.innerHTML = `

        <div class="page-header">

            <div>

                <h1>

                    ${
                        editing
                            ? "Edit Subject"
                            : "Add Subject"
                    }

                </h1>


                <p>

                    ${
                        editing
                            ? "Update subject information"
                            : "Create a new subject"
                    }

                </p>

            </div>


            <button
                class="secondary-button"
                onclick="loadSubjects()"
            >
                ← Back
            </button>

        </div>


        <div class="panel">

            <form id="subjectForm">

                <div class="form-grid">


                    <div class="form-field">

                        <label>
                            Subject Name *
                        </label>


                        <input
                            id="subject_name"
                            required
                            placeholder="e.g. Biology"
                            value="${
                                editing
                                    ? escapeAttribute(
                                        subject.name
                                    )
                                    : ""
                            }"
                        >

                    </div>


                    <div class="form-field">

                        <label>
                            Subject Code
                        </label>


                        <input
                            id="subject_code"
                            placeholder="Optional"
                            value="${
                                editing
                                    ? escapeAttribute(
                                        subject.code
                                    )
                                    : ""
                            }"
                        >

                    </div>


                    <div
                        class="form-field full-width"
                    >

                        <label>
                            Description
                        </label>


                        <textarea
                            id="subject_description"
                            placeholder="Subject description..."
                        >${
                            editing
                                ? escapeHtml(
                                    subject.description || ""
                                )
                                : ""
                        }</textarea>

                    </div>


                </div>


                <div
                    id="subjectMessage"
                    class="form-message"
                ></div>


                <div class="form-actions">


                    <button
                        type="button"
                        class="secondary-button"
                        onclick="loadSubjects()"
                    >
                        Cancel
                    </button>


                    <button
                        type="submit"
                        class="primary-button"
                    >

                        ${
                            editing
                                ? "Update Subject"
                                : "Save Subject"
                        }

                    </button>


                </div>


            </form>

        </div>

    `;


    document
        .getElementById("subjectForm")
        .addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();


                await saveSubject(
                    editing
                        ? subject.id
                        : null
                );

            }
        );

}


// ============================================================
// SAVE / UPDATE SUBJECT
// ============================================================

async function saveSubject(
    id = null
) {

    const message =
        document.getElementById(
            "subjectMessage"
        );


    const name =
        document
            .getElementById(
                "subject_name"
            )
            .value
            .trim();


    const code =
        document
            .getElementById(
                "subject_code"
            )
            .value
            .trim();


    const description =
        document
            .getElementById(
                "subject_description"
            )
            .value
            .trim();


    if (!name) {

        if (message) {

            message.textContent =
                "Subject name is required.";

            message.className =
                "form-message error";

        }

        return;

    }


    const payload = {

        name: name,

        code:
            code || null,

        description:
            description || null

    };


    try {

        await apiRequest(

            id
                ? `/api/subjects/${id}`
                : "/api/subjects/",

            {

                method:
                    id
                        ? "PUT"
                        : "POST",

                body:
                    JSON.stringify(
                        payload
                    )

            }

        );


        alert(

            id
                ? "Subject updated successfully."
                : "Subject added successfully."

        );


        await loadSubjects();


    } catch (error) {

        console.error(
            "Subject save error:",
            error
        );


        if (message) {

            message.textContent =
                error.message;

            message.className =
                "form-message error";

        } else {

            alert(
                error.message
            );

        }

    }

}


// ============================================================
// VIEW SUBJECT
// ============================================================

async function viewSubject(
    id
) {

    try {

        const subject =
            await apiRequest(
                `/api/subjects/${id}`
            );


        alert(

            `Subject\n\n` +

            `ID: ${
                subject.id
            }\n` +

            `Name: ${
                subject.name || "-"
            }\n` +

            `Code: ${
                subject.code || "-"
            }\n` +

            `Description: ${
                subject.description || "-"
            }`

        );


    } catch (error) {

        alert(
            error.message
        );

    }

}


// ============================================================
// EDIT SUBJECT
// ============================================================

async function editSubject(
    id
) {

    try {

        const subject =
            await apiRequest(
                `/api/subjects/${id}`
            );


        showSubjectForm(
            subject
        );


    } catch (error) {

        alert(
            error.message
        );

    }

}


// ============================================================
// DELETE SUBJECT
// ============================================================

async function deleteSubject(
    id
) {

    if (
        !confirm(
            "Are you sure you want to delete this subject?"
        )
    ) {

        return;

    }


    try {

        await apiRequest(

            `/api/subjects/${id}`,

            {
                method: "DELETE"
            }

        );


        alert(
            "Subject deleted successfully."
        );


        await loadSubjects();


    } catch (error) {

        alert(
            error.message
        );

    }

}


// ============================================================
// LOGOUT
// ============================================================

function logout() {

    localStorage.removeItem(
        TOKEN_KEY
    );

    localStorage.removeItem(
        USER_KEY
    );


    window.location.href =
        "index.html";

}