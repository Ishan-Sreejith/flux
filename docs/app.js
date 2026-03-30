/**
 * Flux Evolver Web IDE v0.1.0
 * GitHub Pages friendly, defensive UI wiring.
 */

const state = {
  running: false,
  interval: null,
  generation: 0,
  best: 0,
  history: [],
  historyDisplay: [],
  dataset: [],
  librarySize: 300,
  populationSize: 120,
  genomeLength: 8,
  maxGenerations: 300,
  targetAccuracy: 0.95,
  appVersion: "0.1.0",
  changeCounter: 0,
  activeTheme: "theme-cyber",
};

const uiState = {
  activePanel: "settings",
  guideIndex: 0,
  autoplay: false,
};

const guideSteps = [
  { title: "Protocol 1: Data Link", text: "Ingest a dataset from presets or upload a file to start." },
  { title: "Protocol 2: Normalize", text: "Use Autoformat to clean and validate raw JSON input." },
  { title: "Protocol 3: Decompile", text: "Generate a human-readable algorithm summary from the dataset." },
  { title: "Protocol 4: Evolve", text: "Run training and monitor convergence in the telemetry chart." },
  { title: "Protocol 5: Export", text: "Export generated logic as JavaScript or Python templates." },
];

const $ = (id) => document.getElementById(id);

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}

function nowTimeString() {
  const now = new Date();
  return [
    now.getHours().toString().padStart(2, "0"),
    now.getMinutes().toString().padStart(2, "0"),
    now.getSeconds().toString().padStart(2, "0"),
  ].join(":");
}

function log(msg, type = "default") {
  const consoleOut = $("consoleOutput");
  if (!consoleOut) return;
  const line = el("div", `log-line ${type}`);
  line.innerHTML = `<span class="log-time">[${nowTimeString()}]</span> ${msg}`;
  consoleOut.prepend(line);
}

function setText(id, value) {
  const node = $(id);
  if (node) node.textContent = value;
}

function setValue(id, value) {
  const node = $(id);
  if (node) node.value = value;
}

function updateStatus(message) {
  setText("statusMessage", message);
}

function updateBuildBadges() {
  setText("buildVersion", `v${state.appVersion}`);
}

function clamp01(v) {
  return Math.max(0, Math.min(1, v));
}

function updateLeaderboard() {
  const lb = $("leaderboard");
  if (!lb) return;
  lb.innerHTML = "";
  for (let i = 0; i < 6; i += 1) {
    const row = el("div", "leaderboard-row");
    const fitness = Math.max(0, state.best * 100 - i * 1.8);
    const seq = `P${Math.floor(Math.random() * 250)}:${["add", "mul", "sub", "round"][i % 4]} -> P${Math.floor(Math.random() * 250)}:${["if", "clamp", "div", "pow"][i % 4]}`;
    row.innerHTML = `
      <span class="rank">#${i + 1}</span>
      <span class="formula">${seq}</span>
      <span class="score">${fitness.toFixed(2)}%</span>
    `;
    lb.appendChild(row);
  }
}

function resizeCanvas(canvas) {
  const parent = canvas?.parentElement;
  if (!canvas || !parent) return null;
  const rect = parent.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const width = Math.max(1, rect.width);
  const height = Math.max(1, rect.height);
  const targetWidth = Math.floor(width * dpr);
  const targetHeight = Math.floor(height * dpr);
  if (canvas.width !== targetWidth || canvas.height !== targetHeight) {
    canvas.width = targetWidth;
    canvas.height = targetHeight;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
  }
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, width, height };
}

