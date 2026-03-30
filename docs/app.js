/**
 * Flux Evolver Core v0.0.3
 * Improved Neural Formula Studio
 */

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
  datasetRaw: null,
  librarySize: 300,
  numericParamCount: 600,
  textParamCount: 400,
  genomeLength: 8,
  maxGenerations: 300,
  targetAccuracy: 0.95,
  minGenerations: 30,
  mutationRate: 0.2,
  mutationStrength: 0.35,
  selectionStrategy: "roulette",
  topK: 10,
  eliteFraction: 0.1,
  mutationPressure: true,
  stagnationGenerations: 16,
  stagnationCounter: 0,
  domain: "numeric",
  appVersion: "0.0.3",
  changeCounter: 0,
};

const uiState = {
  ghostLines: false,
  nodeMap: false,
  autopilot: false,
  mutator: new Map(),
  activePanel: 'settings',
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
  algoKeyAsk: document.getElementById("algoKeyAsk"),
  askOutput: document.getElementById("askOutput"),
  askStatus: document.getElementById("askStatus"),
  btnAsk: document.getElementById("btnAsk"),
  btnStart: document.getElementById("btnStart"),
  btnStop: document.getElementById("btnStop"),
  btnSample: document.getElementById("btnSample"),
  btnAutopilot: document.getElementById("btnAutopilot"),
  fitnessChart: document.getElementById("fitnessChart"),
  geneChart: document.getElementById("geneChart"),
  leaderboard: document.getElementById("leaderboard"),
  genLabel: document.getElementById("genLabel"),
  bestLabel: document.getElementById("bestLabel"),
  trainCards: Array.from(document.querySelectorAll(".train-only")),
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
  fileName: document.getElementById("fileName"),
  mapperModal: document.getElementById("mapperModal"),
  mapperGrid: document.getElementById("mapperGrid"),
  btnMapperApply: document.getElementById("btnMapperApply"),
  btnMapperClose: document.getElementById("btnMapperClose"),
  stopOnTarget: document.getElementById("stopOnTarget"),
  exampleModal: document.getElementById("exampleModal"),
  btnExampleClose: document.getElementById("btnExampleClose"),
  exampleCards: Array.from(document.querySelectorAll(".example-card")),
  buildVersion: document.getElementById("buildVersion"),
  btnAutoformat: document.getElementById("btnAutoformat"),
  btnGenerateHuman: document.getElementById("btnGenerateHuman"),
  fullVersionInput: document.getElementById("fullVersionInput"),
  guideCard: document.getElementById("guideCard"),
  guideTitle: document.getElementById("guideTitle"),
  guideText: document.getElementById("guideText"),
  guideStep: document.getElementById("guideStep"),
  btnGuidePrev: document.getElementById("btnGuidePrev"),
  btnGuideNext: document.getElementById("btnGuideNext"),
  btnGuideClose: document.getElementById("btnGuideClose"),
  btnGuideStart: document.getElementById("btnGuideStart"),
  consoleOutput: document.getElementById("consoleOutput"),
  btnClearConsole: document.getElementById("btnClearConsole"),
};

const guideSteps = [
  { title: "Protocol 1: Data Link", text: "Ingest a dataset via Data Architect to initialize search space." },
  { title: "Protocol 2: Logic Decompile", text: "Autoformat raw signals and decompile to human-readable strategies." },
  { title: "Protocol 3: Seed Evolution", text: "Configure population density and genome length to begin training." },
  { title: "Protocol 4: Interactive Mutator", text: "Pin or ban specific alleles to influence evolution in real-time." },
  { title: "Protocol 5: Deploy SDK", text: "Export optimized neural sequences as Python or JS modules." },
];

let guideIndex = 0;

/**
 * Console Utilities
 */
function log(msg, type = 'default') {
  const line = document.createElement("div");
  line.className = `log-line ${type}`;
  const now = new Date();
  const time = now.getHours().toString().padStart(2, '0') + ":" + now.getMinutes().toString().padStart(2, '0') + ":" + now.getSeconds().toString().padStart(2, '0');
  line.innerHTML = `<span class="log-time">[${time}]</span> ${msg}`;
  el.consoleOutput.prepend(line);
}

function setStatus(message) {
  el.statusMessage.textContent = message;
}

function setDatasetStatus() {
  el.datasetStatus.textContent = `${state.dataset.length} items`;
}

/**
 * Data Processing
 */
