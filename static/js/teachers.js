document.addEventListener("DOMContentLoaded", () => {
  document.querySelector("#teacherSearch")?.addEventListener("input", (event) => {
    const value = event.target.value.toLowerCase();
    document.querySelectorAll("[data-teacher-card]").forEach((card) => {
      card.classList.toggle("d-none", !card.textContent.toLowerCase().includes(value));
    });
  });
});
