import os
import psycopg2
import psycopg2.extras
from flask import Flask, redirect, render_template, request, url_for, abort, flash, session
from flask_babel import Babel, _
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

app.config["LANGUAGES"] = ["en", "pt_BR", "es"]
app.config["BABEL_DEFAULT_LOCALE"] = "en"
app.config["BABEL_TRANSLATION_DIRECTORIES"] = "translations"


# ── PostgreSQL helper ─────────────────────────────────────────────────────────
class Database:
    """Lightweight psycopg2 wrapper with a cs50-like .execute() interface.

    Returns a list of dicts for SELECT / INSERT … RETURNING queries,
    and an empty list for INSERT / UPDATE / DELETE without RETURNING.
    """

    def __init__(self, url: str):
        # Render supplies 'postgres://' but psycopg2 requires 'postgresql://'
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        self._url = url

    def execute(self, query: str, *args):
        conn = psycopg2.connect(self._url)
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, args or None)
                conn.commit()
                if cur.description:
                    return [dict(row) for row in cur.fetchall()]
                return []
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


_database_url = os.environ.get("DATABASE_URL")
if not _database_url:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Set it to your PostgreSQL connection string before starting the app."
    )

db = Database(_database_url)
# ─────────────────────────────────────────────────────────────────────────────

CATEGORIES = [
    "About Me",
    "Entertainment",
    "History",
    "Science",
    "Sports",
    "Technology",
]

# Ensure category names are discoverable for translation extraction
CATEGORY_TRANSLATIONS = [
    _("About Me"),
    _("Entertainment"),
    _("History"),
    _("Science"),
    _("Sports"),
    _("Technology"),
]

DEFAULT_IMAGES = {
    "About Me": "/static/images/categories/aboutme.jpg",
    "Entertainment": "/static/images/categories/entertainment.jpg",
    "History": "/static/images/categories/history.jpg",
    "Science": "/static/images/categories/science.jpg",
    "Sports": "/static/images/categories/sports.jpg",
    "Technology": "/static/images/categories/tecnology.jpg",
}

def select_locale():
    lang = request.args.get("lang")
    if lang:
        if lang in ["pt", "pt-BR", "pt_BR"]:
            lang = "pt_BR"
        if lang in app.config["LANGUAGES"]:
            session["lang"] = lang
            return lang

    if "lang" in session and session["lang"] in app.config["LANGUAGES"]:
        return session["lang"]

    best = request.accept_languages.best_match(app.config["LANGUAGES"])
    return best if best else app.config["BABEL_DEFAULT_LOCALE"]

babel = Babel(app, locale_selector=select_locale)


@app.route("/set_language/<lang>")
def set_language(lang):
    if lang in ["pt", "pt-BR", "pt_BR"]:
        lang = "pt_BR"
    if lang in app.config["LANGUAGES"]:
        session["lang"] = lang
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    return redirect(url_for("index"))


@app.context_processor
def inject_conf_vars():
    current_lang = select_locale()
    languages = [
        {"code": "en", "name": "English", "flag": "🇺🇸"},
        {"code": "pt_BR", "name": "Português (BR)", "flag": "🇧🇷"},
        {"code": "es", "name": "Español", "flag": "🇪🇸"},
    ]
    return {
        "current_locale": current_lang,
        "languages": languages,
    }


def parse_questions_payload(questions_json):
    if not questions_json:
        return []

    try:
        raw_questions = json.loads(questions_json)
    except json.JSONDecodeError:
        return []

    normalized_questions = []
    for item in raw_questions:
        question_type = item.get("type")
        question_text = (item.get("text") or "").strip()

        if not question_text or question_type not in ("multiple", "boolean", "text"):
            continue

        if question_type in ("multiple", "boolean"):
            options = item.get("options") or []
            clean_options = []
            for option in options:
                option_text = (option or "").strip()
                if option_text:
                    clean_options.append(option_text)

            correct_index = item.get("correct_index")
            if len(clean_options) < 2:
                continue
            if not isinstance(correct_index, int):
                continue
            if correct_index < 0 or correct_index >= len(clean_options):
                continue

            normalized_questions.append(
                {
                    "type": "multiple" if question_type == "multiple" else "boolean",
                    "text": question_text,
                    "options": clean_options,
                    "correct_index": correct_index,
                }
            )
        else:
            correct_answer = (item.get("correct_answer") or "").strip()
            if not correct_answer:
                continue

            normalized_questions.append(
                {
                    "type": "text",
                    "text": question_text,
                    "correct_answer": correct_answer,
                }
            )

    return normalized_questions


