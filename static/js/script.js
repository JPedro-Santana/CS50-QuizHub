const addQuestionBtn = document.getElementById("btn-add");
const questionTypeSelect = document.querySelector(".question-type");
const questionInput = document.getElementById("question-text");
const questionsContainer = document.getElementById("questions-container");

if (addQuestionBtn && questionTypeSelect && questionInput && questionsContainer) {
  addQuestionBtn.addEventListener("click", addQuestion);

  // Allow pressing Enter in the question input to add a question
  questionInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addQuestion();
    }
  });
}

/* ---- Build a question card element ---- */
function createQuestionElement(type, text, data = {}) {
  const questionDiv = document.createElement("div");
  questionDiv.classList.add("question-item");
  questionDiv.dataset.type = type;

  // Trash icon header
  const header = `
    <div class="q-header">
      <span class="q-type-badge">${typeBadgeLabel(type)}</span>
      <ion-icon name="trash-outline" class="trash-icon" aria-label="Remove question"></ion-icon>
    </div>
    <h3 class="q-text">${escapeHtml(text)}</h3>
  `;

  if (type === "multiple") {
    const options = data.options && data.options.length ? data.options : ["", "", "", ""];
    const correctIndex = data.correct_index !== undefined ? data.correct_index : -1;

    let optionsHtml = '<p class="options-hint">Click an option to mark it as correct</p><div class="option-inputs">';
    for (let i = 0; i < options.length; i++) {
      const isCorrect = i === correctIndex;
      optionsHtml += `
        <div class="option-btn-wrap ${isCorrect ? "is-correct" : ""}" data-index="${i}">
          <span class="option-letter">${String.fromCharCode(65 + i)}</span>
          <input
            type="text"
            class="option-text-input"
            placeholder="Option ${i + 1}${i < 2 ? " (required)" : ""}"
            value="${escapeHtml(options[i] || "")}"
            ${i < 2 ? "required" : ""}
          />
          ${isCorrect ? '<ion-icon name="checkmark-circle" class="correct-icon"></ion-icon>' : '<ion-icon name="ellipse-outline" class="correct-icon"></ion-icon>'}
        </div>`;
    }
    optionsHtml += "</div>";

    questionDiv.innerHTML = header + optionsHtml;

    // Click on option div → set as correct
    questionDiv.querySelectorAll(".option-btn-wrap").forEach((wrap) => {
      wrap.addEventListener("click", (e) => {
        // Don't trigger when clicking the text input itself (let user type)
        if (e.target.tagName === "INPUT") return;
        selectCorrectOption(questionDiv, parseInt(wrap.dataset.index));
      });
    });

  } else if (type === "boolean") {
    const correctIndex = data.correct_index !== undefined ? data.correct_index : -1; // 0=True, 1=False
    questionDiv.innerHTML = `
      ${header}
      <p class="options-hint">Click to select the correct answer</p>
      <div class="option-inputs boolean-options">
        <div class="option-btn-wrap ${correctIndex === 0 ? "is-correct" : ""}" data-index="0">
          <span class="option-letter">T</span>
          <span class="bool-label">True</span>
          ${correctIndex === 0 ? '<ion-icon name="checkmark-circle" class="correct-icon"></ion-icon>' : '<ion-icon name="ellipse-outline" class="correct-icon"></ion-icon>'}
        </div>
        <div class="option-btn-wrap ${correctIndex === 1 ? "is-correct" : ""}" data-index="1">
          <span class="option-letter">F</span>
          <span class="bool-label">False</span>
          ${correctIndex === 1 ? '<ion-icon name="checkmark-circle" class="correct-icon"></ion-icon>' : '<ion-icon name="ellipse-outline" class="correct-icon"></ion-icon>'}
        </div>
      </div>
    `;
    questionDiv.querySelectorAll(".option-btn-wrap").forEach((wrap) => {
      wrap.addEventListener("click", () => {
        selectCorrectOption(questionDiv, parseInt(wrap.dataset.index));
      });
    });

  } else if (type === "text") {
    questionDiv.innerHTML = `
      ${header}
      <div class="open-answer-wrap">
        <label class="open-label">Correct answer:</label>
        <input
          type="text"
          class="open-answer-input"
          placeholder="Type the correct answer…"
          value="${escapeHtml(data.correct_answer || "")}"
          required
        />
      </div>
    `;
  }

  return questionDiv;
}

