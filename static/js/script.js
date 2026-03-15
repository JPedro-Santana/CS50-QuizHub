/* Adding a new question */
const addQuestionBtn = document.getElementById("btn-add");
const questionTypeSelect = document.querySelector(".question-type");
const questionInput = document.getElementById("question-text");
const questionsContainer = document.getElementById("questions-container");

if (
  addQuestionBtn &&
  questionTypeSelect &&
  questionInput &&
  questionsContainer
) {
  addQuestionBtn.addEventListener("click", addQuestion);
}

function addQuestion() {
  const type = questionTypeSelect.value;
  const questionText = questionInput.value.trim();

  if (!questionText) {
    return;
  }

  const questionDiv = document.createElement("div");
  questionDiv.classList.add("question-item");
  questionDiv.dataset.type = type;

  if (type === "multiple") {
    const groupName = `answer-${Date.now()}`;
    questionDiv.innerHTML = `
    <ion-icon name="trash-outline" aria-label="Remove"></ion-icon>
    <h3>${questionText}</h3>
      <p>Select the correct answer:</p>
      <div class="options">
        <label>
          <input type="radio" name="${groupName}" value="1">
          <input type="text" name="options" placeholder="Option 1" required>
        </label>
        <label>
          <input type="radio" name="${groupName}" value="2">
          <input type="text" name="options" placeholder="Option 2" required>
        </label>
        <label>
          <input type="radio" name="${groupName}" value="3">
          <input type="text" name="options" placeholder="Option 3">
        </label>
        <label>
          <input type="radio" name="${groupName}" value="4">
          <input type="text" name="options" placeholder="Option 4">
        </label>
      </div>
    `;
  } else if (type === "text") {
    questionDiv.innerHTML = `
    <ion-icon name="trash-outline" aria-label="Remove"></ion-icon>
    <h3>${questionText}</h3>
    <input type="text"  name="correct_answer" class="input" placeholder="Correct answer.." required>
    `;
  } else if (type === "boolean") {
    const groupName = `answer-${Date.now()}`;
    questionDiv.innerHTML = `
      <ion-icon name="trash-outline" aria-label="Remove"></ion-icon>
      <h3>${questionText}</h3>
      <label>
        <input type="radio" name="${groupName}" value="true">
        True
      </label>
      <label>
        <input type="radio" name="${groupName}" value="false">
        False
      </label>
    `;
  }

  questionsContainer.appendChild(questionDiv);
  questionDiv.scrollIntoView();

  if (type === "text" || type === "multiple") {
    const answerInput = questionDiv.querySelector('input[type="text"]');
    if (answerInput) {
      answerInput.focus();
    }
  }

  questionInput.value = "";

  updateBackButtonVisibility();
}

const form =
  document.getElementById("quiz-form") || document.querySelector("form");
if (form && questionsContainer) {
  form.addEventListener("submit", (event) => {
    const questions = [];
    questionsContainer
      .querySelectorAll(".question-item")
      .forEach((questionDiv) => {
        const type = questionDiv.dataset.type;
        const titleElement = questionDiv.querySelector("h3");
        if (!type || !titleElement) return;
        const text = titleElement.textContent.trim();
        if (type === "multiple") {
          const options = [];
          let correctIndex = null;
          const labels = questionDiv.querySelectorAll(".options label");
          labels.forEach((label, index) => {
            const radio = label.querySelector('input[type="radio"]');
            const textInput = label.querySelector('input[type="text"]');
            if (!textInput) return;
            const optionText = textInput.value.trim();
            if (!optionText) return;
            options.push(optionText);
            if (radio && radio.checked) {
              correctIndex = index;
            }
          });
          if (correctIndex === null) {
            alert("Select the correct answer");
            event.preventDefault();
            return;
          }
          if (options.length > 0) {
            questions.push({
              type,
              text,
              options,
              correct_index: correctIndex,
            });
          }
        } else if (type === "text") {
          const answerInput = questionDiv.querySelector(
            'input[name="correct_answer"]',
          );
          if (answerInput) {
            questions.push({
              type,
              text,
              correct_answer: answerInput.value.trim(),
            });
          }
        } else if (type === "boolean") {
          const radios = questionDiv.querySelectorAll('input[type="radio"]');
          let correctValue = null;
          radios.forEach((radio) => {
            if (radio.checked) {
              correctValue = radio.value;
            }
          });
          if (!correctValue) {
            alert("Select True or False");
            event.preventDefault();
            return;
          }
          const options = ["True", "False"];
          const correctIndex = correctValue === "true" ? 0 : 1;
          questions.push({ type, text, options, correct_index: correctIndex });
        }
      });
      
    if (questions.length === 0) {
      event.preventDefault();
      return;
    }
    const hiddenInput = document.getElementById("questions-json");
    if (hiddenInput) {
      hiddenInput.value = JSON.stringify(questions);
    }
  });
}

/* Remove question when clicking on trash icon */
if (questionsContainer) {
  questionsContainer.addEventListener("click", (event) => {
    const trashIcon = event.target.closest('ion-icon[name="trash-outline"]');
    if (!trashIcon) return;

    const questionDiv = trashIcon.closest(".question-item");
    if (questionDiv && questionsContainer.contains(questionDiv)) {
      questionDiv.remove();
    }
  });
}

/* Go back to the question input section when clicking in the arrow icon */
const backToQuestion = document.createElement("button");
backToQuestion.innerHTML = `<ion-icon name="arrow-up-circle-outline"></ion-icon>`;

backToQuestion.addEventListener("click", () => {
  questionTypeSelect.scrollIntoView();
  questionInput.focus();
});

function updateBackButtonVisibility() {
  const questionCount =
    questionsContainer.querySelectorAll(".question-item").length;
  if (questionCount >= 2) {
    if (!document.querySelector("main").contains(backToQuestion)) {
      document.querySelector("main").appendChild(backToQuestion);
    }
  } else {
    if (document.body.contains(backToQuestion)) {
      backToQuestion.remove();
    }
  }
}

const messages = [
  "Keep practicing! You'll do better next time! 📚",
  "Good effort! Room for improvement! 💪",
  "Well done! Solid performance! 👏",
  "Excellent work! Almost perfect! 🌟",
  "Perfect score! You're a genius! 🏆",
];

/* Opening modal confirmation when clicking on delete quiz button */
const modal = document.getElementById("deleteModal");
const openBtn = document.getElementById("openDeleteModal");
const cancelBtn = document.getElementById("cancelDelete");
const confirmBtn = document.getElementById("confirmDelete");
const deleteForm = document.getElementById("delete-form");

if (modal && openBtn && cancelBtn && confirmBtn && deleteForm) {
  openBtn.addEventListener("click", () => {
    modal.style.display = "flex";
  });

  cancelBtn.addEventListener("click", () => {
    modal.style.display = "none";
  });

  confirmBtn.addEventListener("click", () => {
    deleteForm.submit();
  });
}
