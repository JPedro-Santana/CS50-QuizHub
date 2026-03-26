from cs50 import SQL
from flask import Flask, redirect, render_template, request, url_for, abort, flash
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = "my-secret-key"

db = SQL("sqlite:///quiz.db")

CATEGORIES = [
    "About Me",
    "Entertainment",
    "History",
    "Science",
    "Sports",
    "Tecnology",
]

DEFAULT_IMAGES = {
    "About Me": "/static/images/categories/aboutme.jpg",
    "Entertainment": "/static/images/categories/entertainment.jpg",
    "History": "/static/images/categories/history.jpg",
    "Science": "/static/images/categories/science.jpg",
    "Sports": "/static/images/categories/sports.jpg",
    "Tecnology": "/static/images/categories/tecnology.jpg",
}


@app.route("/")
@app.route("/index")
def index():
    quizzes = db.execute("SELECT * FROM quiz ORDER BY created_at DESC LIMIT 3")
    return render_template("index.html", quizzes=quizzes)


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        category = request.form.get("category")
        description = (request.form.get("description") or "").strip()
        image = (request.form.get("image") or "").strip()
        questions_json = request.form.get("questions_json")

        if not image:
            image = DEFAULT_IMAGES.get(category)

        if not title or not category:
            flash("Title and Category are required.")
            return redirect("/create")

        if questions_json:
            try:
                questions = json.loads(questions_json)
            except json.JSONDecodeError:
                questions = []
        else:
            questions = []

        if not questions:
            flash("Add at least one question")
            return redirect(url_for("create"))

        db.execute(
            "INSERT INTO quiz (title, category, description, image) VALUES(?, ?, ?, ?)",
            title, category, description, image,
        )
        quiz_id = db.execute("SELECT last_insert_rowid() as id")[0]["id"]

        for q in questions:
            original_type = q.get("type")
            question_text = q.get("text")

            if not question_text or not question_text.strip():
                continue

            question_type_db = "open" if original_type == "text" else "multiple"

            db.execute(
                "INSERT INTO questions (quiz_id, question_text, question_type) VALUES (?, ?, ?)",
                quiz_id, question_text, question_type_db,
            )
            question_id = db.execute("SELECT last_insert_rowid() as id")[0]["id"]

            if original_type in ("multiple", "boolean"):
                options = q.get("options") or []
                correct_index = q.get("correct_index")

                if not options or correct_index is None:
                    continue
                if correct_index >= len(options):
                    continue

                for idx, option_text in enumerate(options):
                    option_text = option_text.strip()
                    if not option_text:
                        continue
                    is_correct = 1 if idx == correct_index else 0
                    db.execute(
                        "INSERT INTO options (question_id, options_text, is_correct) VALUES (?, ?, ?)",
                        question_id, option_text, is_correct,
                    )

            elif original_type == "text":
                correct_answer = q.get("correct_answer")
                if correct_answer:
                    db.execute(
                        "INSERT INTO open_answers (question_id, correct_answer) VALUES(?, ?)",
                        question_id, correct_answer,
                    )

        return redirect(url_for("quiz_layout", id=quiz_id))

    return render_template("create.html", categories=CATEGORIES)


@app.route("/explore", methods=["GET"])
def explore():
    category = request.args.get("category", "all")
    order = request.args.get("order", "recent")
    search = request.args.get("q", "")

    query = "SELECT * FROM quiz WHERE 1=1"
    params = []

    if category and category != "all":
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    query += " ORDER BY created_at DESC" if order == "recent" else " ORDER BY created_at ASC"

    quizzes = db.execute(query, *params)

    return render_template(
        "explore.html",
        quizzes=quizzes,
        categories=CATEGORIES,
        selected_category=category,
        selected_order=order,
        search_query=search,
    )


def get_quiz_with_questions(quiz_id):
    quiz = db.execute("SELECT * FROM quiz WHERE id = ?", quiz_id)
    if not quiz:
        return None
    quiz = quiz[0]

    questions = db.execute(
        "SELECT id, question_text, question_type FROM questions WHERE quiz_id = ?",
        quiz_id,
    )

    quiz_questions = []
    for q in questions:
        question = {
            "id": q["id"],
            "text": q["question_text"],
            "type": q["question_type"],
        }
        if q["question_type"] == "multiple":
            options = db.execute(
                "SELECT id, options_text, is_correct FROM options WHERE question_id = ?",
                q["id"],
            )
            question["options"] = options
        else:
            answer = db.execute(
                "SELECT correct_answer FROM open_answers WHERE question_id = ?", q["id"]
            )
            question["correct_answer"] = answer[0]["correct_answer"] if answer else ""

        quiz_questions.append(question)

    return quiz, quiz_questions


