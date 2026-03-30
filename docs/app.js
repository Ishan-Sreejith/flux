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

// Simplified element accessor with safety
const getEl = (id) => document.getElementById(id);

const el = {
  appRoot: getEl("appRoot"),
  iconButtons: Array.from(document.querySelectorAll(".icon-btn")),
  slidePanel: getEl("slidePanel"),
  panelSections: Array.from(document.querySelectorAll(".panel-section")),
  librarySize: getEl("librarySize"),
  libraryValue: getEl("libraryValue"),
  populationSize: getEl("populationSize"),
  genomeLength: getEl("genomeLength"),
  generationCount: getEl("generationCount"),
  accuracyTarget: getEl("accuracyTarget"),
  fileInput: getEl("fileInput"),
  datasetInput: getEl("datasetInput"),
  datasetStatus: getEl("datasetStatus"),
  statusMessage: getEl("statusMessage"),
  themePills: Array.from(document.querySelectorAll(".theme-pill")),
  modePills: Array.from(document.querySelectorAll(".mode-pill")),
  askPanel: getEl("askPanel"),
  askInput: getEl("askInput"),
  algoKeyInput: getEl("algoKeyInput"),
  algoKeyAsk: getEl("algoKeyAsk"),
  askOutput: getEl("askOutput"),
  askStatus: getEl("askStatus"),
  btnAsk: getEl("btnAsk"),
  btnStart: getEl("btnStart"),
  btnStop: getEl("btnStop"),
  btnSample: getEl("btnSample"),
  btnAutopilot: getEl("btnAutopilot"),
  fitnessChart: getEl("fitnessChart"),
  geneChart: getEl("geneChart"),
  leaderboard: getEl("leaderboard"),
  genLabel: getEl("genLabel"),
  bestLabel: getEl("bestLabel"),
  trainCards: Array.from(document.querySelectorAll(".train-only")),
  btnCopyAlgo: getEl("btnCopyAlgo"),
  btnGhost: getEl("btnGhost"),
  btnNodeMap: getEl("btnNodeMap"),
  nodeMap: getEl("nodeMap"),
  btnCataclysm: getEl("btnCataclysm"),
  mutatorGrid: getEl("mutatorGrid"),
  btnLockAll: getEl("btnLockAll"),
  btnBanAll: getEl("btnBanAll"),
  btnClearLocks: getEl("btnClearLocks"),
  rewindSlider: getEl("rewindSlider"),
  rewindValue: getEl("rewindValue"),
  btnRewind: getEl("btnRewind"),
  btnRewindBoost: getEl("btnRewindBoost"),
  btnExportPy: getEl("btnExportPy"),
  btnExportJs: getEl("btnExportJs"),
  apiToggle: getEl("apiToggle"),
  apiUrl: getEl("apiUrl"),
  formulaPlayback: getEl("formulaPlayback"),
  fileName: getEl("fileName"),
  mapperModal: getEl("mapperModal"),
  mapperGrid: getEl("mapperGrid"),
  btnMapperApply: getEl("btnMapperApply"),
  btnMapperClose: getEl("btnMapperClose"),
  stopOnTarget: getEl("stopOnTarget"),
  exampleModal: getEl("exampleModal"),
  btnExampleClose: getEl("btnExampleClose"),
  exampleCards: Array.from(document.querySelectorAll(".example-card")),
  buildVersion: getEl("buildVersion"),
  btnAutoformat: getEl("btnAutoformat"),
  btnGenerateHuman: getEl("btnGenerateHuman"),
  fullVersionInput: getEl("fullVersionInput"),
  guideCard: getEl("guideCard"),
  guideTitle: getEl("guideTitle"),
  guideText: getEl("guideText"),
  guideStep: getEl("guideStep"),
  btnGuidePrev: getEl("btnGuidePrev"),
  btnGuideNext: getEl("btnGuideNext"),
  btnGuideClose: getEl("btnGuideClose"),
  btnGuideStart: getEl("btnGuideStart"),
  consoleOutput: getEl("consoleOutput"),
  btnClearConsole: getEl("btnClearConsole"),
};

const guideSteps = [
  { title: "Protocol 1: Data Link", text: "Ingest a dataset via Data Architect to initialize search space." },
  { title: "Protocol 2: Logic Decompile", text: "Autoformat raw signals and decompile to human-readable strategies." },
  { title: "Protocol 3: Seed Evolution", text: "Configure population density and genome length to begin training." },
  { title: "Protocol 4: Interactive Mutator", text: "Pin or ban specific alleles to influence evolution in real-time." },
  { title: "Protocol 5: Deploy SDK", text: "Export optimized neural sequences as Python or JS modules." },
];

let guideIndex = 0;

