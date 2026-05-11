document.addEventListener("DOMContentLoaded", () => {
  const typeInputs = document.querySelectorAll("[data-registration-type]");
  const sections = document.querySelectorAll("[data-registration-section]");

  const syncRegistrationType = () => {
    const selectedType = document.querySelector("[data-registration-type]:checked")?.value || "student";
    typeInputs.forEach((input) => {
      input.closest(".file-drop")?.classList.toggle("is-active", input.checked);
    });
    sections.forEach((section) => {
      const isActive = section.dataset.registrationSection === selectedType;
      section.classList.toggle("d-none", !isActive);
      section.querySelectorAll("input, select, textarea").forEach((field) => {
        field.disabled = !isActive;
        field.required = isActive && field.dataset.requiredIf === selectedType;
      });
    });
  };

  typeInputs.forEach((input) => input.addEventListener("change", syncRegistrationType));
  syncRegistrationType();

  document.querySelectorAll(".file-drop input[type='file']").forEach((input) => {
    input.addEventListener("change", () => {
      const wrapper = input.closest(".file-drop");
      const label = wrapper.querySelector("[data-file-label]");
      wrapper.classList.toggle("is-active", input.files.length > 0);
      if (label) label.textContent = input.files.length ? input.files[0].name : label.dataset.defaultLabel;
    });
  });
});
