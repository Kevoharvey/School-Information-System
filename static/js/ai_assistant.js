document.addEventListener("DOMContentLoaded", () => {
  const input = document.querySelector("#aiQuestion");
  const send = document.querySelector("#askAiButton");
  const chat = document.querySelector("#chatMessages");
  const sql = document.querySelector("#generatedSql");
  const results = document.querySelector("#queryResults");
  const history = document.querySelector("#chatHistory");
  const newQueryButton = document.querySelector("#newQueryButton");

  const appendMessage = (type, text) => {
    const wrap = document.createElement("div");
    wrap.className = `chat-bubble ${type} mb-3`;
    wrap.textContent = text;
    chat.appendChild(wrap);
    chat.scrollTop = chat.scrollHeight;
  };

  const renderTable = (data) => {
    if (!data.columns || !data.columns.length) {
      results.innerHTML = '<div class="empty-state">No rows returned.</div>';
      return;
    }
    const head = data.columns.map((col) => `<th>${col}</th>`).join("");
    const body = data.rows
      .map((row) => `<tr>${row.map((cell) => `<td>${cell ?? "-"}</td>`).join("")}</tr>`)
      .join("");
    results.innerHTML = `<div class="table-responsive"><table class="table table-sm align-middle"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
  };

  const ask = async () => {
    const question = input.value.trim();
    if (!question) return;
    appendMessage("user", question);
    input.value = "";
    send.disabled = true;
    send.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Asking';
    try {
      const response = await fetch("/ai-assistant/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "AI request failed.");
      appendMessage("ai", data.explanation || "Query completed.");
      sql.textContent = data.sql || "";
      renderTable(data);
      const item = document.createElement("button");
      item.type = "button";
      item.className = "list-group-item list-group-item-action";
      item.textContent = question;
      item.addEventListener("click", () => {
        input.value = question;
        input.focus();
      });
      history.prepend(item);
    } catch (error) {
      appendMessage("ai", error.message);
    } finally {
      send.disabled = false;
      send.innerHTML = '<i class="bi bi-send"></i> Ask AI';
    }
  };

  const resetChat = async () => {
    try {
      await fetch("/ai-assistant/reset", { method: "POST" });
    } catch (_error) {
      // UI reset should still proceed even if reset request fails.
    }
    chat.innerHTML = `
      <div class="text-center mx-auto my-5 intro-narrow">
        <div class="icon-box mx-auto mb-3"><i class="bi bi-stars"></i></div>
        <h2 class="brand-font fw-bold">Ask AI about your school data</h2>
        <p class="text-muted-soft">Generate SQL, view result tables, and discover smart analytics suggestions.</p>
      </div>
    `;
    history.innerHTML = "";
    sql.textContent = "SELECT * FROM Student ORDER BY Student_ID DESC;";
    results.innerHTML = '<div class="empty-state">Ask a question to see results.</div>';
    input.value = "";
    input.focus();
  };

  send?.addEventListener("click", ask);
  input?.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      ask();
    }
  });
  document.querySelectorAll("[data-ai-example]").forEach((button) => {
    button.addEventListener("click", () => {
      input.value = button.dataset.aiExample;
      input.focus();
    });
  });
  newQueryButton?.addEventListener("click", resetChat);
});