function drawFitness() {
  const canvas = $("fitnessChart");
  if (!canvas) return;
  const size = resizeCanvas(canvas);
  if (!size) return;
  const { ctx, width, height } = size;

  ctx.clearRect(0, 0, width, height);
  const padding = { left: 38, right: 10, top: 10, bottom: 24 };
  const pW = width - padding.left - padding.right;
  const pH = height - padding.top - padding.bottom;

  ctx.strokeStyle = "rgba(255,255,255,0.07)";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i += 1) {
    const y = padding.top + pH * (1 - i / 4);
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
  }

  if (state.historyDisplay.length < 2) return;

  ctx.beginPath();
  ctx.lineWidth = 2.5;
  ctx.strokeStyle = "#00d2ff";
  const stepX = pW / (state.historyDisplay.length - 1);
  state.historyDisplay.forEach((v, i) => {
    const x = padding.left + i * stepX;
    const y = padding.top + (1 - v) * pH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.lineTo(padding.left + pW, padding.top + pH);
  ctx.lineTo(padding.left, padding.top + pH);
  ctx.fillStyle = "rgba(0, 210, 255, 0.08)";
  ctx.fill();
}

function refreshChartState() {
  if (state.history.length > 0) {
    if (state.historyDisplay.length < state.history.length) {
      state.historyDisplay.push(state.history[state.historyDisplay.length]);
    }
    state.historyDisplay = state.historyDisplay.map((v, i) => v + (state.history[i] - v) * 0.18);
  }
  drawFitness();
}

function syncNumericSettings() {
  const pop = Number($("populationSize")?.value || state.populationSize);
  const genome = Number($("genomeLength")?.value || state.genomeLength);
  const generations = Number($("generationCount")?.value || state.maxGenerations);
  const accuracy = Number($("accuracyTarget")?.value || state.targetAccuracy);
  const library = Number($("librarySize")?.value || state.librarySize);

  state.populationSize = Number.isFinite(pop) ? Math.max(2, pop) : state.populationSize;
  state.genomeLength = Number.isFinite(genome) ? Math.max(1, genome) : state.genomeLength;
  state.maxGenerations = Number.isFinite(generations) ? Math.max(1, generations) : state.maxGenerations;
  state.targetAccuracy = Number.isFinite(accuracy) ? clamp01(accuracy) : state.targetAccuracy;
  state.librarySize = Number.isFinite(library) ? Math.max(10, library) : state.librarySize;

  setText("libraryValue", String(state.librarySize));
}

function parseDataset(raw) {
  const text = String(raw || "").trim();
  if (!text) return [];
  try {
    const parsed = JSON.parse(text);
    if (Array.isArray(parsed)) return parsed;
    if (parsed && typeof parsed === "object") return Object.values(parsed);
    return [];
  } catch {
    return [];
  }
}

function normalizeDataset(input) {
  const rows = Array.isArray(input) ? input : [];
  return rows
    .map((entry, index) => {
      if (entry && typeof entry === "object") {
        const key = entry.Key ?? entry.key ?? entry.input ?? entry.x ?? index;
        const value = entry.Value ?? entry.value ?? entry.output ?? entry.y ?? entry;
        return { Key: key, Value: value };
      }
      return { Key: index, Value: entry };
    })
    .filter((entry) => entry.Key !== undefined && entry.Value !== undefined);
}

function updateDatasetState(data, sourceName = "inline") {
  state.dataset = normalizeDataset(data);
  setText("datasetStatus", `${state.dataset.length} items`);
  setText("fileName", sourceName);
  if (state.dataset.length > 0) {
    updateStatus("Dataset Linked");
    log(`Dataset loaded (${state.dataset.length} rows).`, "success");
  } else {
    log("Dataset is empty after normalization.", "error");
  }
}

function autoformatDataset() {
  const input = $("datasetInput");
  if (!input) return;
  const parsed = parseDataset(input.value);
  if (parsed.length === 0) {
    log("Autoformat skipped. Provide valid JSON first.", "error");
    return;
  }
  const normalized = normalizeDataset(parsed);
  input.value = JSON.stringify(normalized, null, 2);
  updateDatasetState(normalized, $("fileName")?.textContent || "formatted.json");
  log("Dataset normalized and formatted.", "success");
}

function deriveRuleFromDataset(dataset) {
  if (!dataset.length) return "No deterministic rule could be inferred from empty data.";
  const pairs = dataset.slice(0, 6).map((item) => `${JSON.stringify(item.Key)} -> ${JSON.stringify(item.Value)}`);
  return [
    "Likely mapping strategy:",
    "1. Parse input key as primitive token.",
    "2. Apply deterministic transform sequence.",
    "3. Emit value domain-specific target.",
    "",
    "Sample traces:",
    ...pairs,
  ].join("\n");
}

function generateHumanAlgorithm() {
  const output = deriveRuleFromDataset(state.dataset);
  const target = $("fullVersionInput");
  if (target) {
    target.classList.remove("hidden");
    target.value = output;
  }
  log("Generated human-readable algorithm draft.", "system");
  return output;
}

function executeInference() {
  const input = $("askInput");
  const out = $("askOutput");
  if (!input || !out) return;
  const raw = input.value.trim();
  if (!raw) {
    out.textContent = "Provide a key first.";
    setText("askStatus", "Missing Input");
    return;
  }

  const maybeNumber = Number(raw);
  const key = Number.isNaN(maybeNumber) ? raw : maybeNumber;
  const match = state.dataset.find((row) => row.Key === key || String(row.Key) === String(key));
  const value = match ? match.Value : `No exact match. Heuristic: ${raw}`;
  out.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  setText("askStatus", match ? "Exact Match" : "Heuristic Output");
  log(`Inference executed for key "${raw}".`, "default");
}

function toDataUrl(content, mimeType) {
  return `data:${mimeType};charset=utf-8,${encodeURIComponent(content)}`;
}

function downloadText(filename, text, mimeType = "text/plain") {
  const link = document.createElement("a");
  link.href = toDataUrl(text, mimeType);
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
}

function exportModel(kind) {
  const readable = generateHumanAlgorithm();
  if (kind === "py") {
    const py = `# Flux export v${state.appVersion}\nalgorithm = """\n${readable}\n"""\n`;
    downloadText("flux_algorithm.py", py, "text/x-python");
  } else {
    const js = `// Flux export v${state.appVersion}\nexport const algorithm = ${JSON.stringify(readable)};\n`;
    downloadText("flux_algorithm.js", js, "text/javascript");
  }
  log(`Exported ${kind.toUpperCase()} SDK template.`, "success");
}

function resolveDataPath(relativePath) {
  return new URL(relativePath, window.location.href).toString();
}

async function loadExample(id) {
  const paths = {
    animals: "data/animals.json",
    taxonomy: "data/taxonomy.json",
    lexicon: "data/lexicon.json",
    market: "data/market_linear.json",
    solar: "data/solar_system.json",
    slingshot: "data/slingshot_data.json",
  };
  const path = paths[id];
  if (!path) {
    log(`Preset "${id}" not found.`, "error");
    return;
  }
  try {
    log(`Loading preset "${id}"...`, "system");
    const response = await fetch(resolveDataPath(path), { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    const normalized = normalizeDataset(Array.isArray(data) ? data : Object.values(data));
    setValue("datasetInput", JSON.stringify(normalized, null, 2));
    updateDatasetState(normalized, `${id}.json`);
    $("exampleModal")?.classList.add("hidden");
  } catch (error) {
    log(`Preset load failed: ${error.message}`, "error");
  }
}

function fileToText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("Failed to read file"));
    reader.readAsText(file);
  });
}

