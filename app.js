const DATA_URL = "./data/dashboard_master.csv";
const RAW_IMAGE_BASE = "./assets/si_images_20bar_padded/test/";
const OVERLAY_IMAGE_BASE = "./assets/si_xai_final/raw_overlay/";

let masterRows = [];
let filteredRows = [];

const splitFilter = document.getElementById("splitFilter");
const contractFilter = document.getElementById("contractFilter");
const xaiFilter = document.getElementById("xaiFilter");
const signalFilter = document.getElementById("signalFilter");
const confidenceFilter = document.getElementById("confidenceFilter");
const dateFromInput = document.getElementById("dateFrom");
const dateToInput = document.getElementById("dateTo");
const resetFiltersBtn = document.getElementById("resetFiltersBtn");
const sampleSelect = document.getElementById("sampleSelect");
const sampleMeta = document.getElementById("sampleMeta");
const dataTableBody = document.getElementById("dataTableBody");

const kpiRows = document.getElementById("kpiRows");
const kpiAccuracy = document.getElementById("kpiAccuracy");
const kpiPup = document.getElementById("kpiPup");
const kpiForwardReturn = document.getElementById("kpiForwardReturn");

const rawImage = document.getElementById("rawImage");
const overlayImage = document.getElementById("overlayImage");
const rawImageFallback = document.getElementById("rawImageFallback");
const overlayImageFallback = document.getElementById("overlayImageFallback");

function toNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function toBoolean(value) {
  if (typeof value === "boolean") return value;
  if (value === "true" || value === "TRUE" || value === "True") return true;
  if (value === "false" || value === "FALSE" || value === "False") return false;
  return null;
}

function safeString(value) {
  return value === null || value === undefined ? "" : String(value);
}

function basename(pathValue) {
  const value = safeString(pathValue);
  if (!value) return "";
  const parts = value.split("/");
  return parts[parts.length - 1];
}

function uniqueSorted(values) {
  return [...new Set(values.filter(v => v !== null && v !== undefined && v !== ""))].sort();
}

function normalizeRow(row) {
  const label = row.label !== undefined ? toNumber(row.label) : toNumber(row.label_20);
  const pred =
    row.pred !== undefined
      ? toNumber(row.pred)
      : row.cnn_pred !== undefined
      ? toNumber(row.cnn_pred)
      : row.cnn_pred_thr_050 !== undefined
      ? toNumber(row.cnn_pred_thr_050)
      : null;

  const imageFilename =
    row.image_filename !== undefined && row.image_filename !== ""
      ? safeString(row.image_filename)
      : basename(row.image_path);

  const overlayFilename =
    row.gradcam_raw_path !== undefined && row.gradcam_raw_path !== ""
      ? basename(row.gradcam_raw_path)
      : imageFilename;

  const xaiBucket =
    row.xai_bucket !== undefined && row.xai_bucket !== ""
      ? safeString(row.xai_bucket)
      : row.xai_quality_bucket !== undefined
      ? safeString(row.xai_quality_bucket)
      : "";

  const forwardReturn =
    row.forward_return !== undefined ? toNumber(row.forward_return) : toNumber(row.forward_return_20);

  const isCorrect =
    row.is_correct !== undefined && row.is_correct !== ""
      ? toBoolean(row.is_correct)
      : label !== null && pred !== null
      ? label === pred
      : null;

  const anchorTime = safeString(row.anchor_time);
  const tradeDate =
    row.trade_date !== undefined && row.trade_date !== ""
      ? safeString(row.trade_date)
      : anchorTime
      ? anchorTime.slice(0, 10)
      : "";

  return {
    sample_id: toNumber(row.sample_id),
    anchor_idx: toNumber(row.anchor_idx),
    anchor_time: anchorTime,
    trade_date: tradeDate,
    contract: safeString(row.contract),
    split: safeString(row.split),
    label: label,
    pred: pred,
    cnn_p_up: toNumber(row.cnn_p_up),
    forward_return: forwardReturn,
    xai_quality_score: toNumber(row.xai_quality_score),
    xai_bucket: xaiBucket,
    signal_bucket: safeString(row.signal_bucket),
    confidence_bucket: safeString(row.confidence_bucket),
    image_filename: imageFilename,
    overlay_filename: overlayFilename,
    is_correct: isCorrect,
    error_type: safeString(row.error_type)
  };
}

function formatPercent(value, decimals = 1) {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  return `${(value * 100).toFixed(decimals)}%`;
}

function formatNumber(value, decimals = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  return Number(value).toFixed(decimals);
}

function fillSelect(selectEl, options) {
  selectEl.innerHTML = "";
  const allOption = document.createElement("option");
  allOption.value = "all";
  allOption.textContent = "All";
  selectEl.appendChild(allOption);

  options.forEach(value => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    selectEl.appendChild(option);
  });
}