function log(msg, type = 'default') {
  if (!el.consoleOutput) return;
  const line = document.createElement("div");
  line.className = `log-line ${type}`;
  const now = new Date();
  const time = now.getHours().toString().padStart(2, '0') + ":" + now.getMinutes().toString().padStart(2, '0') + ":" + now.getSeconds().toString().padStart(2, '0');
  line.innerHTML = `<span class="log-time">[${time}]</span> ${msg}`;
  el.consoleOutput.prepend(line);
}

function setStatus(message) {
  if (el.statusMessage) el.statusMessage.textContent = message;
}

function setDatasetStatus() {
  if (el.datasetStatus) el.datasetStatus.textContent = `${state.dataset.length} items`;
}

function parseDataset(text) {
  if (!text || !text.trim()) return [];
  const trimmed = text.trim();
  try {
    if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
      const payload = JSON.parse(trimmed);
      return Array.isArray(payload) ? payload : Object.values(payload);
    }
  } catch (err) {
    log("Parsing CSV/Text format...", "default");
  }
  const rows = trimmed.split(/\r?\n/).filter((line) => line.trim());
  return rows.map((line) => line.split(","));
}

function loadDatasetFromText() {
  if (!el.datasetInput) return false;
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

function loadExample(exampleId) {
  const map = {
    animals: "data/animals.json",
    taxonomy: "data/taxonomy.json",
    lexicon: "data/lexicon.json",
    market: "data/market_linear.json",
    solar: "data/solar_system.json",
    slingshot: "data/slingshot_data.json",
  };
  const path = map[exampleId];
  if (!path) return;
  
  log(`Fetching preset: ${exampleId}...`, "system");
  fetch(path)
    .then(res => res.json())
    .then(data => {
      if (el.datasetInput) {
        el.datasetInput.value = JSON.stringify(data, null, 2);
        loadDatasetFromText();
        if (el.fileName) el.fileName.textContent = path.split("/").pop();
        log(`Neural preset "${exampleId}" loaded.`, "success");
        if (el.exampleModal) el.exampleModal.classList.add("hidden");
        openMapper();
      }
    })
    .catch(err => {
      log(`Failed to load preset: ${err.message}`, "error");
    });
}

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
  if (!state.dataset || state.dataset.length === 0) return "numeric";
  const first = state.dataset[0];
  if (typeof first === "string" || (Array.isArray(first) && typeof first[0] === "string")) return "text";
  return "numeric";
}

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
  if (!el.leaderboard) return;
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

  ctx.beginPath();
  ctx.lineWidth = 3;
  ctx.strokeStyle = "#00d2ff";
  ctx.lineJoin = "round";

  state.historyDisplay.forEach((val, idx) => {
    const x = padding.left + (plotW / (state.historyDisplay.length - 1)) * idx;
    const y = padding.top + (1 - val) * plotH;
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.lineTo(padding.left + plotW, padding.top + plotH);
  ctx.lineTo(padding.left, padding.top + plotH);
  const grad = ctx.createLinearGradient(0, padding.top, 0, padding.top + plotH);
  grad.addColorStop(0, "rgba(0, 210, 255, 0.1)");
  grad.addColorStop(1, "rgba(0, 210, 255, 0)");
  ctx.fillStyle = grad;
  ctx.fill();
}

function bumpVersion() {
  state.changeCounter += 1;
  if (el.buildVersion) {
    el.buildVersion.textContent = `v${state.appVersion}.${state.changeCounter}`;
  }
}

function renderGuide() {
  if (!el.guideTitle || !el.guideText || !el.guideStep) return;
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
  
  if (el.genLabel) el.genLabel.textContent = `GEN ${state.generation}`;
  if (el.bestLabel) el.bestLabel.textContent = `${(state.best * 100).toFixed(2)}%`;
  
  updateLeaderboard();
  
  if (state.generation % 10 === 0) {
    log(`Gen ${state.generation}: Alpha Fitness at ${(state.best * 100).toFixed(2)}%`);
  }

  const stopChecked = el.stopOnTarget ? el.stopOnTarget.checked : false;
  if (state.generation >= state.maxGenerations || (stopChecked && state.best >= state.targetAccuracy)) {
    stopTraining();
    log(`Simulation stabilized at Gen ${state.generation}. Target fitness reached.`, "success");
  }
}

function startTraining() {
  if (!loadDatasetFromText()) {
    log("Simulation failed: Dataset source required.", "error");
    togglePanel("files");
    return;
  }
  state.running = true;
  state.generation = 0;
  state.best = 0;
  state.history = [];
  state.historyDisplay = [];
  
  if (el.appRoot) el.appRoot.classList.add("training-running");
  log("Initializing neural evolution kernel...", "system");
  
  if (state.interval) clearInterval(state.interval);
  state.interval = setInterval(stepTraining, 200);
}

function stopTraining() {
  state.running = false;
  if (el.appRoot) el.appRoot.classList.remove("training-running");
  if (state.interval) clearInterval(state.interval);
  setStatus("Engine Standby");
}

function togglePanel(panelName) {
  if (uiState.activePanel === panelName && el.slidePanel && !el.slidePanel.classList.contains("collapsed")) {
    el.slidePanel.classList.add("collapsed");
    return;
  }
  
  if (el.slidePanel) el.slidePanel.classList.remove("collapsed");
  uiState.activePanel = panelName;
  
  el.iconButtons.forEach(btn => btn.classList.toggle("active", btn.dataset.panel === panelName));
  el.panelSections.forEach(sec => sec.classList.toggle("active", sec.dataset.panelSection === panelName));
}

function setMode(mode) {
  el.modePills.forEach((pill) => {
    pill.classList.toggle("active", pill.dataset.mode === mode);
  });
  
  const fitnessCard = getEl("fitnessCard");
  const leaderboardCard = getEl("leaderboardCard");
  
  if (mode === "ask") {
    if (el.askPanel) el.askPanel.classList.remove("hidden");
    if (fitnessCard) fitnessCard.classList.add("hidden");
    if (leaderboardCard) leaderboardCard.classList.add("hidden");
  } else {
    if (el.askPanel) el.askPanel.classList.add("hidden");
    if (fitnessCard) fitnessCard.classList.remove("hidden");
    if (leaderboardCard) leaderboardCard.classList.remove("hidden");
  }

  log(`Switching to ${mode} mode.`);
}

function openMapper() { if (el.mapperModal) el.mapperModal.classList.remove("hidden"); }
function closeMapper() { if (el.mapperModal) el.mapperModal.classList.add("hidden"); }

function populateMutator() {
  if (!el.mutatorGrid) return;
  el.mutatorGrid.innerHTML = "";
  for(let i=1; i<=30; i++) {
    const chip = document.createElement("div");
    chip.className = "mutator-chip";
    chip.textContent = `P${i.toString().padStart(3, '0')}`;
    chip.addEventListener("click", () => chip.classList.toggle("locked"));
    el.mutatorGrid.appendChild(chip);
  }
}

/**
 * Initialization
 */
function init() {
  // Navigation
  el.iconButtons.forEach(btn => {
    btn.onclick = () => togglePanel(btn.dataset.panel);
  });

  // Mode Switching
  el.modePills.forEach(pill => {
    pill.onclick = () => setMode(pill.dataset.mode);
  });

  // Engine Controls
  if (el.btnStart) el.btnStart.onclick = startTraining;
  if (el.btnStop) el.btnStop.onclick = stopTraining;
  
  // Theme Switching
  el.themePills.forEach(pill => {
    pill.onclick = () => {
      el.themePills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      if (el.appRoot) el.appRoot.className = `ide ${pill.dataset.theme}`;
      log(`UI Environment synced: ${pill.textContent}`, "system");
    };
  });

  // Guide
  if (el.btnGuideNext) el.btnGuideNext.onclick = () => {
    guideIndex = (guideIndex + 1) % guideSteps.length;
    renderGuide();
  };
  if (el.btnGuidePrev) el.btnGuidePrev.onclick = () => {
    guideIndex = (guideIndex - 1 + guideSteps.length) % guideSteps.length;
    renderGuide();
  };
  if (el.btnGuideClose) el.btnGuideClose.onclick = () => {
    if (el.guideCard) el.guideCard.classList.add("hidden");
  };
  if (el.btnGuideStart) el.btnGuideStart.onclick = () => {
    guideIndex = 0;
    if (el.guideCard) el.guideCard.classList.remove("hidden");
    renderGuide();
  };

  // File handling
  if (el.fileInput) {
    el.fileInput.onchange = (e) => handleFileUpload(e.target.files[0]);
  }
  
  // Dataset Input
  if (el.datasetInput) {
    el.datasetInput.oninput = () => {
      loadDatasetFromText();
      bumpVersion();
    };
  }

  // Console
  if (el.btnClearConsole) el.btnClearConsole.onclick = () => {
    if (el.consoleOutput) el.consoleOutput.innerHTML = "";
  };

  // Modals
  if (el.btnSample) el.btnSample.onclick = () => {
    if (el.exampleModal) el.exampleModal.classList.remove("hidden");
  };
  if (el.btnExampleClose) el.btnExampleClose.onclick = () => {
    if (el.exampleModal) el.exampleModal.classList.add("hidden");
  };
  if (el.btnMapperClose) el.btnMapperClose.onclick = closeMapper;
  if (el.btnMapperApply) el.btnMapperApply.onclick = closeMapper;

  // Example Cards
  el.exampleCards.forEach(card => {
    card.onclick = () => loadExample(card.dataset.example);
  });

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
  populateMutator();
  log("Neural Evolution Engine v0.0.3 Ready.");
}

// Global initialization
window.onload = init;
