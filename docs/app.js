const state = {
  running: false,
  interval: null,
  generation: 0,
  best: 0,
  avg: 0,
  history: [],
  historyDisplay: [],
  geneFreq: [],
  geneDisplay: [],
  dataset: [],
  librarySize: 300,
  genomeLength: 8,
  maxGenerations: 300,
  targetAccuracy: 0.95,
  minGenerations: 30,
};

const el = {
  appRoot: document.getElementById("appRoot"),
  iconButtons: Array.from(document.querySelectorAll(".icon-btn")),
  slidePanel: document.getElementById("slidePanel"),
  panelSections: Array.from(document.querySelectorAll(".panel-section")),
  librarySize: document.getElementById("librarySize"),
  libraryValue: document.getElementById("libraryValue"),
  populationSize: document.getElementById("populationSize"),
  genomeLength: document.getElementById("genomeLength"),
  generationCount: document.getElementById("generationCount"),
  accuracyTarget: document.getElementById("accuracyTarget"),
  fileInput: document.getElementById("fileInput"),
  datasetInput: document.getElementById("datasetInput"),
  datasetStatus: document.getElementById("datasetStatus"),
  statusMessage: document.getElementById("statusMessage"),
  themePills: Array.from(document.querySelectorAll(".theme-pill")),
  modePills: Array.from(document.querySelectorAll(".mode-pill")),
  askPanel: document.getElementById("askPanel"),
  askInput: document.getElementById("askInput"),
  algoKeyInput: document.getElementById("algoKeyInput"),
  askOutput: document.getElementById("askOutput"),
  askStatus: document.getElementById("askStatus"),
  btnAsk: document.getElementById("btnAsk"),
  btnStart: document.getElementById("btnStart"),
  btnStop: document.getElementById("btnStop"),
  btnSample: document.getElementById("btnSample"),
  fitnessChart: document.getElementById("fitnessChart"),
  geneChart: document.getElementById("geneChart"),
  leaderboard: document.getElementById("leaderboard"),
  genLabel: document.getElementById("genLabel"),
  bestLabel: document.getElementById("bestLabel"),
  trainCards: Array.from(document.querySelectorAll(".train-only")),
  algoKeyBox: document.getElementById("algoKeyBox"),
  btnCopyAlgo: document.getElementById("btnCopyAlgo"),
  btnGhost: document.getElementById("btnGhost"),
  btnNodeMap: document.getElementById("btnNodeMap"),
  nodeMap: document.getElementById("nodeMap"),
  btnCataclysm: document.getElementById("btnCataclysm"),
  mutatorGrid: document.getElementById("mutatorGrid"),
  btnLockAll: document.getElementById("btnLockAll"),
  btnBanAll: document.getElementById("btnBanAll"),
  btnClearLocks: document.getElementById("btnClearLocks"),
  rewindSlider: document.getElementById("rewindSlider"),
  rewindValue: document.getElementById("rewindValue"),
  btnRewind: document.getElementById("btnRewind"),
  btnRewindBoost: document.getElementById("btnRewindBoost"),
  btnExportPy: document.getElementById("btnExportPy"),
  btnExportJs: document.getElementById("btnExportJs"),
  apiToggle: document.getElementById("apiToggle"),
  apiUrl: document.getElementById("apiUrl"),
  formulaPlayback: document.getElementById("formulaPlayback"),
  mapperModal: document.getElementById("mapperModal"),
  mapperGrid: document.getElementById("mapperGrid"),
  btnMapperApply: document.getElementById("btnMapperApply"),
  btnMapperClose: document.getElementById("btnMapperClose"),
  stopOnTarget: document.getElementById("stopOnTarget"),
};

const uiState = {
  ghostLines: false,
  nodeMap: false,
  mutator: new Map(),
};

function setStatus(message) {
  el.statusMessage.textContent = message;
}

function setDatasetStatus() {
  el.datasetStatus.textContent = `${state.dataset.length} samples`;
}

function parseDataset(text) {
  if (!text || !text.trim()) {
    return [];
  }
  const trimmed = text.trim();
  if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
    try {
      const payload = JSON.parse(trimmed);
      if (Array.isArray(payload)) {
        return payload;
      }
      if (payload && typeof payload === "object") {
        return Object.values(payload);
      }
    } catch (err) {
      return [];
    }
  }
  const rows = trimmed.split(/\r?\n/).filter((line) => line.trim());
  return rows.map((line) => line.split(","));
}

