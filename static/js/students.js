document.addEventListener("DOMContentLoaded", () => {
  document.querySelector("#studentSearch")?.addEventListener("input", (event) => {
    const value = event.target.value.toLowerCase();
    document.querySelectorAll("[data-student-row]").forEach((row) => {
      row.classList.toggle("d-none", !row.textContent.toLowerCase().includes(value));
    });
  });
});