function parseDataset(text) {
  if (!text || !text.trim()) return [];
  const trimmed = text.trim();
  try {
    if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
      const payload = JSON.parse(trimmed);
      return Array.isArray(payload) ? payload : Object.values(payload);
    }
  } catch (err) {
    log("Error parsing JSON, attempting CSV/Text", "error");
  }
  const rows = trimmed.split(/\r?\n/).filter((line) => line.trim());
  return rows.map((line) => line.split(","));
}

function loadDatasetFromText() {
  state.datasetRaw = null;
  const trimmed = el.datasetInput.value.trim();
  state.dataset = parseDataset(trimmed);
  setDatasetStatus();
  return state.dataset.length > 0;
}

function handleFileUpload(file) {
  const reader = new FileReader();
  reader.onload = () => {
    el.datasetInput.value = reader.result;
    if (el.fileName) el.fileName.textContent = file.name;
    loadDatasetFromText();
    openMapper();
    log(`Dataset "${file.name}" ingested.`, "success");
  };
  reader.readAsText(file);
}

/**
 * Simulation Engine
 */
function randomInt(max) {
  return Math.floor(Math.random() * max);
}

function randomFormula() {
  const domain = inferDomain();
  const ops =
    domain === "text"
      ? ["upper", "lower", "capitalize", "swapcase", "first_letter", "last_letter", "strip", "concat", "replace"]
      : ["add_const", "sub_const", "mul_const", "div_const", "round", "clamp"];
  const steps = [];
  for (let i = 0; i < state.genomeLength; i += 1) {
    const poolSize = domain === "text" ? state.textParamCount : state.numericParamCount;
    const paramId = String(randomInt(poolSize) + 1).padStart(3, "0");
    const op = ops[randomInt(ops.length)];
    steps.push(`P${paramId}:${op}`);
  }
  return steps.join("→");
}

function inferDomain() {
  const first = state.dataset[0];
  if (typeof first === "string" || (Array.isArray(first) && typeof first[0] === "string")) return "text";
  return "numeric";
}

/**
 * Visualization
 */
