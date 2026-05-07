document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".alert[data-auto-dismiss]").forEach((alertEl) => {
    setTimeout(() => {
      const alert = bootstrap.Alert.getOrCreateInstance(alertEl);
      alert.close();
    }, 5000);
  });
});
