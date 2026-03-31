/**
 * Flux Evolver Web IDE v0.3.0
 * Extended UX: persistence, shortcuts, search, progress metrics, cleaner control flow.
 */

const STORAGE_KEY = "flux_evolver_workspace_v3";

const PREBUILT_ALGORITHMS = [
  {
    id: "linear-fast",
    name: "Linear Fastfit",
    summary: "Numeric mapping tuned for monotonic linear datasets.",
    preset: "market",
    config: { population: 180, genome: 6, generations: 260, target: 0.97, library: 420 },
    logic: ["normalize(input)", "derive slope", "predict output = a*x+b", "clamp outliers"],
  },
  {
    id: "taxonomy-encoder",
    name: "Taxonomy Encoder",
    summary: "Text/category mapping for hierarchy labels and semantic grouping.",
    preset: "taxonomy",
    config: { population: 220, genome: 8, generations: 320, target: 0.95, library: 520 },
    logic: ["to_string(input)", "token split", "lookup parent class", "emit category code"],
  },
  {
    id: "orbital-ranker",
    name: "Orbital Ranker",
    summary: "Ranking model for ordered physical systems.",
    preset: "solar",
    config: { population: 160, genome: 7, generations: 280, target: 0.96, library: 460 },
    logic: ["coerce numeric", "weight major feature", "rank against priors", "emit indexed class"],
  },
  {
    id: "lexicon-simplifier",
    name: "Lexicon Simplifier",
    summary: "String transform baseline for lower/replace/shape operations.",
    preset: "lexicon",
    config: { population: 140, genome: 7, generations: 220, target: 0.94, library: 360 },
    logic: ["lowercase", "strip punctuation", "apply replacements", "emit normalized token"],
  },
  {
    id: "classification-sieve",
    name: "Classification Sieve",
    summary: "General-purpose class assignment for mixed symbolic inputs.",
    preset: "animals",
    config: { population: 200, genome: 8, generations: 340, target: 0.95, library: 540 },
    logic: ["tokenize input", "extract features", "score class priors", "emit class id"],
  },
];

const state = {
  running: false,
  interval: null,
  generation: 0,
  best: 0,
  history: [],
  historyDisplay: [],
  historyStartGeneration: 1,
  maxHistoryPoints: 140,
  dataset: [],
  librarySize: 300,
  populationSize: 120,
  genomeLength: 8,
  maxGenerations: 300,
  targetAccuracy: 0.95,
  appVersion: "0.3.0",
  activeTheme: "theme-comfort",
  uiMode: "simple",
  ghostMode: false,
  activePrebuiltId: null,
  prebuiltQuery: "",
  inferenceModel: null,
  lastEpochAt: 0,
  epochRate: 0,
  mutator: {
    lockAll: false,
    banAll: false,
    locked: new Set(),
    banned: new Set(),
    genes: ["add", "sub", "mul", "div", "pow", "mod", "sin", "cos", "clamp", "round", "concat", "replace"],
  },
};

const uiState = {
  activePanel: "settings",
  guideIndex: 0,
};

const guideSteps = [
  { title: "Protocol 1: Data Link", text: "Load a preset or upload a file to initialize the workspace." },
  { title: "Protocol 2: Normalize", text: "Run Autoformat to standardize keys and outputs into clean JSON." },
  { title: "Protocol 3: Library", text: "Pick a prebuilt algorithm and apply its tuned profile." },
  { title: "Protocol 4: Evolve", text: "Start simulation and monitor bounded telemetry progression." },
  { title: "Protocol 5: Export", text: "Export generated logic to Python/JS and reuse it for inference." },
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
  return [now.getHours(), now.getMinutes(), now.getSeconds()].map((v) => String(v).padStart(2, "0")).join(":");
}

function setText(id, value) {
  const node = $(id);
  if (node) node.textContent = value;
}

function setValue(id, value) {
  const node = $(id);
  if (node) node.value = value;
}

function clamp01(v) {
  return Math.max(0, Math.min(1, v));
}

function toFiniteNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function applyUiMode(mode) {
  const root = $("appRoot");
  const shell = $("simpleShell");
  const sidebar = document.querySelector(".sidebar");
  const workspace = document.querySelector(".workspace");
  if (!root) return;
  state.uiMode = mode === "advanced" ? "advanced" : "simple";
  root.classList.toggle("ui-simple", state.uiMode === "simple");
  root.classList.toggle("ui-advanced", state.uiMode === "advanced");
  if (state.uiMode === "simple") {
    if (sidebar) sidebar.style.display = "none";
    if (workspace) workspace.style.display = "none";
    if (shell) {
      shell.classList.remove("hidden");
      shell.style.display = "grid";
    }
  } else {
    if (sidebar) sidebar.style.display = "";
    if (workspace) workspace.style.display = "";
    if (shell) {
      shell.classList.add("hidden");
      shell.style.display = "none";
    }
  }
  const btn = $("btnUiMode");
  if (btn) btn.textContent = state.uiMode === "simple" ? "Switch To Advanced" : "Switch To Simple";
  if (state.uiMode === "simple") {
    showSimpleUploadScreen();
  }
  persistWorkspace(false);
}

function showSimpleUploadScreen() {
  $("simpleUploadScreen")?.classList.remove("hidden");
  $("simpleChatScreen")?.classList.add("hidden");
}

function showSimpleChatScreen() {
  $("simpleUploadScreen")?.classList.add("hidden");
  $("simpleChatScreen")?.classList.remove("hidden");
}