function initializeFilters(rows) {
  fillSelect(splitFilter, uniqueSorted(rows.map(r => r.split)));
  fillSelect(contractFilter, uniqueSorted(rows.map(r => r.contract)));
  fillSelect(xaiFilter, uniqueSorted(rows.map(r => r.xai_bucket)));
  fillSelect(signalFilter, uniqueSorted(rows.map(r => r.signal_bucket)));
  fillSelect(confidenceFilter, uniqueSorted(rows.map(r => r.confidence_bucket)));

  const dates = uniqueSorted(rows.map(r => r.trade_date));
  if (dates.length > 0) {
    dateFromInput.value = dates[0];
    dateToInput.value = dates[dates.length - 1];
    dateFromInput.min = dates[0];
    dateFromInput.max = dates[dates.length - 1];
    dateToInput.min = dates[0];
    dateToInput.max = dates[dates.length - 1];
  }
}

function applyFilters() {
  const splitValue = splitFilter.value;
  const contractValue = contractFilter.value;
  const xaiValue = xaiFilter.value;
  const signalValue = signalFilter.value;
  const confidenceValue = confidenceFilter.value;
  const dateFrom = dateFromInput.value;
  const dateTo = dateToInput.value;

  filteredRows = masterRows.filter(row => {
    if (splitValue !== "all" && row.split !== splitValue) return false;
    if (contractValue !== "all" && row.contract !== contractValue) return false;
    if (xaiValue !== "all" && row.xai_bucket !== xaiValue) return false;
    if (signalValue !== "all" && row.signal_bucket !== signalValue) return false;
    if (confidenceValue !== "all" && row.confidence_bucket !== confidenceValue) return false;
    if (dateFrom && row.trade_date < dateFrom) return false;
    if (dateTo && row.trade_date > dateTo) return false;
    return true;
  });

  filteredRows.sort((a, b) => {
    if (a.anchor_time < b.anchor_time) return -1;
    if (a.anchor_time > b.anchor_time) return 1;
    if ((a.anchor_idx ?? 0) < (b.anchor_idx ?? 0)) return -1;
    if ((a.anchor_idx ?? 0) > (b.anchor_idx ?? 0)) return 1;
    return 0;
  });

  renderDashboard();
}

function renderKpis(rows) {
  const rowCount = rows.length;
  const validAccRows = rows.filter(r => r.label !== null && r.pred !== null);
  const accuracy =
    validAccRows.length > 0
      ? validAccRows.filter(r => r.label === r.pred).length / validAccRows.length
      : null;

  const pUpRows = rows.filter(r => r.cnn_p_up !== null);
  const avgPup =
    pUpRows.length > 0
      ? pUpRows.reduce((sum, r) => sum + r.cnn_p_up, 0) / pUpRows.length
      : null;

  const returnRows = rows.filter(r => r.forward_return !== null);
  const avgReturn =
    returnRows.length > 0
      ? returnRows.reduce((sum, r) => sum + r.forward_return, 0) / returnRows.length
      : null;

  kpiRows.textContent = String(rowCount);
  kpiAccuracy.textContent = accuracy === null ? "N/A" : formatPercent(accuracy, 1);
  kpiPup.textContent = avgPup === null ? "N/A" : formatPercent(avgPup, 1);
  kpiForwardReturn.textContent = avgReturn === null ? "N/A" : formatPercent(avgReturn, 3);
}

