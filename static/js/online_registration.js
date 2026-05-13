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

      if (input.files.length > 0) {
        wrapper.classList.remove("border-danger", "border", "border-2");
        const err = wrapper.querySelector(".file-error-msg, .field-error-msg");
        if (err) err.remove();
        input.classList.remove("is-invalid");
      }
    });
  });

  document.querySelectorAll("input, select, textarea").forEach((field) => {
    field.addEventListener("input", () => {
      const wrapper = field.closest(".col-md-4, .col-md-6, .col-12") || field.parentElement;
      
      field.classList.remove("is-invalid");
      if (wrapper.classList.contains("file-drop")) {
        wrapper.classList.remove("border-danger", "border", "border-2");
      }
      const err = wrapper.querySelector(".field-error-msg");
      if (err) err.remove();
    });
    field.addEventListener("change", () => {
      const wrapper = field.closest(".col-md-4, .col-md-6, .col-12") || field.parentElement;
      
      field.classList.remove("is-invalid");
      if (wrapper.classList.contains("file-drop")) {
        wrapper.classList.remove("border-danger", "border", "border-2");
      }
      const err = wrapper.querySelector(".field-error-msg");
      if (err) err.remove();
    });
  });

  document.querySelector("form").addEventListener("submit", (e) => {
    let hasError = false;
    const requiredFields = document.querySelectorAll("input[required]:not([type='file']), select[required], textarea[required]");
    requiredFields.forEach((field) => {
      const wrapper = field.closest(".col-md-4, .col-md-6, .col-12") || field.parentElement;
      
      const oldErr = wrapper.querySelector(".field-error-msg");
      if (oldErr) oldErr.remove();

      let isEmpty = false;
      if (field.tagName === "SELECT") {
        isEmpty = !field.value || field.value === "";
      } else {
        isEmpty = !field.value.trim();
      }

      if (isEmpty) {
        hasError = true;
        field.classList.add("is-invalid");

        const msg = document.createElement("div"); 
        msg.className = "field-error-msg text-danger fw-bold mt-1";
        msg.style.fontSize = "14px";
        msg.innerHTML = '<i class="bi bi-exclamation-circle me-1"></i> Please fill out this field.';

        wrapper.appendChild(msg);
      } else {
        field.classList.remove("is-invalid");
      }
    });
    const requiredFiles = document.querySelectorAll("input[data-file-required][type='file']");
    requiredFiles.forEach((field) => {
      const wrapper = field.closest(".file-drop");
  
      const oldErr = wrapper.querySelector(".field-error-msg");
      if (oldErr) oldErr.remove();

      if (!field.files || field.files.length === 0) {
        hasError = true;
        wrapper.classList.add("border", "border-2", "border-danger");

        const msg = document.createElement("div"); 
        msg.className = "field-error-msg text-danger fw-bold mt-1";
        msg.style.fontSize = "14px";
        msg.innerHTML = '<i class="bi bi-exclamation-circle me-1"></i> Please fill out this field.';

        wrapper.appendChild(msg);
      } else {
        wrapper.classList.remove("border-danger", "border", "border-2");
      }
    });

    if (hasError) {
      e.preventDefault();
    
      const firstError = document.querySelector(".is-invalid, .border-danger");
      if (firstError) {
        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  });
});