from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector

app = Flask(__name__)
app.secret_key = "ai_interview_coach_secret_key_2026"


def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="",
        database="ai interview coach"
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            return "Please fill all fields."

        if password != confirm_password:
            return "Passwords do not match."

        db = None
        cursor = None

        try:
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute(
                "SELECT id FROM users WHERE email=%s",
                (email,)
            )

            if cursor.fetchone():
                return "Email already registered."

            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                (name, email, password, "User")
            )

            db.commit()

            return redirect(url_for("login"))

        except mysql.connector.Error as error:
            return f"Database Error: {error}"

        finally:
            if cursor:
                cursor.close()

            if db:
                db.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            return "Please enter email and password."

        db = None
        cursor = None

        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id, name, email, password, role
                FROM users
                WHERE email=%s AND password=%s
                """,
                (email, password)
            )

            user = cursor.fetchone()

            if user:

                session["user_id"] = user["id"]
                session["name"] = user["name"]
                session["email"] = user["email"]
                session["role"] = user["role"]

                if user["role"] == "Admin":
                    return redirect(url_for("admin"))

                return redirect(url_for("dashboard"))

            return "Invalid Email or Password."

        except mysql.connector.Error as error:
            return f"Database Error: {error}"

        finally:
            if cursor:
                cursor.close()

            if db:
                db.close()

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session.get("name"),
        email=session.get("email")
    )


@app.route("/interview")
def interview():

    if "user_id" not in session:
        return redirect(url_for("login"))

    role = request.args.get("role", "").strip()

    if not role:
        return "Please select a job role."

    db = None
    cursor = None

    try:

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT q.id, q.question_text
            FROM questions q
            INNER JOIN job_roles r
            ON q.role_id = r.id
            WHERE r.role_name=%s
            ORDER BY q.id ASC
            LIMIT 10
            """,
            (role,)
        )

        questions_data = cursor.fetchall()

        if not questions_data:
            return f"No questions available for {role}."

        questions = [
            q["question_text"]
            for q in questions_data
        ]

        return render_template(
            "interview.html",
            role=role,
            questions=questions
        )

    except mysql.connector.Error as error:
        return f"Database Error: {error}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


@app.route("/get_questions")
def get_questions():

    if "user_id" not in session:
        return jsonify({
            "error": "Please login first"
        }), 401

    role = request.args.get("role", "").strip()

    if not role:
        return jsonify({
            "questions": []
        })

    db = None
    cursor = None

    try:

        db = get_db_connection()

        cursor = db.cursor(
            dictionary=True,
            buffered=True
        )

        cursor.execute(
            """
            SELECT q.id, q.question_text
            FROM questions q
            INNER JOIN job_roles r
            ON q.role_id = r.id
            WHERE r.role_name=%s
            ORDER BY q.id ASC
            LIMIT 10
            """,
            (role,)
        )

        rows = cursor.fetchall()

        return jsonify({
            "questions": [
                row["question_text"]
                for row in rows
            ]
        })

    except mysql.connector.Error as error:

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


@app.route("/result")
def result():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("result.html")


@app.route("/save_result", methods=["POST"])
def save_result():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "error": "User not logged in."
        }), 401

    db = None
    cursor = None

    try:

        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "error": "No result data received."
            }), 400

        role = data.get("role", "")
        score = data.get("score", 0)
        status = data.get("status", "Rejected")
        feedback = data.get("feedback", "")

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO interview_results
            (user_id, job_role, score, status, feedback)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                role,
                score,
                status,
                feedback
            )
        )

        db.commit()

        return jsonify({
            "success": True,
            "message": "Interview result saved successfully."
        })

    except mysql.connector.Error as error:

        if db:
            db.rollback()

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied - Admin Only"

    return render_template(
        "admin.html",
        name=session.get("name")
    )


@app.route("/users")
def users():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied - Admin Only"

    db = None
    cursor = None

    try:

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, name, email, role
            FROM users
            ORDER BY id DESC
            """
        )

        user_data = cursor.fetchall()

        return render_template(
            "users.html",
            user_data=user_data,
            users=user_data
        )

    except mysql.connector.Error as error:
        return f"Database Error: {error}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


@app.route("/job_roles")
def job_roles():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied - Admin Only"

    db = None
    cursor = None

    try:

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, role_name, description
            FROM job_roles
            ORDER BY id ASC
            """
        )

        role_data = cursor.fetchall()

        return render_template(
            "job_roles.html",
            role_data=role_data,
            roles=role_data
        )

    except mysql.connector.Error as error:
        return f"Database Error: {error}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


