const chicagoFormatter = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/Chicago",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

function chicagoDate(instant = new Date()) {
  const parts = Object.fromEntries(
    chicagoFormatter.formatToParts(instant).map(({ type, value }) => [type, value]),
  );
  return `${parts.year}-${parts.month}-${parts.day}`;
}

function shiftDate(isoDate, days) {
  const value = new Date(`${isoDate}T12:00:00Z`);
  value.setUTCDate(value.getUTCDate() + days);
  return value.toISOString().slice(0, 10);
}

function showError(message) {
  const feedback = document.getElementById("feedback");
  feedback.textContent = message;
  feedback.classList.remove("hidden");
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof payload?.detail === "string" ? payload.detail : null;
    throw new Error(detail || `Request failed (${response.status}).`);
  }
  return payload;
}

async function saveForm(form, url, method, payload) {
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  try {
    await apiRequest(url, { method, body: JSON.stringify(payload) });
    window.location.reload();
  } catch (error) {
    showError(error.message);
    button.disabled = false;
  }
}

document.querySelectorAll("[data-daily-form]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const today = chicagoDate();
    if (today !== form.dataset.logDate) {
      window.location.reload();
      return;
    }

    const field = form.dataset.field;
    const rawValue = new FormData(form).get(field);
    const value = form.dataset.kind === "boolean" ? rawValue === "true" : Number(rawValue);
    const exists = form.dataset.exists === "true";
    const url = exists ? `${form.dataset.endpoint}/${today}` : form.dataset.endpoint;
    const payload = exists ? { [field]: value } : { [field]: value, log_date: today };
    saveForm(form, url, exists ? "PATCH" : "POST", payload);
  });
});

document.getElementById("vitamin-dose-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const vitaminId = Number(new FormData(form).get("vitamin_id"));
  saveForm(form, "/vitamin-logs", "POST", { vitamin_id: vitaminId });
});

document.getElementById("vitamin-create-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const values = new FormData(form);
  saveForm(form, "/vitamins", "POST", {
    name: values.get("name"),
    dose_amount: Number(values.get("dose_amount")),
    dose_unit: values.get("dose_unit"),
    brand: values.get("brand") || null,
  });
});

function renderHistory(target, entries, field, kind, unit = "") {
  target.replaceChildren();
  if (entries.length === 0) {
    target.textContent = "No entries in this range.";
    return;
  }

  const recent = entries.slice(-14).reverse();
  const maxValue = Math.max(1, ...recent.map((entry) => Number(entry[field])));
  const list = document.createElement("ul");
  list.className = "space-y-3";

  for (const entry of recent) {
    const item = document.createElement("li");
    item.className = "border-b border-slate-100 pb-3 last:border-0 last:pb-0";
    const line = document.createElement("div");
    line.className = "flex items-center justify-between gap-3";
    const date = document.createElement("time");
    date.dateTime = entry.log_date;
    date.textContent = entry.log_date;
    const value = document.createElement("span");
    value.className = "font-medium text-slate-900";
    value.textContent = kind === "boolean"
      ? (entry[field] ? "Yes" : "No")
      : `${entry[field]}${unit}`;
    line.append(date, value);
    item.append(line);

    if (kind === "bar") {
      const track = document.createElement("div");
      track.className = "mt-2 h-2 overflow-hidden rounded-full bg-slate-100";
      const fill = document.createElement("div");
      fill.className = "h-full rounded-full bg-teal-600";
      fill.style.width = `${Math.max(4, Number(entry[field]) / maxValue * 100)}%`;
      track.append(fill);
      item.append(track);
    }
    list.append(item);
  }
  target.append(list);
}

async function loadHistory(targetId, endpoint, field, kind, unit, query) {
  const target = document.getElementById(targetId);
  try {
    const entries = await apiRequest(`${endpoint}?${query}`);
    renderHistory(target, entries, field, kind, unit);
  } catch (error) {
    target.textContent = `Could not load history: ${error.message}`;
  }
}

async function loadVitaminHistory(query) {
  const target = document.getElementById("vitamins-history");
  try {
    const logs = await apiRequest(`/vitamin-logs?${query}`);
    const counts = new Map();
    for (const log of logs) {
      const date = chicagoDate(new Date(log.taken_at));
      counts.set(date, (counts.get(date) || 0) + 1);
    }
    const entries = [...counts.entries()]
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([log_date, doses]) => ({ log_date, doses }));
    renderHistory(target, entries, "doses", "bar", " dose(s)");
  } catch (error) {
    target.textContent = `Could not load history: ${error.message}`;
  }
}

const today = chicagoDate();
const query = new URLSearchParams({ start: shiftDate(today, -29), end: today });
loadVitaminHistory(query);
loadHistory("weight-history", "/weight", "weight_lbs", "bar", " lb", query);
loadHistory("protein-history", "/protein", "hit_goal", "boolean", "", query);
loadHistory("lift-history", "/lift", "completed", "boolean", "", query);
loadHistory("sleep-history", "/sleep", "hours_slept", "bar", " hr", query);