async function handleFileUpload(event) {
  const file = event?.target?.files?.[0];
  if (!file) return;
  try {
    const text = await fileToText(file);
    let parsed = parseDataset(text);
    if (parsed.length === 0 && file.name.toLowerCase().endsWith(".csv")) {
      parsed = text
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line, i) => {
          const [key, value] = line.split(",");
          return { Key: key ?? i, Value: value ?? "" };
        });
    }
    if (parsed.length === 0) {
      throw new Error("Unsupported file format or empty payload");
    }
    const normalized = normalizeDataset(parsed);
    setValue("datasetInput", JSON.stringify(normalized, null, 2));
    updateDatasetState(normalized, file.name);
  } catch (error) {
    log(`File ingest failed: ${error.message}`, "error");
  }
}

function setTheme(themeClass) {
  const root = $("appRoot");
  if (!root) return;
  root.classList.remove("theme-cyber", "theme-matrix", "theme-solar", "theme-arctic", "theme-comfort");
  root.classList.add(themeClass);
  state.activeTheme = themeClass;
  document.querySelectorAll(".theme-pill").forEach((pill) => {
    pill.classList.toggle("active", pill.dataset.theme === themeClass);
  });
  log(`Theme switched to ${themeClass.replace("theme-", "")}.`, "default");
}

