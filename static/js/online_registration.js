document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".file-drop input[type='file']").forEach((input) => {
    input.addEventListener("change", () => {
      const wrapper = input.closest(".file-drop");
      const label = wrapper.querySelector("[data-file-label]");
      wrapper.classList.toggle("is-active", input.files.length > 0);
      if (label) label.textContent = input.files.length ? input.files[0].name : label.dataset.defaultLabel;
    });
  });
});