def delete_quiz_questions(quiz_id):
    old_questions = db.execute("SELECT id FROM questions WHERE quiz_id=%s", quiz_id)
    for question in old_questions:
        db.execute("DELETE FROM options WHERE question_id=%s", question["id"])
        db.execute("DELETE FROM open_answers WHERE question_id=%s", question["id"])
    db.execute("DELETE FROM questions WHERE quiz_id=%s", quiz_id)


def save_quiz_questions(quiz_id, questions):
    for question in questions:
        question_type_db = "open" if question["type"] == "text" else "multiple"
        result = db.execute(
            "INSERT INTO questions (quiz_id, question_text, question_type)"
            " VALUES (%s, %s, %s) RETURNING id",
            quiz_id,
            question["text"],
            question_type_db,
        )
        question_id = result[0]["id"]

        if question["type"] in ("multiple", "boolean"):
            for index, option_text in enumerate(question["options"]):
                db.execute(
                    "INSERT INTO options (question_id, options_text, is_correct)"
                    " VALUES (%s, %s, %s)",
                    question_id,
                    option_text,
                    index == question["correct_index"],
                )
        else:
            db.execute(
                "INSERT INTO open_answers (question_id, correct_answer) VALUES(%s, %s)",
                question_id,
                question["correct_answer"],
            )


@app.route("/")
@app.route("/index")
def index():
    quizzes = db.execute("SELECT * FROM quiz ORDER BY created_at DESC LIMIT 3")
    total_quizzes = db.execute("SELECT COUNT(*) as count FROM quiz")[0]["count"]
    total_categories = db.execute("SELECT COUNT(DISTINCT category) as count FROM quiz")[0]["count"]
    return render_template(
        "index.html",
        quizzes=quizzes,
        total_quizzes=total_quizzes,
        total_categories=total_categories,
    )


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        category = request.form.get("category")
        description = (request.form.get("description") or "").strip()
        image = (request.form.get("image") or "").strip()
        questions = parse_questions_payload(request.form.get("questions_json"))

        if not image:
            image = DEFAULT_IMAGES.get(category)

        if not title or not category:
            flash(_("Title and Category are required."))
            return redirect("/create")

        if not questions:
            flash(_("Add at least one question"))
            return redirect(url_for("create"))

        result = db.execute(
            "INSERT INTO quiz (title, category, description, image)"
            " VALUES(%s, %s, %s, %s) RETURNING id",
            title, category, description, image,
        )
        quiz_id = result[0]["id"]
        save_quiz_questions(quiz_id, questions)

        return redirect(url_for("quiz_layout", id=quiz_id))

    return render_template("create.html", categories=CATEGORIES)