function setSimpleStatus(message) {
  setText("simpleTrainStatus", message);
}

function pushSimpleChatMessage(text, role = "bot") {
  const root = $("simpleChatMessages");
  if (!root) return;
  const bubble = el("div", `chat-bubble ${role}`, text);
  root.appendChild(bubble);
  root.scrollTop = root.scrollHeight;
}

function showToast(message, type = "info") {
  const root = $("toastContainer");
  if (!root) return;
  const item = el("div", `toast ${type}`);
  item.textContent = message;
  root.appendChild(item);
  requestAnimationFrame(() => item.classList.add("show"));
  setTimeout(() => {
    item.classList.remove("show");
    setTimeout(() => item.remove(), 220);
  }, 2200);
}

function log(msg, type = "default") {
  const consoleOut = $("consoleOutput");
  if (!consoleOut) return;
  const line = el("div", `log-line ${type}`);
  line.innerHTML = `<span class="log-time">[${nowTimeString()}]</span> ${msg}`;
  consoleOut.prepend(line);
}

function updateStatus(message) {
  setText("statusMessage", message);
}

function updateBuildBadges() {
  setText("buildVersion", `v${state.appVersion}`);
}

function workspaceSnapshot() {
  return {
    datasetInput: $("datasetInput")?.value || "",
    activeTheme: state.activeTheme,
    uiMode: state.uiMode,
    activePrebuiltId: state.activePrebuiltId,
    settings: {
      populationSize: state.populationSize,
      genomeLength: state.genomeLength,
      maxGenerations: state.maxGenerations,
      targetAccuracy: state.targetAccuracy,
      librarySize: state.librarySize,
    },
    prebuiltQuery: state.prebuiltQuery,
  };
}

function persistWorkspace(showMessage = false) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(workspaceSnapshot()));
    if (showMessage) {
      showToast("Workspace saved", "success");
      log("Workspace saved to local storage.", "success");
    }
  } catch {
    if (showMessage) showToast("Unable to save workspace", "error");
  }
}

function hydrateFromWorkspace() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const data = JSON.parse(raw);
    if (data.settings) {
      if (Number.isFinite(data.settings.populationSize)) setValue("populationSize", data.settings.populationSize);
      if (Number.isFinite(data.settings.genomeLength)) setValue("genomeLength", data.settings.genomeLength);
      if (Number.isFinite(data.settings.maxGenerations)) setValue("generationCount", data.settings.maxGenerations);
      if (Number.isFinite(data.settings.targetAccuracy)) setValue("accuracyTarget", data.settings.targetAccuracy);
      if (Number.isFinite(data.settings.librarySize)) setValue("librarySize", data.settings.librarySize);
    }
    if (typeof data.datasetInput === "string" && data.datasetInput.trim()) {
      setValue("datasetInput", data.datasetInput);
      setValue("simpleDatasetInput", data.datasetInput);
      const parsed = parseDataset(data.datasetInput);
      if (parsed.length > 0) updateDatasetState(parsed, "workspace.json", false);
    }
    if (typeof data.prebuiltQuery === "string") {
      state.prebuiltQuery = data.prebuiltQuery;
      setValue("prebuiltSearch", data.prebuiltQuery);
    }
    if (typeof data.activeTheme === "string") state.activeTheme = data.activeTheme;
    if (data.uiMode === "simple" || data.uiMode === "advanced") state.uiMode = data.uiMode;
    if (typeof data.activePrebuiltId === "string") state.activePrebuiltId = data.activePrebuiltId;
  } catch {
    log("Workspace restoration failed. Starting with defaults.", "error");
  }
}

function resetWorkspace() {
  stopTraining();
  state.history = [];
  state.historyDisplay = [];
  state.historyStartGeneration = 1;
  state.best = 0;
  state.generation = 0;
  state.dataset = [];
  state.prebuiltQuery = "";
  state.activePrebuiltId = null;
  state.inferenceModel = null;
  state.uiMode = "simple";
  setValue("populationSize", 120);
  setValue("genomeLength", 8);
  setValue("generationCount", 300);
  setValue("accuracyTarget", 0.95);
  setValue("librarySize", 300);
  setValue("datasetInput", "");
  setValue("simpleDatasetInput", "");
  setValue("simpleChatInput", "");
  setValue("prebuiltSearch", "");
  setText("fileName", "No source linked");
  setText("datasetStatus", "0 items");
  setText("genLabel", "GEN 0");
  setText("bestLabel", "0.00%");
  setText("progressLabel", "Progress 0.00%");
  setText("epochRate", "0.0 epochs/s");
  const fill = $("progressFill");
  if (fill) fill.style.width = "0%";
  localStorage.removeItem(STORAGE_KEY);
  const chat = $("simpleChatMessages");
  if (chat) chat.innerHTML = "";
  setSimpleStatus("Waiting for dataset...");
  showSimpleUploadScreen();
  syncNumericSettings();
  applyUiMode(state.uiMode);
  renderPrebuiltList();
  updateLeaderboard();
  drawFitness();
  showToast("Workspace reset", "info");
  log("Workspace reset to defaults.", "system");
}

function syncRewindRange() {
  const slider = $("rewindSlider");
  if (!slider) return;
  const max = Math.max(0, state.history.length - 1);
  slider.max = String(max);
  if (Number(slider.value) > max) slider.value = String(max);
  setText("rewindValue", slider.value);
}