function togglePanel(panel) {
  const slidePanel = $("slidePanel");
  if (!slidePanel) return;
  if (uiState.activePanel === panel && !slidePanel.classList.contains("collapsed")) {
    slidePanel.classList.add("collapsed");
    return;
  }
  slidePanel.classList.remove("collapsed");
  uiState.activePanel = panel;
  document.querySelectorAll(".icon-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.panel === panel);
  });
  document.querySelectorAll(".panel-section").forEach((section) => {
    section.classList.toggle("active", section.dataset.panelSection === panel);
  });
}

function setMode(mode) {
  document.querySelectorAll(".mode-pill").forEach((pill) => {
    pill.classList.toggle("active", pill.dataset.mode === mode);
  });
  $("askPanel")?.classList.toggle("hidden", mode !== "ask");
  $("fitnessCard")?.classList.toggle("hidden", mode === "ask");
  $("leaderboardCard")?.classList.toggle("hidden", mode === "ask");
  log(`Kernel mode set to ${mode.toUpperCase()}.`, "system");
}

function stepTraining() {
  if (!state.running) return;
  state.generation += 1;
  const improvement = (1 - state.best) * (0.014 + Math.random() * 0.03);
  state.best = clamp01(state.best + improvement);
  state.history.push(state.best);
  setText("genLabel", `GEN ${state.generation}`);
  setText("bestLabel", `${(state.best * 100).toFixed(2)}%`);
  updateLeaderboard();

  if (state.generation % 10 === 0) {
    log(`Epoch ${state.generation}: best=${(state.best * 100).toFixed(2)}%`, "default");
  }

  const stopOnTarget = $("stopOnTarget")?.checked ?? false;
  if (state.generation >= state.maxGenerations || (stopOnTarget && state.best >= state.targetAccuracy)) {
    stopTraining();
    log("Simulation complete. Target reached or max generations hit.", "success");
  }
}

function startTraining() {
  syncNumericSettings();
  if (state.dataset.length === 0) {
    log("Cannot start: load dataset first.", "error");
    togglePanel("files");
    return;
  }
  state.running = true;
  state.generation = 0;
  state.best = 0;
  state.history = [];
  state.historyDisplay = [];
  $("appRoot")?.classList.add("training-running");
  updateStatus("Training");
  if (state.interval) clearInterval(state.interval);
  state.interval = setInterval(stepTraining, 160);
  log("Evolution kernel started.", "system");
}

function stopTraining() {
  state.running = false;
  $("appRoot")?.classList.remove("training-running");
  if (state.interval) clearInterval(state.interval);
  state.interval = null;
  updateStatus("System Standby");
}

function setGuideStep(index) {
  const normalized = ((index % guideSteps.length) + guideSteps.length) % guideSteps.length;
  uiState.guideIndex = normalized;
  const step = guideSteps[normalized];
  setText("guideTitle", step.title);
  setText("guideText", step.text);
  setText("guideStep", `${normalized + 1}/${guideSteps.length}`);
}

function toggleNodeMap() {
  const nodeMap = $("nodeMap");
  if (!nodeMap) return;
  nodeMap.classList.toggle("hidden");
  if (!nodeMap.classList.contains("hidden")) {
    nodeMap.innerHTML = "";
    for (let i = 0; i < 14; i += 1) {
      const dot = el("span", "node-dot");
      dot.style.left = `${8 + Math.random() * 84}%`;
      dot.style.top = `${8 + Math.random() * 84}%`;
      nodeMap.appendChild(dot);
    }
  }
}

function runAutopilot() {
  if (state.dataset.length === 0) {
    loadExample("animals").then(() => startTraining());
    return;
  }
  startTraining();
}

function triggerCataclysm() {
  if (!state.running) {
    log("Cataclysm requires active training.", "error");
    return;
  }
  state.best = clamp01(state.best * 0.65);
  log("Cataclysm triggered. Fitness dropped, exploration increased.", "error");
}

function applyRewind() {
  const rewind = Number($("rewindSlider")?.value || 0);
  setText("rewindValue", String(rewind));
  if (state.history.length === 0) return;
  const idx = Math.max(0, Math.min(rewind, state.history.length - 1));
  state.generation = idx;
  state.best = state.history[idx] || 0;
  state.history = state.history.slice(0, idx + 1);
  state.historyDisplay = state.historyDisplay.slice(0, idx + 1);
  setText("genLabel", `GEN ${state.generation}`);
  setText("bestLabel", `${(state.best * 100).toFixed(2)}%`);
  log(`Timeline rewound to generation ${idx}.`, "system");
}

