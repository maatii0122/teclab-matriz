let payload = null;
let currentRows = [];

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function cleanValue(value) {
  const text = String(value ?? "").replace(/\u00a0/g, " ").trim();
  return text || "";
}

function splitValues(value) {
  const text = cleanValue(value);
  return text ? text.split(",").map((part) => part.trim()).filter(Boolean) : [];
}

function periodValues(value) {
  const text = cleanValue(value).toUpperCase();
  const combined = text.match(/^(\d)A\s*\/\s*(\d)?B$/);
  if (combined) {
    return [`${combined[1]}A`, `${combined[1]}B`];
  }
  return splitValues(text);
}

function uniqueValues(values, split = false) {
  const seen = new Set();
  const result = [];
  values.forEach((value) => {
    const parts = split ? splitValues(value) : [cleanValue(value)];
    parts.forEach((part) => {
      if (part && !seen.has(part)) {
        seen.add(part);
        result.push(part);
      }
    });
  });
  return result;
}

function sortText(value) {
  return cleanValue(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase();
}

function selectedValues(select) {
  return [...select.selectedOptions].map((option) => option.value);
}

function matchesAny(value, selected) {
  if (!selected.length) return true;
  const values = new Set(splitValues(value));
  return selected.some((item) => values.has(item));
}

function matchesPeriod(value, selected) {
  if (!selected.length) return true;
  const values = new Set(periodValues(value));
  return selected.some((item) => values.has(item));
}

function buildCleanMatrix(rows) {
  return [...rows].sort((a, b) => sortText(a.MATERIA).localeCompare(sortText(b.MATERIA)));
}

function buildMetrics(rows) {
  return payload.fields.map((field) => {
    const filled = rows.filter((row) => cleanValue(row[field])).length;
    const missing = rows.length - filled;
    const percent = rows.length ? `${((filled / rows.length) * 100).toFixed(1)}%` : "0.0%";
    return { field, filled, missing, percent };
  });
}

function fillSelect(id, values) {
  const select = $(id);
  select.innerHTML = values
    .sort((a, b) => sortText(a).localeCompare(sortText(b)))
    .map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`)
    .join("");
}

function renderMetrics(container, metrics) {
  container.innerHTML = metrics
    .map(
      (metric) => `
        <article class="metric">
          <span>${escapeHtml(metric.field)}</span>
          <strong>${escapeHtml(metric.percent)}</strong>
          <small>${metric.filled} completados / ${metric.missing} faltantes</small>
        </article>
      `,
    )
    .join("");
}

function renderStats() {
  const stats = payload.stats;
  $("#stats").innerHTML = [
    ["Filas originales", stats.rawRows],
    ["Materias únicas", stats.uniqueSubjects],
    ["Filas matriz limpia", stats.cleanRows],
    ["Carreras", stats.careers],
    ["Períodos", stats.periods],
  ]
    .map(
      ([label, value]) => `
        <article class="metric">
          <span>${label}</span>
          <strong>${Number(value).toLocaleString("es-AR")}</strong>
        </article>
      `,
    )
    .join("");
}

function renderTable(table, rows, columns) {
  if (!rows.length) {
    table.innerHTML = `<tbody><tr><td>No hay resultados para los filtros seleccionados.</td></tr></tbody>`;
    return;
  }

  const head = `<thead><tr>${columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr></thead>`;
  const body = rows
    .map(
      (row) => `
        <tr>
          ${columns.map((column) => `<td>${escapeHtml(row[column])}</td>`).join("")}
        </tr>
      `,
    )
    .join("");
  table.innerHTML = `${head}<tbody>${body}</tbody>`;
}

function renderAuditTable(metrics) {
  const columns = ["Campo", "Completados", "Faltantes", "% Completado"];
  const rows = metrics.map((metric) => ({
    Campo: metric.field,
    Completados: metric.filled,
    Faltantes: metric.missing,
    "% Completado": metric.percent,
  }));
  renderTable($("#auditTable"), rows, columns);
}

function applyFilters() {
  const careers = selectedValues($("#careerFilter"));
  const years = selectedValues($("#yearFilter"));
  const periods = selectedValues($("#periodFilter"));
  const query = cleanValue($("#searchInput").value).toLowerCase();

  const filteredRaw = payload.rawRows.filter(
    (row) =>
      matchesAny(row.CARRERAS, careers) &&
      matchesAny(row.AÑO, years) &&
      matchesPeriod(row.PERIODO, periods),
  );

  currentRows = buildCleanMatrix(filteredRaw).filter((row) => {
    if (!query) return true;
    return cleanValue(row.MATERIA).toLowerCase().includes(query);
  });

  const metrics = buildMetrics(currentRows);
  renderMetrics($("#metrics"), metrics);
  renderTable($("#matrixTable"), currentRows, payload.columns);
  const uniqueSubjects = new Set(currentRows.map((row) => cleanValue(row.MATERIA)).filter(Boolean)).size;
  $("#resultSummary").innerHTML = `<strong>${currentRows.length.toLocaleString("es-AR")}</strong> filas cumplen con los filtros seleccionados (${uniqueSubjects.toLocaleString("es-AR")} materias, sin mezclar información entre filas).`;
}

function downloadCsv(rows, filename) {
  const csv = [
    payload.columns.map(csvCell).join(","),
    ...rows.map((row) => payload.columns.map((column) => csvCell(row[column])).join(",")),
  ].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function csvCell(value) {
  const text = cleanValue(value).replace(/"/g, '""');
  return `"${text}"`;
}

function escapeHtml(value) {
  return cleanValue(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function setupNavigation() {
  $$(".nav-button").forEach((button) => {
    button.addEventListener("click", () => {
      $$(".nav-button").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      $$(".page").forEach((page) => page.classList.remove("active"));
      $(`#${button.dataset.page}Page`).classList.add("active");
      $("#filters").style.display = button.dataset.page === "matrix" ? "block" : "none";
    });
  });
}

async function init() {
  const response = await fetch("./data/matriz.json");
  payload = await response.json();

  fillSelect("#careerFilter", uniqueValues(payload.rawRows.map((row) => row.CARRERAS), true));
  fillSelect("#yearFilter", uniqueValues(payload.rawRows.map((row) => row.AÑO), true));
  fillSelect("#periodFilter", uniqueValues(payload.rawRows.flatMap((row) => periodValues(row.PERIODO)), false));

  renderStats();
  renderMetrics($("#metrics"), payload.metrics);
  renderAuditTable(payload.metrics);
  renderTable($("#cleanTable"), payload.cleanRows, payload.columns);
  setupNavigation();
  applyFilters();

  ["#careerFilter", "#yearFilter", "#periodFilter"].forEach((id) => $(id).addEventListener("change", applyFilters));
  $("#searchInput").addEventListener("input", applyFilters);
  $("#clearFilters").addEventListener("click", () => {
    ["#careerFilter", "#yearFilter", "#periodFilter"].forEach((id) => {
      [...$(id).options].forEach((option) => {
        option.selected = false;
      });
    });
    applyFilters();
  });
  $("#downloadFiltered").addEventListener("click", () => downloadCsv(currentRows, "matriz-ipp-filtrada.csv"));
  $("#downloadClean").addEventListener("click", () => downloadCsv(payload.cleanRows, "matriz-limpia.csv"));
}

init();