function renderProbabilityChart(rows) {
  const chartRows = rows.filter(r => r.anchor_time && r.cnn_p_up !== null);
  const x = chartRows.map(r => r.anchor_time);
  const y = chartRows.map(r => r.cnn_p_up);

  Plotly.newPlot(
    "probabilityChart",
    [
      {
        x,
        y,
        mode: "lines+markers",
        type: "scatter",
        name: "P(up)"
      }
    ],
    {
      margin: { t: 20, r: 20, b: 50, l: 50 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { color: "#e5e7eb" },
      xaxis: { title: "Time", gridcolor: "#374151" },
      yaxis: { title: "P(up)", gridcolor: "#374151", range: [0, 1] }
    },
    { responsive: true, displayModeBar: false }
  );
}

function renderConfusionChart(rows) {
  const counts = {
    "0,0": 0,
    "0,1": 0,
    "1,0": 0,
    "1,1": 0
  };

  rows.forEach(r => {
    if (r.label !== null && r.pred !== null) {
      counts[`${r.label},${r.pred}`] += 1;
    }
  });

  const z = [
    [counts["0,0"], counts["0,1"]],
    [counts["1,0"], counts["1,1"]]
  ];

  Plotly.newPlot(
    "confusionChart",
    [
      {
        z,
        x: ["Pred 0", "Pred 1"],
        y: ["True 0", "True 1"],
        type: "heatmap",
        text: z,
        texttemplate: "%{text}",
        showscale: false
      }
    ],
    {
      margin: { t: 20, r: 20, b: 40, l: 60 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { color: "#e5e7eb" }
    },
    { responsive: true, displayModeBar: false }
  );
}

function renderContractChart(rows) {
  const grouped = {};
  rows.forEach(r => {
    if (!r.contract || r.label === null || r.pred === null) return;
    if (!grouped[r.contract]) grouped[r.contract] = { total: 0, correct: 0 };
    grouped[r.contract].total += 1;
    if (r.label === r.pred) grouped[r.contract].correct += 1;
  });

  const contracts = Object.keys(grouped).sort();
  const accuracies = contracts.map(c => (grouped[c].correct / grouped[c].total) * 100);
  const texts = contracts.map(c => String(grouped[c].total));

  Plotly.newPlot(
    "contractChart",
    [
      {
        x: contracts,
        y: accuracies,
        type: "bar",
        text: texts,
        textposition: "outside"
      }
    ],
    {
      margin: { t: 20, r: 20, b: 50, l: 50 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { color: "#e5e7eb" },
      xaxis: { title: "Contract", gridcolor: "#374151" },
      yaxis: { title: "Accuracy (%)", gridcolor: "#374151" }
    },
    { responsive: true, displayModeBar: false }
  );
}

function renderSignalChart(rows) {
  const grouped = {};
  rows.forEach(r => {
    if (!r.signal_bucket) return;
    grouped[r.signal_bucket] = (grouped[r.signal_bucket] || 0) + 1;
  });

  const names = Object.keys(grouped);
  const values = names.map(name => grouped[name]);

  Plotly.newPlot(
    "signalChart",
    [
      {
        x: names,
        y: values,
        type: "bar"
      }
    ],
    {
      margin: { t: 20, r: 20, b: 70, l: 50 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { color: "#e5e7eb" },
      xaxis: { title: "Signal bucket", gridcolor: "#374151" },
      yaxis: { title: "Rows", gridcolor: "#374151" }
    },
    { responsive: true, displayModeBar: false }
  );
}

function renderXaiChart(rows) {
  const grouped = {};
  rows.forEach(r => {
    if (!r.xai_bucket) return;
    grouped[r.xai_bucket] = (grouped[r.xai_bucket] || 0) + 1;
  });

  const labels = Object.keys(grouped);
  const values = labels.map(label => grouped[label]);

  Plotly.newPlot(
    "xaiChart",
    [
      {
        labels,
        values,
        type: "pie",
        textinfo: "label+percent"
      }
    ],
    {
      margin: { t: 20, r: 20, b: 20, l: 20 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { color: "#e5e7eb" },
      showlegend: false
    },
    { responsive: true, displayModeBar: false }
  );
}

function renderReturnChart(rows) {
  const values = rows.filter(r => r.forward_return !== null).map(r => r.forward_return);

  Plotly.newPlot(
    "returnChart",
    [
      {
        x: values,
        type: "histogram",
        nbinsx: 40
      }
    ],
    {
      margin: { t: 20, r: 20, b: 50, l: 50 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { color: "#e5e7eb" },
      xaxis: { title: "Forward return", gridcolor: "#374151" },
      yaxis: { title: "Rows", gridcolor: "#374151" }
    },
    { responsive: true, displayModeBar: false }
  );
}

function renderSampleOptions(rows) {
  sampleSelect.innerHTML = "";

  if (rows.length === 0) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "No rows available";
    sampleSelect.appendChild(option);
    sampleMeta.textContent = "";
    renderImages(null);
    return;
  }

  rows.forEach((row, index) => {
    const option = document.createElement("option");
    option.value = String(index);
    const parts = [
      String(index + 1),
      row.anchor_time || "",
      row.contract || "",
      row.anchor_idx !== null ? `idx ${row.anchor_idx}` : ""
    ].filter(Boolean);
    option.textContent = parts.join(" | ");
    sampleSelect.appendChild(option);
  });

  sampleSelect.value = "0";
  renderSelectedSample();
}

function renderSelectedSample() {
  if (filteredRows.length === 0) {
    sampleMeta.textContent = "";
    renderImages(null);
    return;
  }

  const index = Number(sampleSelect.value || 0);
  const row = filteredRows[index];

  sampleMeta.textContent = [
    `sample_id: ${row.sample_id ?? "N/A"}`,
    `anchor_idx: ${row.anchor_idx ?? "N/A"}`,
    `anchor_time: ${row.anchor_time || "N/A"}`,
    `trade_date: ${row.trade_date || "N/A"}`,
    `contract: ${row.contract || "N/A"}`,
    `split: ${row.split || "N/A"}`,
    `label: ${row.label ?? "N/A"}`,
    `pred: ${row.pred ?? "N/A"}`,
    `cnn_p_up: ${row.cnn_p_up !== null ? row.cnn_p_up.toFixed(6) : "N/A"}`,
    `forward_return: ${row.forward_return !== null ? row.forward_return.toFixed(6) : "N/A"}`,
    `xai_bucket: ${row.xai_bucket || "N/A"}`,
    `signal_bucket: ${row.signal_bucket || "N/A"}`,
    `confidence_bucket: ${row.confidence_bucket || "N/A"}`,
    `is_correct: ${row.is_correct === null ? "N/A" : row.is_correct}`,
    `error_type: ${row.error_type || "N/A"}`
  ].join("\n");

  renderImages(row);
}

function setImage(imgEl, fallbackEl, src, missingText) {
  imgEl.style.display = "none";
  imgEl.removeAttribute("src");
  fallbackEl.textContent = "";

  if (!src) {
    fallbackEl.textContent = missingText;
    return;
  }

  imgEl.onload = () => {
    imgEl.style.display = "block";
    fallbackEl.textContent = "";
  };

  imgEl.onerror = () => {
    imgEl.style.display = "none";
    fallbackEl.textContent = missingText;
  };

  imgEl.src = src;
}

function renderImages(row) {
  if (!row) {
    setImage(rawImage, rawImageFallback, "", "No image");
    setImage(overlayImage, overlayImageFallback, "", "No overlay");
    return;
  }

  const rawSrc = row.image_filename ? `${RAW_IMAGE_BASE}${row.image_filename}` : "";
  const overlaySrc = row.overlay_filename ? `${OVERLAY_IMAGE_BASE}${row.overlay_filename}` : "";

  setImage(rawImage, rawImageFallback, rawSrc, "Raw image not found");
  setImage(overlayImage, overlayImageFallback, overlaySrc, "Overlay image not found");
}

function renderTable(rows) {
  dataTableBody.innerHTML = "";

  if (rows.length === 0) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 15;
    td.className = "empty-state";
    td.textContent = "No rows match the selected filters.";
    tr.appendChild(td);
    dataTableBody.appendChild(tr);
    return;
  }

  rows.slice(0, 200).forEach(row => {
    const tr = document.createElement("tr");
    const values = [
      row.sample_id,
      row.anchor_idx,
      row.anchor_time,
      row.trade_date,
      row.contract,
      row.split,
      row.label,
      row.pred,
      row.cnn_p_up !== null ? row.cnn_p_up.toFixed(6) : "",
      row.forward_return !== null ? row.forward_return.toFixed(6) : "",
      row.xai_bucket,
      row.signal_bucket,
      row.confidence_bucket,
      row.is_correct,
      row.error_type
    ];

    values.forEach(value => {
      const td = document.createElement("td");
      td.textContent = value === null || value === undefined ? "" : String(value);
      tr.appendChild(td);
    });

    dataTableBody.appendChild(tr);
  });
}

function renderDashboard() {
  renderKpis(filteredRows);
  renderProbabilityChart(filteredRows);
  renderConfusionChart(filteredRows);
  renderContractChart(filteredRows);
  renderSignalChart(filteredRows);
  renderXaiChart(filteredRows);
  renderReturnChart(filteredRows);
  renderSampleOptions(filteredRows);
  renderTable(filteredRows);
}

function resetFilters() {
  splitFilter.value = "all";
  contractFilter.value = "all";
  xaiFilter.value = "all";
  signalFilter.value = "all";
  confidenceFilter.value = "all";

  const dates = uniqueSorted(masterRows.map(r => r.trade_date));
  if (dates.length > 0) {
    dateFromInput.value = dates[0];
    dateToInput.value = dates[dates.length - 1];
  }

  applyFilters();
}

function attachEvents() {
  [splitFilter, contractFilter, xaiFilter, signalFilter, confidenceFilter, dateFromInput, dateToInput].forEach(el => {
    el.addEventListener("change", applyFilters);
  });

  resetFiltersBtn.addEventListener("click", resetFilters);
  sampleSelect.addEventListener("change", renderSelectedSample);
}

function loadData() {
  Papa.parse(DATA_URL, {
    download: true,
    header: true,
    skipEmptyLines: true,
    complete: (results) => {
      masterRows = results.data.map(normalizeRow).filter(row => row.image_filename !== "");
      initializeFilters(masterRows);
      attachEvents();
      applyFilters();
    },
    error: (error) => {
      console.error(error);
      alert("Failed to load data/dashboard_master.csv");
    }
  });
}

loadData();
