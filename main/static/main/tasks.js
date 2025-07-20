// main/static/main/tasks.js

// Wait for the DOM to fully load
document.addEventListener("DOMContentLoaded", function () {
  // Select all checkboxes with class 'task-checkbox'
  document.querySelectorAll(".task-checkbox").forEach(function (checkbox) {
    checkbox.addEventListener("change", function () {
      if (!checkbox.checked) return; // Only handle checking, not unchecking
      const taskId = checkbox.getAttribute("data-task-id");
      if (!taskId) return;

      // Get CSRF token from cookie (standard Django method)
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

      // Prepare data for POST
      const data = new URLSearchParams();
      data.append("task_id", taskId);

      // Send AJAX POST to /tasks/complete/
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
        .catch((error) => {
          alert("Network error: could not mark task as complete.");
          checkbox.checked = false;
        });
    });
  });
});
