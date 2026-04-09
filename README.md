# CS50's Final Project: QuizHub

### Video Demo:
<a href="http://www.youtube.com/watch?feature=player_embedded&v=tq9AtzCuWp8
" target="_blank"><img src="http://img.youtube.com/vi/tq9AtzCuWp8/0.jpg" 
alt="QuizHub Thumbnail" width="280" height="280" border="10" /></a>

## Description
QuizHub is a web application that allows users to create, explore and solve quizzes on different topics.

The main goal of the project is to provide a simple and interactive platform where user can both test their knowledge and build their own quizzes.
The application was designed with accessibility and ease of use in mind. At this stage, users are not required to create an account or log in, which means anyone can immediately start interacting with the platform.

On the homepage, users are introduced to the project and can quickly navigate to the main sections of the website.
The landing page also displays the three most recently created quizzes, making it easy to discover new content right away.

<img width="1348" height="624" alt="QuizHubHomePage" src="https://github.com/user-attachments/assets/274dbcc8-a325-4187-b66a-3976984dd95a" />

***

#### **QuizHub is divided into four main features:**

### Explore Quizzes
The explore page allows users to browse all quizzes stored in the database. Quizzes can be filtered by category, searched by title, and sorted by creation date. This makes it easier to find quizzes related to specific interests or topics.
<img width="1352" height="608" alt="QuizHubExplore" src="https://github.com/user-attachments/assets/90ac0265-b5ef-40e8-a6bf-ba80d610519d" />

### Solving a Quiz
When solving a quiz, the user is presented with a clean and intuitive interface that displays the quiz title, category, image, description, and all of its questions.

The current version supports multiple question formats:
- Multiple choice
- True or false
- Open answer

After submitting the quiz, the application calculates the score and shows a results screen with:
- Total correct answers
- Percentage score
- A feedback message based on performance
- A full answer review

The answer review highlights correct and incorrect responses, and for open-answer questions it also shows the expected answer. Users can then retry the quiz or return to the explore page.

<img width="1684" height="616" alt="QuH" src="https://github.com/user-attachments/assets/dc1239c3-bb3a-46af-b173-e5f70f9baee0" />

### Create Quiz
Users can create their own quizzes directly on the platform. To create a quiz, the user must provide:
- A title
- A category
- An optional description
- An optional custom image URL

If no image URL is provided, the application automatically assigns a default image based on the selected category.

When building the quiz, users can dynamically add questions using JavaScript. Each question can be created as multiple choice, true/false, or open answer. Before submission, the questions are serialized into JSON and sent to the backend, where they are validated and stored in the SQLite database.
<img width="1224" height="632" alt="QH" src="https://github.com/user-attachments/assets/23c909ba-7a63-421e-83b9-652901523f30" />

### Edit and Delete Quizzes

QuizHub also allows existing quizzes to be managed after creation.

Users can edit a quiz’s title, category, description, image and question list. Existing questions are loaded into the editor so they can be updated, removed, or replaced with new ones. This makes it possible to keep quizzes up to date over time without recreating them from scratch.

If a quiz is no longer needed, it can also be deleted. A confirmation modal is shown before deletion to prevent accidental removal.

## Design Decisions

Several design decisions were made during development to keep the project focused and functional.

Flask was chosen as the backend framework due to its lightweight nature and flexibility. t provides a clear way to handle routes, forms, and database interaction without unnecessary complexity. It also matches the technologies introduced in CS50, making it a practical choice for this project.

SQLite was selected as the database because it is simple, file-based, and easy to integrate into a small web application. Since QuizHub does not require a large-scale database system, SQLite is more than enough for storing quizzes, questions, answer options, and open answers.

While implementing user accounts would add more features, it also introduce additional complexity such as session management and security concerns. Given the scope of this project, the focus was placed on quiz functionality rather than user management. This decision allowed more time to refine the core features of the application.

The frontend was built with plain HTML, CSS, and JavaScript instead of using a frontend framework. This decision was intentional so the project could reinforce core web development concepts and keep the structure easy to understand. JavaScript is used to make the quiz creation and editing experience dynamic, especially when adding, removing, and validating questions.
The application also uses Ionicons for interface icons and custom category images to improve the visual experience without adding unnecessary technical overhead.
## Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript
- CS50 SQL library
- Ionicons

## Project Structure

- `app.py` - Main Flask application. Handles routing, form submission, quiz validation, database interaction, scoring, editing, deletion, and error handling.
- `quiz.db` - SQLite database that stores quizzes, questions, options, and open answers.
- `templates/` - HTML templates for each page of the application.
- `templates/index.html` - Homepage with navigation and recent quizzes.
- `templates/explore.html` - Page for browsing, filtering, and searching quizzes.
- `templates/create.html` - Quiz creation page.
- `templates/edit_quiz.html` - Quiz editing page.
- `templates/quiz_layout.html` - Quiz solving and result review page.
- `templates/not_found.html` - Custom 404 error page.
- `templates/layout.html` - Base layout shared across pages.
- `static/css/` - Stylesheets for the different pages.
- `static/js/script.js` - Frontend logic for creating, editing, validating, and interacting with quizzes.
- `static/fonts/` - Custom Vegur font files used in the design.
- `static/images/` - Logo, GitHub icon, and default category images.

## How to Run

1. Clone the repository.
2. Install the dependencies:

```bash
pip install -r requirements.txt
```
3. Run the application:
```bash
  flask run
```
If needed, you can also run it directly with Python:
  ```bash
    python app.py
  ```

## Final Thoughts

There are several features that could be added in future versions of QuizHub, such as:

- User authentication and personal quiz ownership
- Score history and leaderboard functionality
- More quiz categories and sorting options
- Image upload support instead of only image URLs
- Improved search and filtering
- Better mobile responsiveness and accessibility improvements

 QuizHub was built as a way to apply the concepts learned in CS50, especially in web development, backend logic, databases, and user interaction. The project combines Flask, SQLite, HTML, CSS, and JavaScript into a complete application where users can create, manage, and solve quizzes in a straightforward way.

Although the project is still relatively simple, it already includes a full workflow for quiz creation and participation, along with editing, deletion, validation, and result review. Building it was a valuable experience in structuring a full-stack web application and turning an idea into a working product.