/* Mark one option as correct, update icons */
function selectCorrectOption(questionDiv, selectedIndex) {
  questionDiv.querySelectorAll(".option-btn-wrap").forEach((wrap, idx) => {
    const isCorrect = idx === selectedIndex;
    wrap.classList.toggle("is-correct", isCorrect);
    const icon = wrap.querySelector(".correct-icon");
    if (icon) icon.setAttribute("name", isCorrect ? "checkmark-circle" : "ellipse-outline");
  });
}

function typeBadgeLabel(type) {
  return { multiple: "Multiple Choice", boolean: "True / False", text: "Open Answer" }[type] || type;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/* ---- Add question from the top form ---- */
function addQuestion() {
  const type = questionTypeSelect.value;
  const questionText = questionInput.value.trim();
  if (!questionText) {
    questionInput.focus();
    questionInput.classList.add("input-error");
    setTimeout(() => questionInput.classList.remove("input-error"), 1200);
    return;
  }

  const questionDiv = createQuestionElement(type, questionText, {
    options: ["", "", "", ""],
    correct_index: -1,
  });

  questionsContainer.appendChild(questionDiv);
  questionDiv.scrollIntoView({ behavior: "smooth", block: "center" });

  // Focus first option input for speed
  const firstInput = questionDiv.querySelector("input[type='text']");
  if (firstInput) firstInput.focus();

  questionInput.value = "";
  updateBackButtonVisibility();
}

/* ---- Serialize questions to JSON before submit ---- */
const form = document.getElementById("quiz-form") || document.querySelector("form");
if (form && questionsContainer) {
  form.addEventListener("submit", (event) => {
    const hiddenInput = document.getElementById("questions-json");
    if (!hiddenInput) return; // not a quiz form

    const questions = [];
    let validationError = false;

    questionsContainer.querySelectorAll(".question-item").forEach((questionDiv) => {
      const type = questionDiv.dataset.type;
      const titleElement = questionDiv.querySelector(".q-text");
      if (!type || !titleElement) return;

      const text = titleElement.textContent.trim();
      if (!text) return;

      if (type === "multiple") {
        const options = [];
        let correctIndex = null;

        questionDiv.querySelectorAll(".option-btn-wrap").forEach((wrap, idx) => {
          const input = wrap.querySelector(".option-text-input");
          if (!input) return;
          const val = input.value.trim();
          if (!val) return;
          options.push(val);
          if (wrap.classList.contains("is-correct")) correctIndex = idx;
        });

        // Re-map correctIndex to account for empty options that were skipped
        if (correctIndex !== null) {
          // Count how many non-empty options exist before correctIndex
          let realCorrect = 0;
          questionDiv.querySelectorAll(".option-btn-wrap").forEach((wrap, idx) => {
            const input = wrap.querySelector(".option-text-input");
            if (!input) return;
            const val = input.value.trim();
            if (val && wrap.classList.contains("is-correct")) {
              realCorrect = options.indexOf(val);
            }
          });
          correctIndex = realCorrect;
        }

        if (options.length < 2) {
          alert(`Question "${text}": please add at least 2 options.`);
          validationError = true;
          return;
        }
        if (correctIndex === null) {
          alert(`Question "${text}": click one option to mark it as the correct answer (green border).`);
          validationError = true;
          return;
        }
        questions.push({ type, text, options, correct_index: correctIndex });

      } else if (type === "text") {
        const input = questionDiv.querySelector(".open-answer-input");
        const correctAnswer = input ? input.value.trim() : "";
        if (!correctAnswer) {
          alert(`Question "${text}": please provide the correct answer.`);
          validationError = true;
          return;
        }
        questions.push({ type, text, correct_answer: correctAnswer });

      } else if (type === "boolean") {
        const selectedWrap = questionDiv.querySelector(".option-btn-wrap.is-correct");
        if (!selectedWrap) {
          alert(`Question "${text}": please select True or False as the correct answer.`);
          validationError = true;
          return;
        }
        const correctIndex = parseInt(selectedWrap.dataset.index);
        questions.push({ type, text, options: ["True", "False"], correct_index: correctIndex });
      }
    });

    if (validationError) {
      event.preventDefault();
      return;
    }

    if (questions.length === 0) {
      event.preventDefault();
      alert("Add at least one question before saving.");
      return;
    }

    hiddenInput.value = JSON.stringify(questions);
  });
}

/* ---- Remove question on trash icon click ---- */
if (questionsContainer) {
  questionsContainer.addEventListener("click", (event) => {
    const optionWrap = event.target.closest(".option-btn-wrap");
    if (optionWrap && !event.target.closest("input")) {
      const questionDiv = optionWrap.closest(".question-item");
      if (questionDiv) {
        selectCorrectOption(questionDiv, parseInt(optionWrap.dataset.index));
      }
      return;
    }

    const trashIcon = event.target.closest('.trash-icon');
    if (!trashIcon) return;
    const questionDiv = trashIcon.closest(".question-item");
    if (questionDiv && questionsContainer.contains(questionDiv)) {
      questionDiv.remove();
      updateBackButtonVisibility();
    }
  });
}

/* ---- Floating back-to-top button ---- */
const backToQuestion = document.createElement("button");
backToQuestion.type = "button";
backToQuestion.className = "back-to-top-btn";
backToQuestion.innerHTML = `<ion-icon name="arrow-up-circle-outline"></ion-icon>`;
if (questionTypeSelect) {
  backToQuestion.addEventListener("click", () => {
    questionTypeSelect.scrollIntoView({ behavior: "smooth" });
    if (questionInput) questionInput.focus();
  });
}

function updateBackButtonVisibility() {
  if (!questionsContainer) return;
  const count = questionsContainer.querySelectorAll(".question-item").length;
  const mainEl = document.querySelector("main");
  if (!mainEl) return;
  if (count >= 2) {
    if (!mainEl.contains(backToQuestion)) mainEl.appendChild(backToQuestion);
  } else {
    if (document.body.contains(backToQuestion)) backToQuestion.remove();
  }
}

if (questionsContainer) updateBackButtonVisibility();

/* ---- Delete quiz modal ---- */
const modal = document.getElementById("deleteModal");
const openBtn = document.getElementById("openDeleteModal");
const cancelBtn = document.getElementById("cancelDelete");
const confirmBtn = document.getElementById("confirmDelete");
const deleteForm = document.getElementById("delete-form");

if (modal && openBtn && cancelBtn && confirmBtn && deleteForm) {
  openBtn.addEventListener("click", () => (modal.style.display = "flex"));
  cancelBtn.addEventListener("click", () => (modal.style.display = "none"));
  confirmBtn.addEventListener("click", () => deleteForm.submit());
  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.style.display = "none";
  });
}

/* ---- Quiz play page: clickable option cards ---- */
document.querySelectorAll(".play-options").forEach((optionsDiv) => {
  optionsDiv.querySelectorAll(".play-option").forEach((optBtn) => {
    optBtn.addEventListener("click", () => {
      // Deselect siblings
      optionsDiv.querySelectorAll(".play-option").forEach((o) => o.classList.remove("selected"));
      optBtn.classList.add("selected");

      // Sync hidden radio input
      const radio = optBtn.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
    });
  });
});
