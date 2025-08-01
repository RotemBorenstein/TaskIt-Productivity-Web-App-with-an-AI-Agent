// main/static/main/tasks.js
console.log("tasks.js loaded!");

document.addEventListener("DOMContentLoaded", function () {
  // 1. AJAX "Mark Complete" for all checkboxes
  document.querySelectorAll(".task-checkbox").forEach(function (checkbox) {
    checkbox.addEventListener("change", function () {
      if (!checkbox.checked) return;
      const taskId = checkbox.getAttribute("data-task-id");
      if (!taskId) return;

      // CSRF token retrieval
      function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
          const cookies = document.cookie.split(";");
          for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
            }
          }
        }
        return cookieValue;
      }
      const csrftoken = getCookie("csrftoken");

      // Send AJAX POST to /tasks/complete/
      const data = new URLSearchParams();
      data.append("task_id", taskId);

      fetch("/tasks/complete/", {
        method: "POST",
        headers: {
          "X-CSRFToken": csrftoken,
          "X-Requested-With": "XMLHttpRequest",
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: data,
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            // Fade out and remove the task <li>
            const li = document.getElementById(`task-${taskId}`);
            if (li) {
              li.classList.add("fade-out");
              setTimeout(() => {
                li.remove();
              }, 500);
            }
          } else {
            alert("Failed to complete task: " + (data.error || "Unknown error"));
            checkbox.checked = false;
          }
        })
        .catch(() => {
          alert("Network error: could not mark task as complete.");
          checkbox.checked = false;
        });
    });
  });

  // 2. Show/Hide Add Task Forms for Each Section
  function showForm(formId) {
    document.getElementById(formId).style.display = "block";
    // Optionally close the other form
    if (formId === "daily-form-container") {
      document.getElementById("long-form-container").style.display = "none";
    } else {
      document.getElementById("daily-form-container").style.display = "none";
    }
  }
  function hideForm(formId) {
    document.getElementById(formId).style.display = "none";
  }

  // Show buttons
  var showDailyBtn = document.getElementById("show-daily-form");
  var showLongBtn = document.getElementById("show-long-form");
  if (showDailyBtn) {
    showDailyBtn.onclick = function () {
      showForm("daily-form-container");
    };
  }
  if (showLongBtn) {
    showLongBtn.onclick = function () {
      showForm("long-form-container");
    };
  }

  // Close buttons
  var closeDailyBtn = document.getElementById("close-daily-form");
  var closeLongBtn = document.getElementById("close-long-form");
  if (closeDailyBtn) {
    closeDailyBtn.onclick = function () {
      hideForm("daily-form-container");
    };
  }
  if (closeLongBtn) {
    closeLongBtn.onclick = function () {
      hideForm("long-form-container");
    };
  }
});
