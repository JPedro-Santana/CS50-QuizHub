from cs50 import SQL
from flask import Flask, redirect, render_template, request, url_for, abort

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
        
        db.execute("INSERT INTO quiz (title, category, description) VALUES(?, ?, ?)", title, category, description)
        
        quiz_id = db.execute("SELECT last_insert_rowid() as id")[0]["id"]
        
        return redirect(url_for("quiz_layout", id=quiz_id))
    
    return render_template("create.html", categories=CATEGORIES)

@app.route("/explore", methods=["GET"])
def explore():
    category = request.args.get("category")
    order = request.args.get("order")
    search = request.args.get("q")
    
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
    quiz = db.execute("SELECT * FROM quiz WHERE id = ?", quiz_id)

    if len(quiz) == 0:
        abort(404)

    quiz = quiz[0]

    if request.method == "POST":
        title = request.form.get("title")
        category = request.form.get("category")
        description = request.form.get("description")

        db.execute("UPDATE quiz SET title = ?, category = ?, description = ? WHERE id = ?", title, category, description, quiz_id)

        return redirect(url_for("quiz_layout", id=quiz_id))

    return render_template("edit_quiz.html", quiz=quiz, categories=CATEGORIES)


@app.route("/quiz/delete/<int:quiz_id>", methods=["POST"])
def delete_quiz(quiz_id):
    db.execute("DELETE FROM quiz WHERE id=?", quiz_id)
    
    return redirect("/explore")

@app.errorhandler(404)   
def page_not_found(error):
    return render_template("not_found.html"), 404
     

if __name__ == "__main__":
    app.run(debug=True)