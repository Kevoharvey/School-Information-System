document.addEventListener("DOMContentLoaded", () => {
  document.querySelector("#assignmentSearch")?.addEventListener("input", (event) => {
    const value = event.target.value.toLowerCase();
    document.querySelectorAll("[data-assignment-row]").forEach((row) => {
      row.classList.toggle("d-none", !row.textContent.toLowerCase().includes(value));
    });
  });
});