function updateApiBadge() {
  const enabled = $("apiToggle")?.checked ?? false;
  const url = `${window.location.origin}${window.location.pathname.replace(/index\.html$/, "")}api/flux`;
  setText("apiUrl", enabled ? url : "Endpoint Disabled");
}

function bindEvents() {
  document.querySelectorAll(".icon-btn").forEach((btn) => {
    btn.addEventListener("click", () => togglePanel(btn.dataset.panel));
  });

  document.querySelectorAll(".theme-pill").forEach((pill) => {
    pill.addEventListener("click", () => setTheme(pill.dataset.theme));
  });

  document.querySelectorAll(".mode-pill").forEach((pill) => {
    pill.addEventListener("click", () => setMode(pill.dataset.mode));
  });

  $("librarySize")?.addEventListener("input", syncNumericSettings);
  $("populationSize")?.addEventListener("change", syncNumericSettings);
  $("genomeLength")?.addEventListener("change", syncNumericSettings);
  $("generationCount")?.addEventListener("change", syncNumericSettings);
  $("accuracyTarget")?.addEventListener("change", syncNumericSettings);
  $("rewindSlider")?.addEventListener("input", () => setText("rewindValue", $("rewindSlider").value));

  $("btnStart")?.addEventListener("click", startTraining);
  $("btnStop")?.addEventListener("click", stopTraining);
  $("btnSample")?.addEventListener("click", () => $("exampleModal")?.classList.remove("hidden"));
  $("btnExampleClose")?.addEventListener("click", () => $("exampleModal")?.classList.add("hidden"));
  $("btnClearConsole")?.addEventListener("click", () => {
    const out = $("consoleOutput");
    if (out) out.innerHTML = "";
  });
  $("btnAutoformat")?.addEventListener("click", autoformatDataset);
  $("btnGenerateHuman")?.addEventListener("click", generateHumanAlgorithm);
  $("btnAsk")?.addEventListener("click", executeInference);
  $("btnExportPy")?.addEventListener("click", () => exportModel("py"));
  $("btnExportJs")?.addEventListener("click", () => exportModel("js"));
  $("btnAutopilot")?.addEventListener("click", runAutopilot);
  $("btnCataclysm")?.addEventListener("click", triggerCataclysm);
  $("btnRewind")?.addEventListener("click", applyRewind);
  $("btnRewindBoost")?.addEventListener("click", () => {
    const slider = $("rewindSlider");
    if (!slider) return;
    slider.value = String(Math.max(0, Number(slider.value) - 15));
    applyRewind();
  });
  $("apiToggle")?.addEventListener("change", updateApiBadge);
  $("btnNodeMap")?.addEventListener("click", toggleNodeMap);
  $("btnGhost")?.addEventListener("click", () => log("Ghost telemetry enabled.", "system"));

  $("btnGuideNext")?.addEventListener("click", () => setGuideStep(uiState.guideIndex + 1));
  $("btnGuidePrev")?.addEventListener("click", () => setGuideStep(uiState.guideIndex - 1));
  $("btnGuideStart")?.addEventListener("click", () => setGuideStep(0));
  $("btnGuideClose")?.addEventListener("click", () => $("guideCard")?.classList.add("hidden"));

  $("fileInput")?.addEventListener("change", handleFileUpload);
  $("datasetInput")?.addEventListener("blur", () => {
    const parsed = parseDataset($("datasetInput").value);
    if (parsed.length > 0) updateDatasetState(parsed, $("fileName")?.textContent || "inline");
  });

  document.querySelectorAll(".example-card").forEach((card) => {
    card.addEventListener("click", () => loadExample(card.dataset.example));
  });

  window.addEventListener("resize", () => refreshChartState());
}

function renderLoop() {
  refreshChartState();
  window.requestAnimationFrame(renderLoop);
}

function init() {
  bindEvents();
  syncNumericSettings();
  updateBuildBadges();
  updateApiBadge();
  setGuideStep(0);
  setTheme(state.activeTheme);
  updateLeaderboard();
  renderLoop();
  log(`Flux kernel v${state.appVersion} ready.`, "system");
}

window.addEventListener("load", init);