@app.route("/explore", methods=["GET"])
def explore():
    category = request.args.get("category", "all")
    order = request.args.get("order", "recent")
    search = request.args.get("q", "")
    page = max(1, int(request.args.get("page", 1) or 1))
    per_page = 6

    base_query = "FROM quiz WHERE 1=1"
    params = []

    if category and category != "all":
        base_query += " AND category = %s"
        params.append(category)

    if search:
        base_query += " AND title ILIKE %s"
        params.append(f"%{search}%")

    order_clause = " ORDER BY created_at DESC" if order == "recent" else " ORDER BY created_at ASC"

    total = db.execute(f"SELECT COUNT(*) as count {base_query}", *params)[0]["count"]
    total_pages = max(1, (total + per_page - 1) // per_page)

    # Clamp page to valid range
    page = min(page, total_pages)

    offset = (page - 1) * per_page
    quizzes = db.execute(
        f"SELECT * {base_query}{order_clause} LIMIT %s OFFSET %s",
        *params, per_page, offset
    )

    return render_template(
        "explore.html",
        quizzes=quizzes,
        categories=CATEGORIES,
        selected_category=category,
        selected_order=order,
        search_query=search,
        page=page,
        total_pages=total_pages,
    )


def get_quiz_with_questions(quiz_id):
    quiz = db.execute("SELECT * FROM quiz WHERE id = %s", quiz_id)
    if not quiz:
        return None
    quiz = quiz[0]

    questions = db.execute(
        "SELECT id, question_text, question_type FROM questions WHERE quiz_id = %s",
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
                "SELECT id, options_text, is_correct FROM options WHERE question_id = %s",
                q["id"],
            )
            question["options"] = options
        else:
            answer = db.execute(
                "SELECT correct_answer FROM open_answers WHERE question_id = %s", q["id"]
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
            message = _("Perfect score! You're a genius! 🏆")
        elif percentage >= 80:
            message = _("Excellent work! Almost perfect! 🌟")
        elif percentage >= 60:
            message = _("Well done! Solid performance! 👏")
        elif percentage >= 40:
            message = _("Good effort! Room for improvement! 💪")
        else:
            message = _("Keep practicing! You'll do better next time! 📚")

        result = {
            "correct_count": correct_count,
            "total": total,
            "percentage": percentage,
            "message": message,
        }

    return render_template("quiz_layout.html", quiz=quiz, questions=questions, result=result)


@app.route("/quiz/edit/<int:quiz_id>", methods=["GET", "POST"])
def edit_quiz(quiz_id):
    quiz = db.execute("SELECT * FROM quiz WHERE id=%s", quiz_id)
    if not quiz:
        abort(404)
    quiz = quiz[0]

    questions = db.execute(
        "SELECT id, question_text, question_type FROM questions WHERE quiz_id=%s", quiz_id
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
                "SELECT options_text, is_correct FROM options WHERE question_id=%s", q["id"]
            )
            q_item["options"] = [opt["options_text"] for opt in options]
            q_item["correct_index"] = next(
                (idx for idx, opt in enumerate(options) if opt["is_correct"]), 0
            )
        else:
            answer = db.execute(
                "SELECT correct_answer FROM open_answers WHERE question_id=%s", q["id"]
            )
            q_item["correct_answer"] = answer[0]["correct_answer"] if answer else ""
        question_data.append(q_item)

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        category = request.form.get("category")
        description = (request.form.get("description") or "").strip()
        image = (request.form.get("image") or "").strip()
        new_questions = parse_questions_payload(request.form.get("questions_json"))

        if not image:
            image = DEFAULT_IMAGES.get(category)

        if not title or not category:
            flash(_("Title and category are required."))
            return redirect(url_for("edit_quiz", quiz_id=quiz_id))

        if len(new_questions) == 0:
            flash(_("Quiz must contain at least one question."))
            return redirect(url_for("edit_quiz", quiz_id=quiz_id))

        db.execute(
            "UPDATE quiz SET title=%s, category=%s, description=%s, image=%s WHERE id=%s",
            title, category, description, image, quiz_id,
        )

        delete_quiz_questions(quiz_id)
        save_quiz_questions(quiz_id, new_questions)

        return redirect(url_for("quiz_layout", id=quiz_id))

    return render_template(
        "edit_quiz.html", quiz=quiz, categories=CATEGORIES, questions=question_data
    )


@app.route("/quiz/delete/<int:quiz_id>", methods=["POST"])
def delete_quiz(quiz_id):
    quiz = db.execute("SELECT id FROM quiz WHERE id=%s", quiz_id)
    if not quiz:
        abort(404)

    delete_quiz_questions(quiz_id)
    db.execute("DELETE FROM quiz WHERE id=%s", quiz_id)

    return redirect("/explore")


@app.errorhandler(404)
def page_not_found(error):
    return render_template("not_found.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