@app.route("/quiz/<int:id>", methods=["GET", "POST"])
def quiz_layout(id):
    result = None
    quiz_data = get_quiz_with_questions(id)
    if not quiz_data:
        abort(404)

    quiz, questions = quiz_data

    if request.method == "POST":
        correct_count = 0
        total = len(questions)

        for question in questions:
            answer_key = f"q_{question['id']}"
            user_answer = request.form.get(answer_key)

            # Store the raw user answer on the question dict (for review display)
            question["user_answer"] = user_answer

            if question["type"] == "multiple":
                if user_answer is None:
                    question["user_correct"] = False
                    continue
                try:
                    selected_index = int(user_answer)
                except (TypeError, ValueError):
                    question["user_correct"] = False
                    continue

                if question.get("options") and 0 <= selected_index < len(question["options"]):
                    is_correct = bool(question["options"][selected_index]["is_correct"])
                    question["user_correct"] = is_correct
                    if is_correct:
                        correct_count += 1
                else:
                    question["user_correct"] = False
            else:
                correct_answer = question.get("correct_answer", "").strip().lower()
                if user_answer and user_answer.strip().lower() == correct_answer:
                    question["user_correct"] = True
                    correct_count += 1
                else:
                    question["user_correct"] = False

        percentage = round((correct_count / total) * 100) if total > 0 else 0

        if percentage == 100:
            message = "Perfect score! You're a genius! 🏆"
        elif percentage >= 80:
            message = "Excellent work! Almost perfect! 🌟"
        elif percentage >= 60:
            message = "Well done! Solid performance! 👏"
        elif percentage >= 40:
            message = "Good effort! Room for improvement! 💪"
        else:
            message = "Keep practicing! You'll do better next time! 📚"

        result = {
            "correct_count": correct_count,
            "total": total,
            "percentage": percentage,
            "message": message,
        }

    return render_template("quiz_layout.html", quiz=quiz, questions=questions, result=result)


@app.route("/quiz/edit/<int:quiz_id>", methods=["GET", "POST"])
def edit_quiz(quiz_id):
    quiz = db.execute("SELECT * FROM quiz WHERE id=?", quiz_id)
    if not quiz:
        abort(404)
    quiz = quiz[0]

    questions = db.execute(
        "SELECT id, question_text, question_type FROM questions WHERE quiz_id=?", quiz_id
    )
    question_data = []
    for q in questions:
        q_item = {
            "id": q["id"],
            "text": q["question_text"],
            "type": q["question_type"],
        }
        if q["question_type"] == "multiple":
            options = db.execute(
                "SELECT options_text, is_correct FROM options WHERE question_id=?", q["id"]
            )
            q_item["options"] = [opt["options_text"] for opt in options]
            q_item["correct_index"] = next(
                (idx for idx, opt in enumerate(options) if opt["is_correct"]), 0
            )
        else:
            answer = db.execute(
                "SELECT correct_answer FROM open_answers WHERE question_id=?", q["id"]
            )
            q_item["correct_answer"] = answer[0]["correct_answer"] if answer else ""
        question_data.append(q_item)

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        category = request.form.get("category")
        description = (request.form.get("description") or "").strip()
        questions_json = request.form.get("questions_json")

        if not title or not category:
            flash("Title and category are required.")
            return redirect(url_for("edit_quiz", quiz_id=quiz_id))

        db.execute(
            "UPDATE quiz SET title=?, category=?, description=? WHERE id=?",
            title, category, description, quiz_id,
        )

        if not questions_json:
            flash("Quiz must contain questions.")
            return redirect(url_for("edit_quiz", quiz_id=quiz_id))

        try:
            new_questions = json.loads(questions_json)
        except json.JSONDecodeError:
            new_questions = []
        if len(new_questions) == 0:
            flash("Quiz must contain at least one question.")
            return redirect(url_for("edit_quiz", quiz_id=quiz_id))

        # Delete old questions/options
        old_questions = db.execute("SELECT id FROM questions WHERE quiz_id=?", quiz_id)
        for q in old_questions:
            db.execute("DELETE FROM options WHERE question_id=?", q["id"])
            db.execute("DELETE FROM open_answers WHERE question_id=?", q["id"])
        db.execute("DELETE FROM questions WHERE quiz_id=?", quiz_id)

        # Insert new questions
        for q in new_questions:
            question_text = q.get("text")
            original_type = q.get("type")
            if not question_text or not question_text.strip():
                continue

            question_type_db = "open" if original_type == "text" else "multiple"
            db.execute(
                "INSERT INTO questions (quiz_id, question_text, question_type) VALUES (?, ?, ?)",
                quiz_id, question_text, question_type_db,
            )
            question_id = db.execute("SELECT last_insert_rowid() as id")[0]["id"]

            if original_type in ("multiple", "boolean"):
                options = q.get("options") or []
                correct_index = q.get("correct_index")
                for idx, option_text in enumerate(options):
                    is_correct = 1 if idx == correct_index else 0
                    db.execute(
                        "INSERT INTO options (question_id, options_text, is_correct) VALUES (?, ?, ?)",
                        question_id, option_text, is_correct,
                    )
            elif original_type == "text":
                correct_answer = q.get("correct_answer")
                if correct_answer:
                    db.execute(
                        "INSERT INTO open_answers (question_id, correct_answer) VALUES (?, ?)",
                        question_id, correct_answer,
                    )

        return redirect(url_for("quiz_layout", id=quiz_id))

    return render_template(
        "edit_quiz.html", quiz=quiz, categories=CATEGORIES, questions=question_data
    )


@app.route("/quiz/delete/<int:quiz_id>", methods=["POST"])
def delete_quiz(quiz_id):
    quiz = db.execute("SELECT id FROM quiz WHERE id=?", quiz_id)
    if not quiz:
        abort(404)

    questions = db.execute("SELECT id from questions WHERE quiz_id=?", quiz_id)
    for q in questions:
        db.execute("DELETE FROM options WHERE question_id=?", q["id"])
        db.execute("DELETE FROM open_answers WHERE question_id=?", q["id"])

    db.execute("DELETE FROM questions WHERE quiz_id=?", quiz_id)
    db.execute("DELETE FROM quiz WHERE id=?", quiz_id)

    return redirect("/explore")


@app.errorhandler(404)
def page_not_found(error):
    return render_template("not_found.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
