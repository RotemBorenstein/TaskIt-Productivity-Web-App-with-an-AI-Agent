// static/main/js/stats.js
// Very simple version: fetch data, draw a line chart, allow day/week/month switch.

document.addEventListener("DOMContentLoaded", function () {
  // 1) Grab elements
  var canvas = document.getElementById("completionRateChart");
  if (!canvas) return; // If this page doesn't have the chart, do nothing.
  var ctx = canvas.getContext("2d");
  var completionRateChartRadios = document.querySelectorAll('input[name="granularity"]');

  var completedCanvas = document.getElementById("completedTasksChart");
  var completedCtx = completedCanvas ? completedCanvas.getContext("2d") : null;
  var completedChart = null;


  // Keep a reference to the current chart so we can replace it
  var chart = null;

  // Load data from API and render
  function loadCompletionRate(granularity) {
    // Example: /api/stats/completion-rate/?granularity=week
    fetch("/api/stats/completion-rate/?granularity=" + encodeURIComponent(granularity), {
      credentials: "same-origin"
    })
      .then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.json();
      })
      .then(function (rows) {
        // rows is an array of objects like:
        // { date, label, created, completed, completion_rate }

        var labels = rows.map(function (r) { return r.label || r.date; });
        var rates  = rows.map(function (r) { return r.completion_rate || 0; });

        // Destroy old chart if it exists
        if (chart) chart.destroy();
        var label, x_text
        if (granularity === "week") {
          label = "Completion rate (weekly)"
          x_text = "week"
        }
        else if (granularity === "month"){
          label = "Completion rate (monthly)"
          x_text = "month"
        }
        else{
          label = "Completion rate (daily)"
          x_text = 'day'
        }

        chart = new Chart(ctx, {
          type: "line",
          data: {
            labels: labels,
            datasets: [{
              label: label,
              data: rates,
              borderWidth: 2,
              tension: 0.3,
              pointRadius: 3
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: {
                min: 0,
                max: 100,
                title: { display: true, text: "Completion rate (%)" },
                ticks: {
                  // Show 0–100 with a % sign
                  callback: function (value) { return value + "%"; }
                }
              },
              x: {
                title: {
                  display: true,
                  text: x_text
                }
              }
            }
          }
        });
      })
      .catch(function (err) {
        console.error(err);
        alert("Could not load stats. Please try again.");
      });
  }

  function loadCompletedTasks(){
    fetch("/api/stats/completed_tasks/", {credentials: "same-origin"})
        .then(function(res){
          return res.json()
        })
        .then(function(rows){
          var labels = rows.map(function(r){return r[0]});
          var counts = rows.map(function(r){return r[1]});
          if (window.completedChart) window.completedChart.destroy();
          var ctx = document.getElementById("completedTasksChart").getContext("2d");
        window.completedChart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: labels,
          datasets: [{
            label: "Most completed daily tasks",
            data: counts
          }]
        },
        options: {
          indexAxis: "y", // makes bars horizontal
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            tooltip: {
              callbacks: {
                label: function (context) {
                  let task = context.label;
                  let value = context.raw;
                  return "Completions: " + value;
                }
              }
            }
          },
          scales: {
            x: {
              beginAtZero: true,
              title: { display: true, text: "Completions" },
              ticks: {stepSize: 1}
            }
          }
        }
      });
    })
    .catch(function (err) {
      console.error("Error loading completed tasks chart:", err);
    });
  }

  function loadPerTaskCompletion(granularity){
    fetch("/api/stats/api_per_task_completion_rate/?granularity=" + encodeURIComponent(granularity), {
      credentials: 'same-origin'
    }).then(function (res){
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    }).then(function(rows){
      var labels = rows.map(function(r){ return r['task']});
      var values = rows.map(function(r){ return r['rate']});
      var isCount = (granularity === "count");
      var label = "Completion (%)"
      var x_text = "Completion (%)"
      if (granularity === "count") {
          label = "Completion"
          x_text = "Completion"
        }
      if (window.perTaskChart) window.perTaskChart.destroy();
          var ctx = document.getElementById("perTaskCompletionChart").getContext("2d");
          window.perTaskChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: isCount ? "Missed completions" : "Completion rate (%)",
          data: values,
          minBarLength: 3,
          backgroundColor: values.map(v => v === 0 ? "rgba(200,200,200,0.6)" : "rgba(54,162,235,0.8)"),
          borderColor: values.map(v => v === 0 ? "rgba(200,200,200,1)" : "rgba(54,162,235,1)"),
        borderWidth: 1
}]
      },
      options: {
        indexAxis: "y", // horizontal bars
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label: function (context) {
                var v = context.raw;
                return isCount ? ("Misses: " + v) : ("Completion: " + v + "%");
              }
            }
          }
        },
        scales: {
          x: isCount
            ? { beginAtZero: true, title: { display: true, text: "Count" } }
            : {
                min: 0, max: 100,
                title: { display: true, text: "Completion rate (%)" },
                ticks: { callback: function (v) { return v + "%"; } }
              }
        }
      }
    });
      })
      .catch(function (err) {
        console.error(err);
        alert("Could not load stats. Please try again.");
      });
  }


  // When the user switches week/month or percentage/count, reload
  completionRateChartRadios.forEach(function (r) {
    r.addEventListener("change", function (e) {
      if (e.target.checked) {
        loadCompletionRate(e.target.value);
      }
    });
  });

  var perTaskRadios = document.querySelectorAll('input[name="granularityPerTask"]');
  perTaskRadios.forEach(function (r) {
  r.addEventListener("change", function (e) {
    if (e.target.checked) {
      loadPerTaskCompletion(e.target.value);
    }
  });
});


  // Initial load
  var initial = document.querySelector('input[name="granularity"]:checked');
  var initialPerTask = document.querySelector('input[name="granularityPerTask"]:checked');

  loadCompletionRate(initial ? initial.value : "day");
  loadCompletedTasks();
  loadPerTaskCompletion(initialPerTask ? initialPerTask.value : "count");
});