function updateProgressUI() {
  const pct = clamp01(state.best) * 100;
  setText("progressLabel", `Progress ${pct.toFixed(2)}%`);
  setText("epochRate", `${state.epochRate.toFixed(1)} epochs/s`);
  const fill = $("progressFill");
  if (fill) fill.style.width = `${pct}%`;
}

function updateLeaderboard() {
  const lb = $("leaderboard");
  if (!lb) return;
  lb.innerHTML = "";
  for (let i = 0; i < 6; i += 1) {
    const row = el("div", "leaderboard-row");
    const fitness = Math.max(0, state.best * 100 - i * 1.4);
    const seq = `P${Math.floor(Math.random() * 250)}:${["add", "mul", "sub", "round"][i % 4]} -> P${Math.floor(Math.random() * 250)}:${["if", "clamp", "div", "pow"][i % 4]}`;
    row.innerHTML = `<span class="rank">#${i + 1}</span><span class="formula">${seq}</span><span class="score">${fitness.toFixed(2)}%</span>`;
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
  const padding = { left: 44, right: 10, top: 10, bottom: 24 };
  const pW = width - padding.left - padding.right;
  const pH = height - padding.top - padding.bottom;

  ctx.strokeStyle = "rgba(255,255,255,0.08)";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i += 1) {
    const y = padding.top + pH * (1 - i / 4);
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
  }
  if (state.historyDisplay.length < 2) return;

  const firstGen = state.historyStartGeneration;
  const lastGen = firstGen + state.historyDisplay.length - 1;
  ctx.fillStyle = "rgba(255,255,255,0.45)";
  ctx.font = "11px JetBrains Mono";
  ctx.fillText(`G${firstGen}`, 6, height - 8);
  ctx.fillText(`G${lastGen}`, Math.max(6, width - 58), height - 8);

  const stepX = pW / (state.historyDisplay.length - 1);
  if (state.ghostMode) {
    ctx.beginPath();
    ctx.lineWidth = 5;
    ctx.strokeStyle = "rgba(0, 210, 255, 0.16)";
    state.historyDisplay.forEach((v, i) => {
      const x = padding.left + i * stepX;
      const y = padding.top + (1 - v) * pH;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  ctx.beginPath();
  ctx.lineWidth = 2.5;
  ctx.strokeStyle = "#00d2ff";
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
    if (state.historyDisplay.length > state.maxHistoryPoints) {
      state.historyDisplay = state.historyDisplay.slice(-state.maxHistoryPoints);
    }
    state.historyDisplay = state.historyDisplay.map((v, i) => v + (state.history[i] - v) * 0.2);
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
  persistWorkspace(false);
}

function parseDataset(raw) {
  const text = String(raw || "").trim();
  if (!text) return [];
  try {
    const parsed = JSON.parse(text);
    if (Array.isArray(parsed)) return parsed;
    if (parsed && typeof parsed === "object") return Object.values(parsed);
  } catch {
    return [];
  }
  return [];
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

function updateDatasetState(data, sourceName = "inline", notify = true) {
  state.dataset = normalizeDataset(data);
  state.inferenceModel = compileInferenceModel(state.dataset);
  setText("datasetStatus", `${state.dataset.length} items`);
  setText("fileName", sourceName);
  if (state.dataset.length > 0) {
    updateStatus("Dataset Linked");
    if (notify) {
      log(`Dataset loaded (${state.dataset.length} rows).`, "success");
      showToast(`Dataset loaded: ${state.dataset.length} rows`, "success");
    }
  } else if (notify) {
    log("Dataset is empty after normalization.", "error");
  }
  generateHumanAlgorithm(false);
  persistWorkspace(false);
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

function compileInferenceModel(dataset) {
  const exactByKey = new Map(dataset.map((row) => [String(row.Key), row.Value]));
  const numericRows = dataset
    .map((row) => ({
      key: toFiniteNumber(row.Key),
      rawKey: row.Key,
      rawValue: row.Value,
      numericValue: toFiniteNumber(row.Value),
    }))
    .filter((row) => row.key !== null)
    .sort((a, b) => a.key - b.key);

  const numericPairs = numericRows.filter((row) => row.numericValue !== null).map((row) => ({ x: row.key, y: row.numericValue }));

  if (numericPairs.length >= 2) {
    const n = numericPairs.length;
    let sumX = 0;
    let sumY = 0;
    let sumXX = 0;
    let sumXY = 0;
    for (const p of numericPairs) {
      sumX += p.x;
      sumY += p.y;
      sumXX += p.x * p.x;
      sumXY += p.x * p.y;
    }
    const denom = n * sumXX - sumX * sumX;
    const slope = Math.abs(denom) < 1e-9 ? 0 : (n * sumXY - sumX * sumY) / denom;
    const intercept = (sumY - slope * sumX) / n;
    const roundOutputs = numericPairs.every((p) => Math.abs(p.y - Math.round(p.y)) < 1e-9);
    return {
      type: "numeric_linear",
      slope,
      intercept,
      roundOutputs,
      minX: Math.min(...numericPairs.map((p) => p.x)),
      maxX: Math.max(...numericPairs.map((p) => p.x)),
      numericRows,
      exactByKey,
    };
  }

  if (numericRows.length >= 1) {
    return {
      type: "numeric_key_lookup",
      minX: numericRows[0].key,
      maxX: numericRows[numericRows.length - 1].key,
      numericRows,
      exactByKey,
    };
  }

  return { type: "lookup", exactByKey };
}

function predictWithModel(key) {
  const k = String(key);
  if (!state.inferenceModel) return { value: `No model available for ${k}`, mode: "heuristic" };
  if (state.inferenceModel.exactByKey.has(k)) {
    return { value: state.inferenceModel.exactByKey.get(k), mode: "exact" };
  }
  if (state.inferenceModel.type === "numeric_linear") {
    const num = toFiniteNumber(key);
    if (num !== null) {
      let predicted = state.inferenceModel.slope * num + state.inferenceModel.intercept;
      if (state.inferenceModel.roundOutputs) predicted = Math.round(predicted);
      return { value: Number(predicted.toFixed(6)), mode: "predicted" };
    }
  }
  if (state.inferenceModel.type === "numeric_key_lookup") {
    const x = toFiniteNumber(key);
    if (x !== null) {
      const rows = state.inferenceModel.numericRows;
      if (rows.length === 1) return { value: rows[0].rawValue, mode: "predicted" };
      let right = rows.findIndex((row) => row.key >= x);
      if (right === -1) right = rows.length - 1;
      const left = Math.max(0, right - 1);
      const a = rows[left];
      const b = rows[Math.min(rows.length - 1, right)];
      if (a.numericValue !== null && b.numericValue !== null && a.key !== b.key) {
        const t = (x - a.key) / (b.key - a.key);
        const y = a.numericValue + t * (b.numericValue - a.numericValue);
        const rounded = Number.isInteger(a.numericValue) && Number.isInteger(b.numericValue);
        return { value: rounded ? Math.round(y) : Number(y.toFixed(6)), mode: "predicted" };
      }
      const nearest = Math.abs(a.key - x) <= Math.abs(b.key - x) ? a : b;
      return { value: nearest.rawValue, mode: "predicted" };
    }
  }
  return { value: `No exact match. Heuristic: ${k}`, mode: "heuristic" };
}

function inferFormulaSteps(dataset) {
  if (!dataset.length || !state.inferenceModel) return ["No deterministic rule inferred from empty dataset."];
  if (state.inferenceModel.type === "numeric_linear") {
    const m = state.inferenceModel.slope.toFixed(6);
    const b = state.inferenceModel.intercept.toFixed(6);
    return [
      "parse key as number",
      "apply learned linear model",
      `compute value = (${m} * x) + (${b})`,
      "return rounded value when target domain is integer",
    ];
  }
  if (state.inferenceModel.type === "numeric_key_lookup") {
    return [
      "parse key as number",
      "locate nearest known key range",
      "interpolate numeric values when available",
      "fallback to nearest known output",
    ];
  }
  return ["coerce key to text", "lookup exact token", "fallback to heuristic output"];
}

function deriveRuleFromDataset(dataset) {
  const logic = inferFormulaSteps(dataset);
  const pairs = dataset.slice(0, 5).map((item) => `${JSON.stringify(item.Key)} -> ${JSON.stringify(item.Value)}`);
  return ["Likely mapping strategy:", ...logic.map((s, i) => `${i + 1}. ${s}`), "", "Sample traces:", ...pairs].join("\n");
}

function generateHumanAlgorithm(notify = true) {
  state.inferenceModel = compileInferenceModel(state.dataset);
  const output = deriveRuleFromDataset(state.dataset);
  const full = $("fullVersionInput");
  if (full) {
    full.classList.remove("hidden");
    full.value = output;
  }
  setValue("algoKeyAsk", output);
  setValue(
    "algoKeyInput",
    JSON.stringify(
      {
        version: state.appVersion,
        prebuilt: state.activePrebuiltId,
        model: state.inferenceModel,
        config: {
          population: state.populationSize,
          genomeLength: state.genomeLength,
          generations: state.maxGenerations,
          targetAccuracy: state.targetAccuracy,
          librarySize: state.librarySize,
        },
      },
      null,
      2
    )
  );
  if (state.inferenceModel?.type === "numeric_linear") {
    const probe = Math.round(state.inferenceModel.maxX + 1);
    setValue("askInput", String(probe));
    setText("askStatus", "Model Ready");
    setText(
      "askOutput",
      `Compiled model: y = ${state.inferenceModel.slope.toFixed(6)}*x + ${state.inferenceModel.intercept.toFixed(6)}`
    );
  } else if (state.inferenceModel?.type === "numeric_key_lookup") {
    const probe = Math.round(state.inferenceModel.maxX + 1);
    setValue("askInput", String(probe));
    setText("askStatus", "Model Ready");
    setText("askOutput", "Compiled numeric-key model (interpolation + nearest fallback).");
  } else {
    const firstKey = state.dataset[0]?.Key;
    if (firstKey !== undefined) setValue("askInput", String(firstKey));
    setText("askStatus", "Model Ready");
    setText("askOutput", "Compiled lookup model from current dataset.");
  }
  if (notify) log("Generated human-readable algorithm draft.", "system");
  return output;
}

function updatePlayback(key, value) {
  const playback = $("formulaPlayback");
  if (!playback) return;
  const steps = inferFormulaSteps(state.dataset);
  playback.innerHTML = "";
  playback.appendChild(el("div", "playback-title", `Input: ${JSON.stringify(key)}`));
  steps.forEach((step, i) => playback.appendChild(el("div", "playback-step", `${i + 1}. ${step}`)));
  playback.appendChild(el("div", "playback-result", `Output: ${JSON.stringify(value)}`));
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
  const predicted = predictWithModel(key);
  const value = predicted.value;
  out.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  setText(
    "askStatus",
    predicted.mode === "exact" ? "Exact Match" : predicted.mode === "predicted" ? "Predicted Output" : "Heuristic Output"
  );
  updatePlayback(key, value);
  log(`Inference executed for key "${raw}" (${predicted.mode}).`, "default");
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
  const readable = generateHumanAlgorithm(false);
  if (kind === "py") {
    downloadText("flux_algorithm.py", `# Flux export v${state.appVersion}\nalgorithm = """\n${readable}\n"""\n`, "text/x-python");
  } else {
    downloadText("flux_algorithm.js", `// Flux export v${state.appVersion}\nexport const algorithm = ${JSON.stringify(readable)};\n`, "text/javascript");
  }
  showToast(`${kind.toUpperCase()} export ready`, "success");
  log(`Exported ${kind.toUpperCase()} SDK template.`, "success");
}

function resolveDataPath(relativePath) {
  return new URL(relativePath, window.location.href).toString();
}

async function loadExample(id, notify = true) {
  const paths = {
    animals: "data/animals.json",
    taxonomy: "data/taxonomy.json",
    lexicon: "data/lexicon.json",
    market: "data/market_linear.json",
    solar: "data/solar_system.json",
    slingshot: "data/slingshot_data.json",
  };
  const path = paths[id];
  if (!path) return;
  try {
    const response = await fetch(resolveDataPath(path), { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    const normalized = normalizeDataset(Array.isArray(data) ? data : Object.values(data));
    setValue("datasetInput", JSON.stringify(normalized, null, 2));
    updateDatasetState(normalized, `${id}.json`, notify);
    $("exampleModal")?.classList.add("hidden");
  } catch (error) {
    log(`Preset load failed: ${error.message}`, "error");
    showToast("Preset load failed", "error");
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

function showMapperModal(fileName, sampleColumns) {
  const modal = $("mapperModal");
  const grid = $("mapperGrid");
  if (!modal || !grid) return;
  grid.innerHTML = "";
  sampleColumns.forEach((col) => {
    const row = el("div", "mapper-row");
    row.innerHTML = `
      <span class="mapper-col">${col}</span>
      <select class="mapper-select">
        <option value="feature">Feature</option>
        <option value="key">Key</option>
        <option value="value">Value</option>
        <option value="ignore">Ignore</option>
      </select>
    `;
    grid.appendChild(row);
  });
  modal.classList.remove("hidden");
  log(`Detected tabular data in "${fileName}". Mapper opened.`, "system");
}

async function handleFileUpload(event) {
  const file = event?.target?.files?.[0];
  if (!file) return;
  try {
    const text = await fileToText(file);
    let parsed = parseDataset(text);
    if (parsed.length === 0 && file.name.toLowerCase().endsWith(".csv")) {
      const rows = text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
      if (rows.length > 1) {
        const headers = rows[0].split(",").map((h) => h.trim());
        parsed = rows.slice(1).map((row, i) => {
          const cells = row.split(",").map((c) => c.trim());
          return { Key: cells[0] ?? i, Value: cells[1] ?? "" };
        });
        showMapperModal(file.name, headers);
      }
    }
    if (parsed.length === 0) throw new Error("Unsupported file format or empty payload");
    const normalized = normalizeDataset(parsed);
    setValue("datasetInput", JSON.stringify(normalized, null, 2));
    updateDatasetState(normalized, file.name);
  } catch (error) {
    log(`File ingest failed: ${error.message}`, "error");
    showToast("File ingest failed", "error");
  }
}

async function loadSimpleFileIntoTextbox() {
  const file = $("simpleFileInput")?.files?.[0];
  if (!file) return;
  try {
    const text = await fileToText(file);
    setValue("simpleDatasetInput", text);
    setSimpleStatus(`Loaded file: ${file.name}`);
  } catch {
    setSimpleStatus("Unable to read selected file.");
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function submitSimpleDataset() {
  const raw = $("simpleDatasetInput")?.value?.trim() || "";
  if (!raw) {
    setSimpleStatus("Paste JSON or choose a file before submitting.");
    showToast("Missing dataset", "error");
    return;
  }
  let parsed = parseDataset(raw);
  if (parsed.length === 0) {
    setSimpleStatus("JSON format is invalid or empty.");
    showToast("Invalid JSON", "error");
    return;
  }

  setSimpleStatus("Validating dataset...");
  await sleep(250);
  setSimpleStatus("Training model (25%)...");
  await sleep(250);
  setSimpleStatus("Training model (55%)...");
  await sleep(250);
  setSimpleStatus("Training model (85%)...");
  await sleep(250);

  updateDatasetState(parsed, "simple-upload.json", false);
  setValue("datasetInput", JSON.stringify(normalizeDataset(parsed), null, 2));
  generateHumanAlgorithm(false);

  const modelKind = state.inferenceModel?.type || "lookup";
  setText("simpleChatMeta", `Model: ${modelKind}`);
  const chat = $("simpleChatMessages");
  if (chat) chat.innerHTML = "";
  pushSimpleChatMessage("Model is ready. Ask for any key and I will predict the value.");
  if (state.inferenceModel?.type === "numeric_linear" || state.inferenceModel?.type === "numeric_key_lookup") {
    pushSimpleChatMessage("Unseen numeric keys are supported using extrapolation/interpolation.");
  }
  showSimpleChatScreen();
  setSimpleStatus("Training complete.");
}

function sendSimpleChat() {
  const input = $("simpleChatInput");
  if (!input) return;
  const raw = input.value.trim();
  if (!raw) return;
  pushSimpleChatMessage(raw, "user");
  input.value = "";
  const key = Number.isNaN(Number(raw)) ? raw : Number(raw);
  const predicted = predictWithModel(key);
  const text = typeof predicted.value === "string" ? predicted.value : JSON.stringify(predicted.value);
  pushSimpleChatMessage(text, "bot");
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
  persistWorkspace(false);
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
  document.querySelectorAll(".icon-btn").forEach((btn) => btn.classList.toggle("active", btn.dataset.panel === panel));
  document.querySelectorAll(".panel-section").forEach((section) => section.classList.toggle("active", section.dataset.panelSection === panel));
}

function setMode(mode) {
  document.querySelectorAll(".mode-pill").forEach((pill) => pill.classList.toggle("active", pill.dataset.mode === mode));
  $("askPanel")?.classList.toggle("hidden", mode !== "ask");
  $("fitnessCard")?.classList.toggle("hidden", mode === "ask");
  $("leaderboardCard")?.classList.toggle("hidden", mode === "ask");
}

function applyMutatorEffect(baseImprovement) {
  if (state.mutator.banAll) return baseImprovement * 0.6;
  let multiplier = 1;
  multiplier += state.mutator.locked.size * 0.004;
  multiplier -= state.mutator.banned.size * 0.003;
  return Math.max(0.001, baseImprovement * multiplier);
}

function pushHistoryPoint(value) {
  state.history.push(value);
  if (state.history.length > state.maxHistoryPoints) {
    state.history.shift();
    state.historyDisplay.shift();
    state.historyStartGeneration += 1;
  }
  syncRewindRange();
}

function stepTraining() {
  if (!state.running) return;
  const now = performance.now();
  if (state.lastEpochAt > 0) {
    const dt = Math.max(1, now - state.lastEpochAt);
    const instant = 1000 / dt;
    state.epochRate = state.epochRate === 0 ? instant : state.epochRate * 0.8 + instant * 0.2;
  }
  state.lastEpochAt = now;

  state.generation += 1;
  const base = (1 - state.best) * (0.01 + Math.random() * 0.026);
  state.best = clamp01(state.best + applyMutatorEffect(base));
  pushHistoryPoint(state.best);
  setText("genLabel", `GEN ${state.generation}`);
  setText("bestLabel", `${(state.best * 100).toFixed(2)}%`);
  updateProgressUI();
  updateLeaderboard();

  const stopOnTarget = $("stopOnTarget")?.checked ?? false;
  if (state.generation >= state.maxGenerations || (stopOnTarget && state.best >= state.targetAccuracy)) {
    stopTraining();
    log("Simulation complete. Target reached or max generations hit.", "success");
    showToast("Training complete", "success");
  }
}

function startTraining() {
  syncNumericSettings();
  if (state.dataset.length === 0) {
    showToast("Load a dataset first", "error");
    togglePanel("files");
    return;
  }
  state.running = true;
  state.generation = 0;
  state.best = 0;
  state.history = [];
  state.historyDisplay = [];
  state.historyStartGeneration = 1;
  state.lastEpochAt = 0;
  state.epochRate = 0;
  $("appRoot")?.classList.add("training-running");
  updateStatus("Training");
  updateProgressUI();
  syncRewindRange();
  if (state.interval) clearInterval(state.interval);
  state.interval = setInterval(stepTraining, 160);
  showToast("Training started", "info");
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
    for (let i = 0; i < 16; i += 1) {
      const dot = el("span", "node-dot");
      dot.style.left = `${8 + Math.random() * 84}%`;
      dot.style.top = `${8 + Math.random() * 84}%`;
      nodeMap.appendChild(dot);
    }
  }
}

function runAutopilot() {
  if (state.dataset.length === 0) loadExample("animals", false).then(() => startTraining());
  else startTraining();
}

function triggerCataclysm() {
  if (!state.running) {
    showToast("Start training first", "error");
    return;
  }
  state.best = clamp01(state.best * 0.65);
  if (state.history.length > 0) state.history[state.history.length - 1] = state.best;
  updateProgressUI();
  log("Cataclysm triggered. Fitness dropped.", "error");
}

function applyRewind() {
  const rewind = Number($("rewindSlider")?.value || 0);
  setText("rewindValue", String(rewind));
  if (state.history.length === 0) return;
  const idx = Math.max(0, Math.min(rewind, state.history.length - 1));
  const absoluteGen = state.historyStartGeneration + idx;
  state.generation = absoluteGen;
  state.best = state.history[idx] || 0;
  state.history = state.history.slice(0, idx + 1);
  state.historyDisplay = state.historyDisplay.slice(0, idx + 1);
  setText("genLabel", `GEN ${state.generation}`);
  setText("bestLabel", `${(state.best * 100).toFixed(2)}%`);
  updateProgressUI();
  syncRewindRange();
}

function updateApiBadge() {
  const enabled = $("apiToggle")?.checked ?? false;
  const url = `${window.location.origin}${window.location.pathname.replace(/index\.html$/, "")}api/flux`;
  setText("apiUrl", enabled ? url : "Endpoint Disabled");
}

function setMutatorMode(mode) {
  if (mode === "lockAll") {
    state.mutator.lockAll = true;
    state.mutator.banAll = false;
    state.mutator.locked = new Set(state.mutator.genes);
    state.mutator.banned.clear();
  } else if (mode === "banAll") {
    state.mutator.banAll = true;
    state.mutator.lockAll = false;
    state.mutator.banned = new Set(state.mutator.genes);
    state.mutator.locked.clear();
  } else {
    state.mutator.banAll = false;
    state.mutator.lockAll = false;
    state.mutator.locked.clear();
    state.mutator.banned.clear();
  }
  renderMutatorGrid();
}

function renderMutatorGrid() {
  const grid = $("mutatorGrid");
  if (!grid) return;
  grid.innerHTML = "";
  state.mutator.genes.forEach((gene) => {
    const btn = el("button", "tiny mutator-chip", gene);
    if (state.mutator.locked.has(gene)) btn.classList.add("locked");
    if (state.mutator.banned.has(gene)) btn.classList.add("banned");
    btn.addEventListener("click", () => {
      if (state.mutator.banned.has(gene)) state.mutator.banned.delete(gene);
      else if (state.mutator.locked.has(gene)) {
        state.mutator.locked.delete(gene);
        state.mutator.banned.add(gene);
      } else state.mutator.locked.add(gene);
      renderMutatorGrid();
    });
    grid.appendChild(btn);
  });
}

function filteredPrebuilts() {
  const q = state.prebuiltQuery.trim().toLowerCase();
  if (!q) return PREBUILT_ALGORITHMS;
  return PREBUILT_ALGORITHMS.filter((item) =>
    `${item.name} ${item.summary} ${item.preset} ${item.logic.join(" ")}`.toLowerCase().includes(q)
  );
}

function renderPrebuiltList() {
  const root = $("prebuiltList");
  if (!root) return;
  root.innerHTML = "";
  const list = filteredPrebuilts();
  if (list.length === 0) {
    root.appendChild(el("div", "prebuilt-empty", "No matching prebuilt profiles."));
    return;
  }
  list.forEach((item) => {
    const card = el("article", "prebuilt-card");
    if (state.activePrebuiltId === item.id) card.classList.add("active");
    card.innerHTML = `
      <div class="prebuilt-head">
        <h4>${item.name}</h4>
        <span class="badge">${item.preset}</span>
      </div>
      <p>${item.summary}</p>
      <div class="prebuilt-logic">${item.logic.join(" -> ")}</div>
      <div class="prebuilt-actions">
        <button class="tiny" data-prebuilt-action="apply" data-id="${item.id}">Apply Profile</button>
        <button class="tiny" data-prebuilt-action="run" data-id="${item.id}">Load + Run</button>
      </div>
    `;
    root.appendChild(card);
  });
  root.querySelectorAll("button[data-prebuilt-action]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const picked = PREBUILT_ALGORITHMS.find((p) => p.id === btn.dataset.id);
      if (!picked) return;
      applyPrebuilt(picked, btn.dataset.prebuiltAction === "run");
    });
  });
}

function applyPrebuilt(item, autorun) {
  state.activePrebuiltId = item.id;
  setValue("populationSize", item.config.population);
  setValue("genomeLength", item.config.genome);
  setValue("generationCount", item.config.generations);
  setValue("accuracyTarget", item.config.target);
  setValue("librarySize", item.config.library);
  syncNumericSettings();
  generateHumanAlgorithm(false);
  renderPrebuiltList();
  togglePanel("library");
  loadExample(item.preset, false).then(() => {
    showToast(`Applied ${item.name}`, "success");
    if (autorun) startTraining();
  });
}

function closeMapperModal() {
  $("mapperModal")?.classList.add("hidden");
}

function closeAllModals() {
  $("mapperModal")?.classList.add("hidden");
  $("exampleModal")?.classList.add("hidden");
  $("shortcutsModal")?.classList.add("hidden");
}

function copyAlgorithmKeys() {
  const text = `${$("algoKeyAsk")?.value || ""}\n\n${$("algoKeyInput")?.value || ""}`;
  if (!text.trim()) {
    showToast("No keys available", "error");
    return;
  }
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(text).then(
      () => showToast("Algorithm keys copied", "success"),
      () => showToast("Clipboard unavailable", "error")
    );
    return;
  }
  showToast("Clipboard unavailable", "error");
}

function bindShortcuts() {
  document.addEventListener("keydown", (event) => {
    const cmd = event.metaKey || event.ctrlKey;
    if (event.key === "Escape") {
      closeAllModals();
      return;
    }
    if (cmd && event.key === "Enter") {
      event.preventDefault();
      if (state.running) stopTraining();
      else startTraining();
      return;
    }
    if (cmd && event.key.toLowerCase() === "k") {
      event.preventDefault();
      togglePanel("library");
      $("prebuiltSearch")?.focus();
      return;
    }
    if (cmd && event.key.toLowerCase() === "s") {
      event.preventDefault();
      persistWorkspace(true);
    }
  });
}

function bindEvents() {
  document.querySelectorAll(".icon-btn").forEach((btn) => btn.addEventListener("click", () => togglePanel(btn.dataset.panel)));
  document.querySelectorAll(".theme-pill").forEach((pill) => pill.addEventListener("click", () => setTheme(pill.dataset.theme)));
  document.querySelectorAll(".mode-pill").forEach((pill) => pill.addEventListener("click", () => setMode(pill.dataset.mode)));

  $("librarySize")?.addEventListener("input", syncNumericSettings);
  $("populationSize")?.addEventListener("change", syncNumericSettings);
  $("genomeLength")?.addEventListener("change", syncNumericSettings);
  $("generationCount")?.addEventListener("change", syncNumericSettings);
  $("accuracyTarget")?.addEventListener("change", syncNumericSettings);
  $("rewindSlider")?.addEventListener("input", () => setText("rewindValue", $("rewindSlider").value));
  $("prebuiltSearch")?.addEventListener("input", () => {
    state.prebuiltQuery = $("prebuiltSearch").value;
    persistWorkspace(false);
    renderPrebuiltList();
  });

  $("btnStart")?.addEventListener("click", startTraining);
  $("btnStop")?.addEventListener("click", stopTraining);
  $("btnAutopilot")?.addEventListener("click", runAutopilot);
  $("btnCataclysm")?.addEventListener("click", triggerCataclysm);
  $("btnRewind")?.addEventListener("click", applyRewind);
  $("btnRewindBoost")?.addEventListener("click", () => {
    const slider = $("rewindSlider");
    if (!slider) return;
    slider.value = String(Math.max(0, Number(slider.value) - 15));
    applyRewind();
  });

  $("btnSample")?.addEventListener("click", () => $("exampleModal")?.classList.remove("hidden"));
  $("btnExampleClose")?.addEventListener("click", () => $("exampleModal")?.classList.add("hidden"));
  $("btnShortcuts")?.addEventListener("click", () => $("shortcutsModal")?.classList.remove("hidden"));
  $("btnShortcutsClose")?.addEventListener("click", () => $("shortcutsModal")?.classList.add("hidden"));
  $("btnUiMode")?.addEventListener("click", () => applyUiMode(state.uiMode === "simple" ? "advanced" : "simple"));
  $("btnSaveWorkspace")?.addEventListener("click", () => persistWorkspace(true));
  $("btnResetWorkspace")?.addEventListener("click", resetWorkspace);

  $("simpleFileInput")?.addEventListener("change", loadSimpleFileIntoTextbox);
  $("btnSimpleSubmit")?.addEventListener("click", submitSimpleDataset);
  $("btnSimpleSend")?.addEventListener("click", sendSimpleChat);
  $("simpleChatInput")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") sendSimpleChat();
  });
  $("btnSimpleBack")?.addEventListener("click", showSimpleUploadScreen);

  $("btnClearConsole")?.addEventListener("click", () => {
    const out = $("consoleOutput");
    if (out) out.innerHTML = "";
  });
  $("btnAutoformat")?.addEventListener("click", autoformatDataset);
  $("btnGenerateHuman")?.addEventListener("click", () => generateHumanAlgorithm(true));
  $("btnCopyAlgo")?.addEventListener("click", copyAlgorithmKeys);
  $("btnAsk")?.addEventListener("click", executeInference);
  $("askInput")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") executeInference();
  });
  $("btnExportPy")?.addEventListener("click", () => exportModel("py"));
  $("btnExportJs")?.addEventListener("click", () => exportModel("js"));

  $("apiToggle")?.addEventListener("change", updateApiBadge);
  $("btnNodeMap")?.addEventListener("click", toggleNodeMap);
  $("btnGhost")?.addEventListener("click", () => {
    state.ghostMode = !state.ghostMode;
    $("btnGhost")?.classList.toggle("active", state.ghostMode);
  });

  $("btnLockAll")?.addEventListener("click", () => setMutatorMode("lockAll"));
  $("btnBanAll")?.addEventListener("click", () => setMutatorMode("banAll"));
  $("btnClearLocks")?.addEventListener("click", () => setMutatorMode("clear"));

  $("btnGuideNext")?.addEventListener("click", () => setGuideStep(uiState.guideIndex + 1));
  $("btnGuidePrev")?.addEventListener("click", () => setGuideStep(uiState.guideIndex - 1));
  $("btnGuideStart")?.addEventListener("click", () => {
    $("guideCard")?.classList.remove("hidden");
    setGuideStep(0);
  });
  $("btnGuideClose")?.addEventListener("click", () => $("guideCard")?.classList.add("hidden"));

  $("fileInput")?.addEventListener("change", handleFileUpload);
  $("datasetInput")?.addEventListener("blur", () => {
    const parsed = parseDataset($("datasetInput").value);
    if (parsed.length > 0) updateDatasetState(parsed, $("fileName")?.textContent || "inline", false);
    persistWorkspace(false);
  });

  document.querySelectorAll(".example-card").forEach((card) => card.addEventListener("click", () => loadExample(card.dataset.example)));

  $("btnMapperClose")?.addEventListener("click", closeMapperModal);
  $("btnMapperApply")?.addEventListener("click", () => {
    closeMapperModal();
    showToast("Mapper settings applied", "success");
  });

  window.addEventListener("resize", refreshChartState);
  bindShortcuts();
}

function renderLoop() {
  refreshChartState();
  window.requestAnimationFrame(renderLoop);
}

function init() {
  bindEvents();
  hydrateFromWorkspace();
  syncNumericSettings();
  updateBuildBadges();
  updateApiBadge();
  setGuideStep(0);
  setTheme(state.activeTheme);
  applyUiMode(state.uiMode);
  renderMutatorGrid();
  renderPrebuiltList();
  updateLeaderboard();
  generateHumanAlgorithm(false);
  setSimpleStatus("Waiting for dataset...");
  updateProgressUI();
  syncRewindRange();
  renderLoop();
  log(`Flux kernel v${state.appVersion} ready.`, "system");
}

window.addEventListener("load", init);
