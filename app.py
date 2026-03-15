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
    "Entertainment": "/static/images/categories/entertainment.jpg" ,
    "History": "/static/images/categories/history.jpg",
    "Science": "/static/images/categories/science.jpg",
    "Sports": "/static/images/categories/sports.jpg" ,
    "Tecnology": "/static/images/categories/tecnology.jpg"
}

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        title = request.form.get("title")
        category = request.form.get("category")
        description = request.form.get("description")
        image = request.form.get("image")

        if not image:
            image = DEFAULT_IMAGES.get(category)
            
        if not title or not category:
            flash("Title and Category are required.")
            return redirect ("/create")

        db.execute(
            "INSERT INTO quiz (title, category, description, image) VALUES(?, ?, ?, ?)",
            title,
            category,
            description,
            image,
        )

        quiz_id = db.execute("SELECT last_insert_rowid() as id")[0]["id"]

        questions_json = request.form.get("questions_json")
        if questions_json:
            try:
                questions = json.loads(questions_json)
            except json.JSONDecodeError:
                questions = []

            if not questions:
                flash("Add at least one question")
                return redirect(url_for("create"))
                
            for q in questions:
                original_type = q.get("type")
                question_text = q.get("text")   

                if not question_text or not question_text.strip():
                    continue
                
                if original_type == "text":
                    question_type_db = "open"
                else:
                    question_type_db = "multiple"

                db.execute(
                    "INSERT INTO questions (quiz_id, question_text, question_type) VALUES (?, ?, ?)",
                    quiz_id,
                    question_text,
                    question_type_db,
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
                            question_id,
                            option_text,
                            is_correct,
                        )
                        
                elif original_type == "text":
                    correct_answer = q.get("correct_answer")
                    if correct_answer:
                        db.execute(
                            "INSERT INTO open_answers (question_id, correct_answer) VALUES(?, ?)",
                            question_id,
                            correct_answer,
                        )

        return redirect(url_for("quiz_layout", id=quiz_id))

    return render_template("create.html", categories=CATEGORIES)

@app.route("/explore", methods=["GET"])
def explore():
    category = request.args.get("category", "all")
    order = request.args.get("order", "recent")
    search = request.args.get("q", "")
    
    query = "SELECT * FROM quiz WHERE 1=1"
    params= []
    
    if category and category != "all":
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    if order == "recent":
        query += " ORDER BY created_at DESC"
    else:
        query += " ORDER BY created_at ASC"

    quizzes = db.execute(query, *params)

    return render_template("explore.html",
        quizzes=quizzes,
        categories=CATEGORIES,
        selected_category=category,
        selected_order=order,
        search_query=search
    )

@app.route("/quiz/<int:id>")
def quiz_layout(id):   
    quiz = db.execute("SELECT * FROM quiz WHERE id = ?", id) 
    
    if len(quiz) == 0:
        abort(404)
    
    return render_template("quiz_layout.html", quiz=quiz[0])


@app.route("/quiz/edit/<int:quiz_id>", methods=["GET", "POST"])
def edit_quiz(quiz_id):
    quiz = db.execute("SELECT * FROM quiz WHERE id=?", quiz_id)

    if not quiz:
        abort(404)

    quiz = quiz[0]

    if request.method == "POST":

        title = request.form.get("title")
        category = request.form.get("category")
        description = request.form.get("description")
        questions_json = request.form.get("questions_json")

        db.execute(
            "UPDATE quiz SET title=?, category=?, description=? WHERE id=?",
            title,
            category,
            description,
            quiz_id,
        )

        old_questions = db.execute(
            "SELECT id FROM questions WHERE quiz_id=?",
            quiz_id
        )

        for q in old_questions:
            db.execute("DELETE FROM options WHERE question_id=?", q["id"])
            db.execute("DELETE FROM open_answers WHERE question_id=?", q["id"])

        db.execute("DELETE FROM questions WHERE quiz_id=?", quiz_id)

        if questions_json:

            questions = json.loads(questions_json)

            for q in questions:

                question_text = q.get("text")
                original_type = q.get("type")

                if not question_text:
                    continue

                question_type_db = "open" if original_type == "text" else "multiple"

                db.execute(
                    "INSERT INTO questions (quiz_id, question_text, question_type) VALUES (?, ?, ?)",
                    quiz_id,
                    question_text,
                    question_type_db,
                )

                question_id = db.execute("SELECT last_insert_rowid() as id")[0]["id"]

                if original_type in ("multiple", "boolean"):

                    options = q.get("options") or []
                    correct_index = q.get("correct_index")

                    for idx, option in enumerate(options):

                        is_correct = 1 if idx == correct_index else 0

                        db.execute(
                            "INSERT INTO options (question_id, options_text, is_correct) VALUES (?, ?, ?)",
                            question_id,
                            option,
                            is_correct,
                        )

                elif original_type == "text":

                    correct_answer = q.get("correct_answer")

                    if correct_answer:
                        db.execute(
                            "INSERT INTO open_answers (question_id, correct_answer) VALUES (?, ?)",
                            question_id,
                            correct_answer,
                        )

        return redirect(url_for("quiz_layout", id=quiz_id))

    questions = db.execute(
        "SELECT * FROM questions WHERE quiz_id=?",
        quiz_id
    )

    for q in questions:

        if q["question_type"] == "multiple":

            q["options"] = db.execute(
                "SELECT * FROM options WHERE question_id=?",
                q["id"]
            )

        elif q["question_type"] == "open":

            answer = db.execute(
                "SELECT * FROM open_answers WHERE question_id=?",
                q["id"]
            )

            q["correct_answer"] = answer[0]["correct_answer"] if answer else ""

    return render_template(
        "edit_quiz.html",
        quiz=quiz,
        questions=questions,
        categories=CATEGORIES
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