function loadDatasetFromText() {
  state.dataset = parseDataset(el.datasetInput.value);
  setDatasetStatus();
  return state.dataset.length > 0;
}

function handleFileUpload(file) {
  const reader = new FileReader();
  reader.onload = () => {
    el.datasetInput.value = reader.result;
    loadDatasetFromText();
    setStatus("Dataset loaded.");
  };
  reader.readAsText(file);
}

function randomInt(max) {
  return Math.floor(Math.random() * max);
}

function randomFormula() {
  const ops = ["add", "sub", "mul", "div", "upper", "lower", "first", "last", "abs"];
  const steps = [];
  for (let i = 0; i < state.genomeLength; i += 1) {
    const paramId = String(randomInt(state.librarySize)).padStart(3, "0");
    const op = ops[randomInt(ops.length)];
    steps.push(`Param_${paramId}:${op}`);
  }
  return steps.join(" -> ");
}

function resizeCanvas(canvas) {
  const parent = canvas.parentElement;
  if (!parent) {
    return null;
  }
  const rect = parent.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const width = Math.max(1, rect.width);
  const height = Math.max(1, rect.height);
  if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
    canvas.width = width * dpr;
    canvas.height = height * dpr;
  }
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, width, height };
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function updateLeaderboard() {
  el.leaderboard.innerHTML = "";
  const topFormula = randomFormula();
  if (el.algoKeyBox) {
    el.algoKeyBox.value = topFormula;
  }
  for (let i = 0; i < 5; i += 1) {
    const row = document.createElement("div");
    row.className = "leaderboard-row";
    const score = Math.max(0, state.best - i * 0.03).toFixed(3);
    const formula = i === 0 ? topFormula : randomFormula();
    row.innerHTML = `<span>#${i + 1}</span><span>${formula}</span><span>${score}</span>`;
    el.leaderboard.appendChild(row);
  }
}

