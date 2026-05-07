document.addEventListener("DOMContentLoaded", () => {
  const password = document.querySelector("#password");
  const confirm = document.querySelector("#confirm_password");
  const form = document.querySelector("#register-form");
  form?.addEventListener("submit", (event) => {
    if (password.value !== confirm.value) {
      event.preventDefault();
      confirm.setCustomValidity("Passwords do not match.");
      confirm.reportValidity();
    } else {
      confirm.setCustomValidity("");
    }
  });
});