function resizeCanvas(canvas) {
  const parent = canvas.parentElement;
  if (!parent) return null;
  const rect = parent.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const width = rect.width || 400;
  const height = rect.height || 220;
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
  if (el.algoKeyAsk) el.algoKeyAsk.value = topFormula;
  
  for (let i = 0; i < 6; i += 1) {
    const row = document.createElement("div");
    row.className = "leaderboard-row";
    const score = (Math.max(0, state.best * 100 - i * 3.42)).toFixed(2);
    const formula = i === 0 ? topFormula : randomFormula();
    row.innerHTML = `
      <span class="rank">#${i + 1}</span>
      <span class="formula">${formula}</span>
      <span class="score">${score}%</span>
    `;
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
  const padding = { left: 40, right: 20, top: 20, bottom: 30 };
  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;

  // Draw Grid
  ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
  ctx.lineWidth = 1;
  for(let i=0; i<=4; i++) {
    const y = padding.top + (plotH * (1 - i/4));
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
  }

  if (state.historyDisplay.length < 2) return;

  // Draw Line
  ctx.beginPath();
  ctx.lineWidth = 3;
  ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue("--accent-2");
  ctx.lineJoin = "round";

  state.historyDisplay.forEach((val, idx) => {
    const x = padding.left + (plotW / (state.historyDisplay.length - 1)) * idx;
    const y = padding.top + (1 - val) * plotH;
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Draw Area
  ctx.lineTo(padding.left + plotW, padding.top + plotH);
  ctx.lineTo(padding.left, padding.top + plotH);
  const grad = ctx.createLinearGradient(0, padding.top, 0, padding.top + plotH);
  grad.addColorStop(0, "rgba(0, 210, 255, 0.1)");
  grad.addColorStop(1, "rgba(0, 210, 255, 0)");
  ctx.fillStyle = grad;
  ctx.fill();
}

/**
 * Event Listeners & UI Lifecycle
 */
function bumpVersion(reason) {
  state.changeCounter += 1;
  if (el.buildVersion) {
    el.buildVersion.textContent = `v${state.appVersion}.${state.changeCounter}`;
  }
}

function renderGuide() {
  const step = guideSteps[guideIndex];
  el.guideTitle.textContent = step.title;
  el.guideText.textContent = step.text;
  el.guideStep.textContent = `${guideIndex + 1} / ${guideSteps.length}`;
}

function stepTraining() {
  if (!state.running) return;
  state.generation += 1;
  
  const step = 0.02 + Math.random() * 0.04;
  state.best = Math.min(1, state.best + (1 - state.best) * step);
  state.history.push(state.best);
  
  el.genLabel.textContent = `GEN ${state.generation}`;
  el.bestLabel.textContent = `${(state.best * 100).toFixed(2)}%`;
  
  updateLeaderboard();
  
  if (state.generation % 10 === 0) {
    log(`Gen ${state.generation}: Alpha Fitness at ${(state.best * 100).toFixed(2)}%`);
  }

  if (state.generation >= state.maxGenerations || (el.stopOnTarget.checked && state.best >= state.targetAccuracy)) {
    stopTraining();
    log(`Simulation stabilized at Gen ${state.generation}. Target fitness reached.`, "success");
  }
}

function startTraining() {
  if (!loadDatasetFromText()) {
    log("Simulation failed: Dataset source required.", "error");
    return;
  }
  state.running = true;
  state.generation = 0;
  state.best = 0;
  state.history = [];
  state.historyDisplay = [];
  
  el.appRoot.classList.add("training-running");
  log("Initializing neural evolution kernel...", "system");
  
  if (state.interval) clearInterval(state.interval);
  state.interval = setInterval(stepTraining, 200);
}

function stopTraining() {
  state.running = false;
  el.appRoot.classList.remove("training-running");
  if (state.interval) clearInterval(state.interval);
  setStatus("Engine Standby");
}

function togglePanel(panel) {
  if (uiState.activePanel === panel) {
    el.slidePanel.classList.toggle("collapsed");
  } else {
    el.slidePanel.classList.remove("collapsed");
    uiState.activePanel = panel;
    
    el.iconButtons.forEach(btn => btn.classList.toggle("active", btn.dataset.panel === panel));
    el.panelSections.forEach(sec => sec.classList.toggle("active", sec.dataset.panelSection === panel));
  }
}

/**
 * Initialization
 */
function init() {
  // Navigation
  el.iconButtons.forEach(btn => btn.addEventListener("click", () => togglePanel(btn.dataset.panel)));

  // Engine Controls
  el.btnStart.addEventListener("click", startTraining);
  el.btnStop.addEventListener("click", stopTraining);
  
  // Theme Switching
  el.themePills.forEach(pill => {
    pill.addEventListener("click", () => {
      el.themePills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      el.appRoot.className = `ide ${pill.dataset.theme}`;
      log(`UI Environment synced: ${pill.textContent}`, "system");
    });
  });

  // Guide
  el.btnGuideNext.addEventListener("click", () => {
    guideIndex = (guideIndex + 1) % guideSteps.length;
    renderGuide();
  });
  el.btnGuidePrev.addEventListener("click", () => {
    guideIndex = (guideIndex - 1 + guideSteps.length) % guideSteps.length;
    renderGuide();
  });

  // File handling
  el.fileInput.addEventListener("change", (e) => handleFileUpload(e.target.files[0]));

  // Start Visual Loop
  function animate() {
    if (state.history.length > 0) {
      if (state.historyDisplay.length < state.history.length) {
        state.historyDisplay.push(state.history[state.historyDisplay.length]);
      }
      state.historyDisplay = state.historyDisplay.map((v, i) => lerp(v, state.history[i], 0.1));
    }
    drawLineChart();
    requestAnimationFrame(animate);
  }
  
  animate();
  renderGuide();
  log("Neural Evolution Engine v0.0.3 Ready.");
}

document.addEventListener("DOMContentLoaded", init);

// Mapper Modal handling
function openMapper() { el.mapperModal.classList.remove("hidden"); }
function closeMapper() { el.mapperModal.classList.add("hidden"); }
el.btnMapperClose.addEventListener("click", closeMapper);
el.btnMapperApply.addEventListener("click", closeMapper);

// Presets Modal
el.btnSample.addEventListener("click", () => el.exampleModal.classList.remove("hidden"));
el.btnExampleClose.addEventListener("click", () => el.exampleModal.classList.add("hidden"));

// Mutation Brush (mockup)
function populateMutator() {
  el.mutatorGrid.innerHTML = "";
  for(let i=1; i<=30; i++) {
    const chip = document.createElement("div");
    chip.className = "mutator-chip";
    chip.textContent = `P${i.toString().padStart(3, '0')}`;
    chip.addEventListener("click", () => chip.classList.toggle("locked"));
    el.mutatorGrid.appendChild(chip);
  }
}
populateMutator();