@app.route("/add_job_role", methods=["POST"])
def add_job_role():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied - Admin Only"

    role_name = request.form.get(
        "role_name",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    if not role_name or not description:
        return "Please fill all fields."

    db = None
    cursor = None

    try:

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            "SELECT id FROM job_roles WHERE role_name=%s",
            (role_name,)
        )

        if cursor.fetchone():
            return "This job role already exists."

        cursor.execute(
            """
            INSERT INTO job_roles
            (role_name, description)
            VALUES (%s, %s)
            """,
            (
                role_name,
                description
            )
        )

        db.commit()

        return redirect(
            url_for("job_roles")
        )

    except mysql.connector.Error as error:

        return f"Database Error: {error}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


@app.route(
    "/edit_job_role/<int:role_id>",
    methods=["GET", "POST"]
)
def edit_job_role(role_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied - Admin Only"

    db = None
    cursor = None

    try:

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        if request.method == "POST":

            role_name = request.form.get(
                "role_name",
                ""
            ).strip()

            description = request.form.get(
                "description",
                ""
            ).strip()

            if not role_name or not description:
                return "Please fill all fields."

            cursor.execute(
                """
                UPDATE job_roles
                SET role_name=%s,
                    description=%s
                WHERE id=%s
                """,
                (
                    role_name,
                    description,
                    role_id
                )
            )

            db.commit()

            return redirect(
                url_for("job_roles")
            )

        cursor.execute(
            """
            SELECT id, role_name, description
            FROM job_roles
            WHERE id=%s
            """,
            (role_id,)
        )

        role = cursor.fetchone()

        if not role:
            return "Job role not found."

        return render_template(
            "edit_job_role.html",
            role=role
        )

    except mysql.connector.Error as error:

        return f"Database Error: {error}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


@app.route(
    "/delete_job_role/<int:role_id>"
)
def delete_job_role(role_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied - Admin Only"

    db = None
    cursor = None

    try:

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM questions
            WHERE role_id=%s
            """,
            (role_id,)
        )

        question_count = cursor.fetchone()[0]

        if question_count > 0:

            return """
            <h2>Cannot Delete Job Role</h2>

            <p>
            This job role has interview questions linked to it.
            </p>

            <p>
            Delete the related questions first.
            </p>

            <br>

            <a href="/job_roles">
            ← Back to Job Roles
            </a>
            """

        cursor.execute(
            "DELETE FROM job_roles WHERE id=%s",
            (role_id,)
        )

        db.commit()

        return redirect(
            url_for("job_roles")
        )

    except mysql.connector.Error as error:

        return f"Database Error: {error}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


@app.route("/questions")
def questions():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied - Admin Only"

    db = None
    cursor = None

    try:

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                q.id,
                q.role_id,
                r.role_name,
                q.question_text
            FROM questions q
            INNER JOIN job_roles r
            ON q.role_id=r.id
            ORDER BY q.id ASC
            """
        )

        question_data = cursor.fetchall()

        cursor.execute(
            """
            SELECT id, role_name
            FROM job_roles
            ORDER BY id ASC
            """
        )

        role_data = cursor.fetchall()

        return render_template(
            "questions.html",
            question_data=question_data,
            role_data=role_data,
            questions=question_data,
            roles=role_data
        )

    except mysql.connector.Error as error:

        return f"Database Error: {error}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


@app.route(
    "/add_question",
    methods=["POST"]
)
def add_question():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied - Admin Only"

    role_id = request.form.get(
        "role_id"
    )

    question_text = request.form.get(
        "question_text",
        ""
    ).strip()

    if not role_id or not question_text:
        return "Please fill all fields."

    db = None
    cursor = None

    try:

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO questions
            (role_id, question_text)
            VALUES (%s, %s)
            """,
            (
                role_id,
                question_text
            )
        )

        db.commit()

        return redirect(
            url_for("questions")
        )

    except mysql.connector.Error as error:

        return f"Database Error: {error}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


@app.route(
    "/edit_question/<int:question_id>",
    methods=["GET", "POST"]
)
def edit_question(question_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied - Admin Only"

    db = None
    cursor = None

    try:

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        if request.method == "POST":

            role_id = request.form.get(
                "role_id"
            )

            question_text = request.form.get(
                "question_text",
                ""
            ).strip()

            if not role_id or not question_text:
                return "Please fill all fields."

            cursor.execute(
                """
                UPDATE questions
                SET role_id=%s,
                    question_text=%s
                WHERE id=%s
                """,
                (
                    role_id,
                    question_text,
                    question_id
                )
            )

            db.commit()

            return redirect(
                url_for("questions")
            )

        cursor.execute(
            """
            SELECT id, role_id, question_text
            FROM questions
            WHERE id=%s
            """,
            (question_id,)
        )

        question = cursor.fetchone()

        if not question:
            return "Question not found."

        cursor.execute(
            """
            SELECT id, role_name
            FROM job_roles
            ORDER BY id ASC
            """
        )

        role_data = cursor.fetchall()

        return render_template(
            "edit_question.html",
            question=question,
            role_data=role_data
        )

    except mysql.connector.Error as error:

        return f"Database Error: {error}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


@app.route(
    "/delete_question/<int:question_id>"
)
def delete_question(question_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied - Admin Only"

    db = None
    cursor = None

    try:

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            "DELETE FROM questions WHERE id=%s",
            (question_id,)
        )

        db.commit()

        return redirect(
            url_for("questions")
        )

    except mysql.connector.Error as error:

        return f"Database Error: {error}"

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


# =========================================================
# REPORTS & ANALYTICS
# =========================================================

@app.route("/reports")
def reports():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied - Admin Only"

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # -----------------------------
        # BASIC STATISTICS
        # -----------------------------

        cursor.execute(
            "SELECT COUNT(*) AS total_users FROM users"
        )

        total_users = cursor.fetchone()["total_users"]

        cursor.execute(
            "SELECT COUNT(*) AS total_interviews FROM interview_results"
        )

        total_interviews = cursor.fetchone()["total_interviews"]

        cursor.execute(
            "SELECT AVG(score) AS average_score FROM interview_results"
        )

        result = cursor.fetchone()

        average_score = (
            0
            if result["average_score"] is None
            else round(float(result["average_score"]))
        )

        cursor.execute(
            "SELECT COUNT(*) AS selected "
            "FROM interview_results "
            "WHERE status='Selected'"
        )

        selected = cursor.fetchone()["selected"]

        cursor.execute(
            "SELECT COUNT(*) AS rejected "
            "FROM interview_results "
            "WHERE status='Rejected'"
        )

        rejected = cursor.fetchone()["rejected"]

        # -----------------------------
        # FULL INTERVIEW REPORT
        # -----------------------------

        cursor.execute(
            """
            SELECT
                ir.id,
                ir.user_id,
                ir.job_role,
                ir.score,
                ir.status,
                ir.feedback,
                ir.start_time,
                ir.end_time,
                ir.duration_seconds,
                u.name,
                u.email
            FROM interview_results ir
            LEFT JOIN users u
                ON ir.user_id = u.id
            ORDER BY ir.id DESC
            """
        )

        interview_data = cursor.fetchall()

        # -----------------------------
        # QUESTION-WISE REPORT
        # -----------------------------

        cursor.execute(
            """
            SELECT
                id,
                interview_id,
                question_no,
                question_text,
                answer_text,
                answer_time_seconds,
                question_score
            FROM interview_answers
            ORDER BY interview_id DESC, question_no ASC
            """
        )

        answer_data = cursor.fetchall()

        # -----------------------------
        # SEND DATA TO HTML
        # -----------------------------

        return render_template(
            "reports.html",
            total_users=total_users,
            total_interviews=total_interviews,
            average_score=average_score,
            selected=selected,
            rejected=rejected,
            reports=interview_data,
            answer_data=answer_data,
            interview_data=interview_data
        )

    except mysql.connector.Error as error:
        return f"Reports Database Error: {error}"

    finally:
        if cursor:
            cursor.close()

        if db:
            db.close()
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
   