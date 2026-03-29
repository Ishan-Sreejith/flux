const state = {
  running: false,
  interval: null,
  generation: 0,
  best: 0,
  avg: 0,
  history: [],
  geneFreq: [],
  dataset: [],
  librarySize: 300,
  genomeLength: 8,
  maxGenerations: 300,
  targetAccuracy: 0.95,
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

function updateLeaderboard() {
  el.leaderboard.innerHTML = "";
  for (let i = 0; i < 5; i += 1) {
    const row = document.createElement("div");
    row.className = "leaderboard-row";
    const score = Math.max(0, state.best - i * 0.03).toFixed(3);
    row.innerHTML = `<span>#${i + 1} ${randomFormula()}</span><span>${score}</span>`;
    el.leaderboard.appendChild(row);
  }
}

function drawLineChart() {
  const canvas = el.fitnessChart;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "#2c3342";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i += 1) {
    const y = (height / 4) * i;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }
  if (state.history.length < 2) return;
  ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue("--accent-2");
  ctx.lineWidth = 2;
  ctx.beginPath();
  state.history.forEach((value, index) => {
    const x = (width / (state.history.length - 1)) * index;
    const y = height - value * height;
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

function drawBarChart() {
  const canvas = el.geneChart;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  const bars = 10;
  const gap = 8;
  const barWidth = (width - gap * (bars - 1)) / bars;
  for (let i = 0; i < bars; i += 1) {
    const value = state.geneFreq[i] || Math.random();
    const barHeight = value * height;
    ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--accent");
    ctx.fillRect(i * (barWidth + gap), height - barHeight, barWidth, barHeight);
  }
}

function stepTraining() {
  if (!state.running) return;
  state.generation += 1;
  const improvement = (1 - state.best) * (0.08 + Math.random() * 0.12);
  state.best = Math.min(1, state.best + improvement);
  state.avg = state.best * (0.65 + Math.random() * 0.1);
  state.history.push(state.best);
  state.geneFreq = Array.from({ length: 10 }, () => Math.random());
  el.genLabel.textContent = `Gen ${state.generation}`;
  el.bestLabel.textContent = `Best ${state.best.toFixed(3)}`;
  updateLeaderboard();
  drawLineChart();
  drawBarChart();
  if (state.best >= state.targetAccuracy || state.generation >= state.maxGenerations) {
    stopTraining();
    setStatus("Training complete.");
  }
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
  state.running = true;
  state.generation = 0;
  state.best = 0;
  state.history = [];
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
  if (mode === "ask") {
    setStatus("Ask mode active.");
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
    el.slidePanel.classList.toggle("collapsed");
    return;
  }
  el.slidePanel.dataset.active = panel;
  el.slidePanel.classList.remove("collapsed");
  el.iconButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.panel === panel);
  });
  el.panelSections.forEach((section) => {
    section.classList.toggle("active", section.dataset.panelSection === panel);
  });
}

function loadSample() {
  fetch("data/lexicon.json")
    .then((res) => res.json())
    .then((data) => {
      el.datasetInput.value = JSON.stringify(data, null, 2);
      loadDatasetFromText();
      setStatus("Sample data loaded.");
    })
    .catch(() => {
      el.datasetInput.value = JSON.stringify(
        { A: { Key: 1, Value: 2 }, B: { Key: 2, Value: 4 } },
        null,
        2
      );
      loadDatasetFromText();
      setStatus("Sample data loaded.");
    });
}

el.iconButtons.forEach((btn) => {
  btn.addEventListener("click", () => togglePanel(btn.dataset.panel));
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

setDatasetStatus();
drawLineChart();
drawBarChart();
