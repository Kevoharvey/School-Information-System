document.addEventListener("DOMContentLoaded", () => {
  document.querySelector("#teacherSearch")?.addEventListener("input", (event) => {
    const value = event.target.value.toLowerCase();
    document.querySelectorAll("[data-teacher-card]").forEach((card) => {
      card.classList.toggle("d-none", !card.textContent.toLowerCase().includes(value));
    });
  });
 
  // Auto-fill employment date with today's date when the Add Teacher modal opens.
  // This records the exact day the account (and welcome email) is issued.
  const addTeacherModal = document.querySelector("#addTeacherModal");
  if (addTeacherModal) {
    addTeacherModal.addEventListener("show.bs.modal", () => {
      const dateInput = addTeacherModal.querySelector("input[name='employment_date']");
      if (dateInput && !dateInput.value) {
        dateInput.value = new Date().toISOString().split("T")[0];
      }
    });
  }
});
 