function drawLineChart() {
  const canvas = el.fitnessChart;
  if (!canvas) return;
  const size = resizeCanvas(canvas);
  if (!size) return;
  const { ctx, width, height } = size;
  ctx.clearRect(0, 0, width, height);
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  const padding = { left: 44, right: 12, top: 12, bottom: 24 };
  const plotW = Math.max(1, width - padding.left - padding.right);
  const plotH = Math.max(1, height - padding.top - padding.bottom);
  ctx.strokeStyle = "#2c3342";
  ctx.lineWidth = 1;
  ctx.font = "11px \"JetBrains Mono\", monospace";
  ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--muted");
  for (let i = 0; i <= 4; i += 1) {
    const value = 1 - i / 4;
    const y = padding.top + plotH * (1 - value);
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
    const label = `${Math.round(value * 100)}%`;
    ctx.fillText(label, 6, y + 4);
  }
  ctx.strokeStyle = "#3a4150";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding.left, padding.top);
  ctx.lineTo(padding.left, height - padding.bottom);
  ctx.lineTo(width - padding.right, height - padding.bottom);
  ctx.stroke();
  ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--muted");
  ctx.fillText("Accuracy", padding.left, padding.top - 4);
  ctx.fillText("Generations", width - 110, height - 6);
  for (let i = 0; i <= 4; i += 1) {
    const x = padding.left + plotW * (i / 4);
    const label = Math.round(state.generation * (i / 4));
    ctx.fillText(String(label), x - 6, height - 6);
  }
  if (state.historyDisplay.length < 2) return;
  ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue("--accent-2");
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  const points = state.historyDisplay.map((value, index) => {
    const x = padding.left + (plotW / Math.max(1, state.historyDisplay.length - 1)) * index;
    const y = padding.top + (1 - value) * plotH;
    return { x, y };
  });
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length - 1; i += 1) {
    const midX = (points[i].x + points[i + 1].x) / 2;
    const midY = (points[i].y + points[i + 1].y) / 2;
    ctx.quadraticCurveTo(points[i].x, points[i].y, midX, midY);
  }
  const last = points[points.length - 1];
  ctx.lineTo(last.x, last.y);
  ctx.stroke();
  if (uiState.ghostLines) {
    ctx.strokeStyle = "rgba(120, 140, 170, 0.3)";
    for (let g = 0; g < 5; g += 1) {
      ctx.beginPath();
      state.historyDisplay.forEach((value, index) => {
        const jitter = (Math.random() - 0.5) * 0.05;
        const x = padding.left + (plotW / Math.max(1, state.historyDisplay.length - 1)) * index;
        const y = padding.top + (1 - Math.max(0, Math.min(1, value + jitter))) * plotH;
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
    }
  }
}

function drawBarChart() {
  const canvas = el.geneChart;
  if (!canvas) return;
  const size = resizeCanvas(canvas);
  if (!size) return;
  const { ctx, width, height } = size;
  ctx.clearRect(0, 0, width, height);
  const bars = 10;
  const gap = 8;
  const barWidth = (width - gap * (bars - 1)) / bars;
  for (let i = 0; i < bars; i += 1) {
    const value = state.geneDisplay[i] ?? Math.random();
    const barHeight = value * height;
    ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--accent");
    ctx.fillRect(i * (barWidth + gap), height - barHeight, barWidth, barHeight);
  }
}

function smoothCharts() {
  const target = state.history;
  if (state.historyDisplay.length < target.length) {
    while (state.historyDisplay.length < target.length) {
      state.historyDisplay.push(target[state.historyDisplay.length] ?? 0);
    }
  }
  state.historyDisplay = state.historyDisplay.map((val, idx) => lerp(val, target[idx] ?? val, 0.08));
  const geneTarget = state.geneFreq;
  if (state.geneDisplay.length < geneTarget.length) {
    while (state.geneDisplay.length < geneTarget.length) {
      state.geneDisplay.push(geneTarget[state.geneDisplay.length] ?? 0);
    }
  }
  state.geneDisplay = state.geneDisplay.map((val, idx) => lerp(val, geneTarget[idx] ?? val, 0.14));
}

function populateMutator() {
  if (!el.mutatorGrid) return;
  el.mutatorGrid.innerHTML = "";
  const count = Math.min(60, state.librarySize);
  for (let i = 0; i < count; i += 1) {
    const chip = document.createElement("div");
    chip.className = "mutator-chip";
    const label = `P${String(i + 1).padStart(3, "0")}`;
    chip.textContent = label;
    chip.dataset.param = label;
    chip.addEventListener("click", () => {
      const status = uiState.mutator.get(label) || "free";
      let next = "locked";
      if (status === "locked") next = "banned";
      if (status === "banned") next = "free";
      uiState.mutator.set(label, next);
      chip.classList.toggle("locked", next === "locked");
      chip.classList.toggle("banned", next === "banned");
      if (next === "free") {
        uiState.mutator.delete(label);
      }
    });
    el.mutatorGrid.appendChild(chip);
  }
}

function renderNodeMap() {
  if (!el.nodeMap) return;
  el.nodeMap.innerHTML = "";
  const steps = randomFormula().split(" -> ");
  steps.forEach((step) => {
    const node = document.createElement("div");
    node.className = "node";
    node.textContent = step;
    el.nodeMap.appendChild(node);
  });
}

function runPlayback() {
  if (!el.formulaPlayback) return;
  el.formulaPlayback.innerHTML = "";
  const steps = randomFormula().split(" -> ");
  steps.forEach((step, idx) => {
    const chip = document.createElement("div");
    chip.className = "formula-step";
    chip.textContent = step;
    el.formulaPlayback.appendChild(chip);
    setTimeout(() => {
      chip.classList.add("active");
    }, 120 * idx);
  });
}

function openMapper() {
  if (!el.mapperModal) return;
  el.mapperGrid.innerHTML = "";
  const sampleKeys = ["Col 1", "Col 2", "Col 3", "Target"];
  sampleKeys.forEach((key) => {
    const item = document.createElement("div");
    item.className = "mapper-item";
    item.textContent = key;
    item.addEventListener("click", () => item.classList.toggle("selected"));
    el.mapperGrid.appendChild(item);
  });
  el.mapperModal.classList.remove("hidden");
}

function closeMapper() {
  if (!el.mapperModal) return;
  el.mapperModal.classList.add("hidden");
}

function stepTraining() {
  if (!state.running) return;
  state.generation += 1;
  const improvement = (1 - state.best) * (0.02 + Math.random() * 0.05);
  state.best = Math.min(1, state.best + improvement);
  state.avg = state.best * (0.65 + Math.random() * 0.1);
  state.history.push(state.best);
  state.geneFreq = Array.from({ length: 10 }, () => Math.random());
  el.genLabel.textContent = `Gen ${state.generation}`;
  el.bestLabel.textContent = `Best ${state.best.toFixed(3)}`;
  updateLeaderboard();
  if (state.generation >= state.maxGenerations) {
    stopTraining();
    setStatus(`Training complete at Gen ${state.generation} (max generations).`);
    return;
  }
  const shouldStopOnTarget = el.stopOnTarget && el.stopOnTarget.checked;
  if (shouldStopOnTarget && state.best >= state.targetAccuracy && state.generation >= state.minGenerations) {
    stopTraining();
    setStatus(`Training complete at Gen ${state.generation} (target reached).`);
  }
}

function renderLoop() {
  smoothCharts();
  drawLineChart();
  drawBarChart();
  requestAnimationFrame(renderLoop);
}

function startTraining() {
  if (!loadDatasetFromText()) {
    setStatus("Load training data first.");
    return;
  }
  state.librarySize = Number(el.librarySize.value);
  state.genomeLength = Number(el.genomeLength.value);
  state.maxGenerations = Number(el.generationCount.value);
  state.targetAccuracy = Number(el.accuracyTarget.value);
  state.minGenerations = Math.max(80, Math.floor(state.maxGenerations * 0.5));
  state.running = true;
  state.generation = 0;
  state.best = 0;
  state.history = [];
  state.historyDisplay = [];
  el.rewindSlider.max = String(state.maxGenerations);
  el.rewindValue.textContent = "0";
  setStatus("Training running...");
  if (state.interval) clearInterval(state.interval);
  state.interval = setInterval(stepTraining, 280);
}

function stopTraining() {
  state.running = false;
  if (state.interval) {
    clearInterval(state.interval);
    state.interval = null;
  }
}

function setMode(mode) {
  el.modePills.forEach((pill) => {
    pill.classList.toggle("active", pill.dataset.mode === mode);
  });
  el.askPanel.classList.toggle("hidden", mode !== "ask");
  el.trainCards.forEach((card) => {
    card.classList.toggle("hidden", mode === "ask");
  });
  if (mode === "ask") {
    setStatus("Ask mode active.");
  } else {
    setStatus("Training mode active.");
  }
}

function runAsk() {
  const key = el.askInput.value.trim();
  const algo = el.algoKeyInput.value.trim();
  if (!algo) {
    el.askStatus.textContent = "Algorithm key required.";
    return;
  }
  el.askStatus.textContent = "Processing...";
  const answer = key ? `Predicted(${key}) -> ${Math.random().toFixed(4)}` : "No key provided.";
  el.askOutput.textContent = answer;
  runPlayback();
}

function setTheme(theme) {
  el.appRoot.className = `ide ${theme}`;
  el.themePills.forEach((pill) => {
    pill.classList.toggle("active", pill.dataset.theme === theme);
  });
  drawLineChart();
  drawBarChart();
}

function togglePanel(panel) {
  const isActive = el.slidePanel.dataset.active === panel;
  if (isActive) {
    const willCollapse = !el.slidePanel.classList.contains("collapsed");
    el.slidePanel.classList.toggle("collapsed");
    el.appRoot.classList.toggle("panel-collapsed", willCollapse);
    drawLineChart();
    drawBarChart();
    return;
  }
  el.slidePanel.dataset.active = panel;
  el.slidePanel.classList.remove("collapsed");
  el.appRoot.classList.remove("panel-collapsed");
  el.iconButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.panel === panel);
  });
  el.panelSections.forEach((section) => {
    section.classList.toggle("active", section.dataset.panelSection === panel);
  });
  drawLineChart();
  drawBarChart();
}

