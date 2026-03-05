



/*Opening modal confirmation when clicking on delete quiz button*/ 
const modal = document.getElementById("deleteModal")
const openBtn = document.getElementById("openDeleteModal")
const cancelBtn = document.getElementById("cancelDelete")
const confirmBtn = document.getElementById("confirmDelete")
const deleteForm = document.getElementById("delete-form")

openBtn.addEventListener("click", () => {
    modal.style.display = "flex"
})

cancelBtn.addEventListener("click", () => {
    modal.style.display = "none"
})

confirmBtn.addEventListener("click", () => {
    deleteForm.submit()
})