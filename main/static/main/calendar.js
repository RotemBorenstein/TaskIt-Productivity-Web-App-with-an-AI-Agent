(function () {
  const $ = (s, r = document) => r.querySelector(s);

  // CSRF helper for Django
  function getCookie(name) {
    const m = document.cookie.match('(^|;)\s*' + name + '\s*=\s*([^;]+)');
    return m ? decodeURIComponent(m.pop()) : null;
  }
  const CSRF = () => ({ "X-CSRFToken": getCookie("csrftoken") });

  // ======== MODAL ELEMENTS ========
  const modal = $("#event-modal");
  const backdrop = $("#event-modal-backdrop");
  const modalClose = $("#event-modal-close");
  const form = $("#event-form");
  const titleIn = $("#ev-title");
  const descIn = $("#ev-desc");
  const startIn = $("#ev-start");
  const endIn = $("#ev-end");
  const allDayIn = $("#ev-all-day");
  const cancelBtn = $("#event-cancel");

  // For Date → datetime-local value (YYYY-MM-DDTHH:MM)
  function toLocalInputValue(date) {
    const d = (date instanceof Date) ? date : new Date(date);
    const local = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 16);
  }

  function setInputValueFromAny(inputEl, valueAny) {
    if (typeof valueAny === 'string') {
      // Expect an ISO-ish string: YYYY-MM-DDTHH:MM[:SS][±HH:MM|Z]
      // We only need YYYY-MM-DDTHH:MM for datetime-local
      const m = valueAny.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/);
      inputEl.value = m ? `${m[1]}T${m[2]}` : toLocalInputValue(valueAny);
    } else {
      inputEl.value = toLocalInputValue(valueAny);
    }
  }

  function openModal(initial) {
    titleIn.value = "";
    descIn.value = "";
    allDayIn.checked = !!initial?.allDay;

    const now = new Date();
    const startAny = initial?.start ?? now;
    const endAny = initial?.end ?? new Date(now.getTime() + 60 * 60 * 1000);

    setInputValueFromAny(startIn, startAny);
    setInputValueFromAny(endIn, endAny);

    backdrop.classList.remove("hidden");
    modal.classList.remove("hidden");
  }
  function closeModal() {
    modal.classList.add("hidden");
    backdrop.classList.add("hidden");
  }
  modalClose?.addEventListener("click", closeModal);
  cancelBtn?.addEventListener("click", closeModal);
  backdrop?.addEventListener("click", closeModal);

  async function submitEvent() {
    const payload = {
      title: titleIn.value.trim(),
      description: descIn.value.trim(),
      start: new Date(startIn.value).toISOString(),
      end: new Date(endIn.value).toISOString(),
      allDay: allDayIn.checked,
    };
    const r = await fetch("/api/events/", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...CSRF() },
      credentials: "same-origin",
      body: JSON.stringify(payload),
    });
    if (!r.ok) throw new Error(await r.text() || "Failed creating event");
    return r.json();
  }

  // ======== TASK PANEL ELEMENTS ========
  const panel = $("#day-panel");
  const panelTitle = $("#day-panel-title");
  const panelClose = $("#day-panel-close");
  const dailyList = $("#daily-list");
  const longtermList = $("#longterm-list");

  panelClose?.addEventListener("click", () => panel.classList.add("hidden"));

  async function loadDay(dateISO) {
    const r = await fetch(`/api/tasks/day/?date=${encodeURIComponent(dateISO)}`, { credentials: "same-origin" });
    if (!r.ok) throw new Error("tasks_of_day endpoint not ready");
    return await r.json();
  }

  function renderDaySkeleton(dateISO) {
    if (panelTitle) panelTitle.textContent = new Date(dateISO).toDateString();
    if (dailyList) dailyList.innerHTML = "";
    if (longtermList) longtermList.innerHTML = "";
    panel?.classList.remove("hidden");
  }

  function renderDay(data) {
    if (panelTitle) panelTitle.textContent = new Date(data.date).toDateString();

    // Daily tasks
    if (dailyList) {
      dailyList.innerHTML = "";
      data.daily.forEach(t => {
        const li = document.createElement("li");
        const id = `d-${t.id}`;
        li.innerHTML = `
          <label for="${id}">
            <input type="checkbox" id="${id}" ${t.completed ? "checked" : ""}>
            <span>${t.title}</span>
          </label>
        `;
        const cb = li.querySelector("input");
        cb.addEventListener("change", async () => {
          const method = cb.checked ? "POST" : "DELETE";
          const form = new URLSearchParams({ task_id: t.id, date: data.date });
          const r = await fetch("/api/daily-completions/", {
            method,
            headers: { "Content-Type": "application/x-www-form-urlencoded", ...CSRF() },
            credentials: "same-origin",
            body: form.toString()
          });
          if (!r.ok) { cb.checked = !cb.checked; alert("Failed saving daily completion"); }
        });
        dailyList.appendChild(li);
      });
    }

    // Long-term tasks
    if (longtermList) {
      longtermList.innerHTML = "";
      data.long_term.forEach(t => {
        const li = document.createElement("li");
        const id = `lt-${t.id}`;
        li.innerHTML = `
          <label for="${id}">
            <input type="checkbox" id="${id}" ${t.completed_on_that_day ? "checked" : ""}>
            <span>${t.title}</span>
          </label>
        `;
        const cb = li.querySelector("input");
        cb.addEventListener("change", async () => {
          const method = cb.checked ? "PATCH" : "DELETE";
          const qs = cb.checked ? `?date=${encodeURIComponent(data.date)}` : "";
          const r = await fetch(`/api/tasks/${t.id}/complete/${qs}`, {
            method,
            headers: { ...CSRF() },
            credentials: "same-origin"
          });
          if (!r.ok) { cb.checked = !cb.checked; alert("Failed updating long-term completion"); }
        });
        longtermList.appendChild(li);
      });
    }

    panel?.classList.remove("hidden");
  }

  // ======== CALENDAR INIT ========
  document.addEventListener("DOMContentLoaded", function () {
    const calendarEl = document.getElementById("calendar");
    if (!calendarEl) return;

    const pluginList = [];
    if (window.FullCalendar && FullCalendar.interactionPlugin) {
      pluginList.push(FullCalendar.interactionPlugin);
    }

    const calendar = new FullCalendar.Calendar(calendarEl, {
      ...(pluginList.length ? { plugins: pluginList } : {}),

      initialView: "dayGridMonth",
      headerToolbar: {
        left: "prev,next today addEvent",
        center: "title",
        right: "dayGridMonth,timeGridWeek,timeGridDay"
      },
      customButtons: {
        addEvent: {
          text: "New Event",
          click: () => openModal({ start: new Date(), end: new Date(Date.now() + 60 * 60 * 1000), allDay: false })
        }
      },
      firstDay: 0,
      timeZone: "Asia/Jerusalem",

      selectable: true,
      selectMirror: true,
      selectMinDistance: 2,
      unselectAuto: true,
      selectAllow: function(selectInfo) {
        const vt = calendar.view ? calendar.view.type : 'dayGridMonth';
        return (vt === 'timeGridDay' || vt === 'timeGridWeek') && selectInfo.start < selectInfo.end;
      },
      select: function(info) {
        // Use FullCalendar's own strings (already in calendar's tz)
        openModal({ start: info.startStr, end: info.endStr, allDay: false });
      },

      events: function(fetchInfo, success, failure) {
        const url = `/api/calendar/?start=${encodeURIComponent(fetchInfo.startStr)}&end=${encodeURIComponent(fetchInfo.endStr)}`;
        fetch(url, { credentials: "same-origin" })
          .then(r => r.ok ? r.json() : Promise.reject(new Error("Failed to load events")))
          .then(data => success(data))
          .catch(failure);
      },

      dateClick: async function (info) {
        const vt = calendar.view ? calendar.view.type : 'dayGridMonth';
        if (vt !== 'dayGridMonth') return;
        const isoDate = info.dateStr;
        renderDaySkeleton(isoDate);
        try {
          const data = await loadDay(isoDate);
          renderDay(data);
        } catch {}
      }
    });

    calendar.render();

    form?.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const ev = await submitEvent();
        calendar.addEvent({ id: ev.id, title: ev.title, start: ev.start, end: ev.end, allDay: ev.allDay });
        closeModal();
      } catch (err) {
        alert(err.message || "Failed creating event");
      }
    });
  });
})();