function loadSample() {
  fetch("data/lexicon.json")
    .then((res) => res.json())
    .then((data) => {
      el.datasetInput.value = JSON.stringify(data, null, 2);
      loadDatasetFromText();
      openMapper();
      setStatus("Sample data loaded.");
    })
    .catch(() => {
      el.datasetInput.value = JSON.stringify(
        {
          Entry_01: { Key: [12, 4, "mars"], Value: 28.5 },
          Entry_02: { Key: [18, 2, "venus"], Value: 32.1 },
          Entry_03: { Key: [7, 9, "jupiter"], Value: 24.7 },
          Entry_04: { Key: [3, 5, "saturn"], Value: 18.2 },
          Entry_05: { Key: [21, 1, "neptune"], Value: 36.9 },
          Entry_06: { Key: [10, 7, "uranus"], Value: 27.4 },
          Entry_07: { Key: [5, 6, "earth"], Value: 19.6 },
          Entry_08: { Key: [16, 3, "mercury"], Value: 30.2 },
        },
        null,
        2
      );
      loadDatasetFromText();
      openMapper();
      setStatus("Sample data loaded.");
    });
}

el.iconButtons.forEach((btn) => {
  btn.addEventListener("click", () => togglePanel(btn.dataset.panel));
});

document.querySelectorAll("button").forEach((btn) => {
  btn.addEventListener("click", () => {
    btn.classList.remove("press");
    void btn.offsetWidth;
    btn.classList.add("press");
    setTimeout(() => btn.classList.remove("press"), 240);
  });
});

