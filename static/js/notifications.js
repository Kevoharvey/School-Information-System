document.addEventListener("DOMContentLoaded", () => {
  document.querySelector("#markAllRead")?.addEventListener("click", async () => {
    await fetch("/notifications/mark-read", { method: "POST" });
    document.querySelectorAll("[data-unread]").forEach((card) => card.classList.remove("border-primary"));
  });
});