el.librarySize.addEventListener("input", () => {
  el.libraryValue.textContent = el.librarySize.value;
});

el.fileInput.addEventListener("change", (event) => {
  const file = event.target.files && event.target.files[0];
  if (file) handleFileUpload(file);
});

el.datasetInput.addEventListener("input", () => {
  loadDatasetFromText();
  setStatus("Dataset updated.");
});

el.themePills.forEach((pill) => {
  pill.addEventListener("click", () => setTheme(pill.dataset.theme));
});

el.modePills.forEach((pill) => {
  pill.addEventListener("click", () => setMode(pill.dataset.mode));
});

el.btnAsk.addEventListener("click", runAsk);
el.btnStart.addEventListener("click", startTraining);
el.btnStop.addEventListener("click", stopTraining);
el.btnSample.addEventListener("click", loadSample);
el.btnCataclysm.addEventListener("click", () => {
  setStatus("Cataclysm triggered. Re-seeding 80% population.");
  state.best = Math.max(0.1, state.best - 0.1);
});
el.btnGhost.addEventListener("click", () => {
  uiState.ghostLines = !uiState.ghostLines;
  el.btnGhost.classList.toggle("active", uiState.ghostLines);
});
el.btnNodeMap.addEventListener("click", () => {
  uiState.nodeMap = !uiState.nodeMap;
  el.nodeMap.classList.toggle("hidden", !uiState.nodeMap);
  if (uiState.nodeMap) renderNodeMap();
});
el.btnLockAll.addEventListener("click", () => {
  el.mutatorGrid.querySelectorAll(".mutator-chip").forEach((chip) => {
    chip.classList.add("locked");
    chip.classList.remove("banned");
  });
});
el.btnBanAll.addEventListener("click", () => {
  el.mutatorGrid.querySelectorAll(".mutator-chip").forEach((chip) => {
    chip.classList.add("banned");
    chip.classList.remove("locked");
  });
});
el.btnClearLocks.addEventListener("click", () => {
  el.mutatorGrid.querySelectorAll(".mutator-chip").forEach((chip) => {
    chip.classList.remove("locked", "banned");
  });
});
el.rewindSlider.addEventListener("input", () => {
  el.rewindValue.textContent = el.rewindSlider.value;
});
el.btnRewind.addEventListener("click", () => {
  const target = Number(el.rewindSlider.value);
  state.generation = target;
  setStatus(`Rewound to Gen ${target}.`);
});
el.btnRewindBoost.addEventListener("click", () => {
  const target = Number(el.rewindSlider.value);
  state.generation = target;
  state.best = Math.max(0, state.best - 0.1);
  setStatus(`Rewound to Gen ${target} with chaos.`);
});
el.btnExportPy.addEventListener("click", () => {
  setStatus("Python export copied.");
});
el.btnExportJs.addEventListener("click", () => {
  setStatus("JavaScript export copied.");
});
el.apiToggle.addEventListener("change", () => {
  if (el.apiToggle.checked) {
    el.apiUrl.textContent = "https://flux-evolver.example/api/v1/ask";
  } else {
    el.apiUrl.textContent = "API disabled";
  }
});
el.btnMapperApply.addEventListener("click", closeMapper);
el.btnMapperClose.addEventListener("click", closeMapper);
el.btnCopyAlgo.addEventListener("click", () => {
  if (!el.algoKeyBox) return;
  el.algoKeyBox.select();
  document.execCommand("copy");
  setStatus("Algorithm key copied.");
});

setDatasetStatus();
populateMutator();
renderLoop();
window.addEventListener("resize", () => {
  drawLineChart();
  drawBarChart();
});
