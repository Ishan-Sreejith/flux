const examples = {
  market: {
    data: {
      "1": 12.5,
      "2": 15,
      "3": 17.5,
      "4": 20,
      "5": 22.5,
      "6": 25,
      "7": 27.5,
      "8": 30,
      "9": 32.5,
      "10": 35,
    },
  },
  solar: {
    data: [
      { Key: 1, Value: 15 },
      { Key: 2, Value: 20 },
      { Key: 3, Value: 25 },
      { Key: 4, Value: 30 },
      { Key: 5, Value: 35 },
      { Key: 6, Value: 40 },
      { Key: 7, Value: 45 },
      { Key: 8, Value: 50 },
    ],
  },
  voyager: {
    data: {
      Entry_01: { Key: [10, 12000, 3.3, 900], Value: [2.6, 13200] },
      Entry_02: { Key: [20, 13000, 4.2, 850], Value: [5.8, 14690] },
      Entry_03: { Key: [30, 14000, 5.1, 800], Value: [9.0, 16280] },
      Entry_04: { Key: [40, 15000, 5.97, 750], Value: [12.2, 18000] },
    },
  },
};

const ui = {
  appRoot: document.getElementById("appRoot"),
  themeSelect: document.getElementById("themeSelect"),
  btnTrain: document.getElementById("btnTrain"),
  btnStop: document.getElementById("btnStop"),
  dropZone: document.getElementById("dropZone"),
  fileInput: document.getElementById("fileInput"),
  datasetInput: document.getElementById("datasetInput"),
  datasetStatus: document.getElementById("datasetStatus"),
  statusMessage: document.getElementById("statusMessage"),
  librarySize: document.getElementById("librarySize"),
  libraryValue: document.getElementById("libraryValue"),
  btnLibrary: document.getElementById("btnLibrary"),
  btnToggleDrawer: document.getElementById("btnToggleDrawer"),
  paramDrawer: document.getElementById("paramDrawer"),
  presetGroup: document.getElementById("presetGroup"),
  populationSize: document.getElementById("populationSize"),
  genomeLength: document.getElementById("genomeLength"),
  generationCount: document.getElementById("generationCount"),
  autoConvert: document.getElementById("autoConvert"),
  leaderboardBody: document.getElementById("leaderboardBody"),
  graveyardCount: document.getElementById("graveyardCount"),
  salvageLog: document.getElementById("salvageLog"),
  scoreChart: document.getElementById("scoreChart"),
  algoTitle: document.getElementById("algoTitle"),
  algoCount: document.getElementById("algoCount"),
  algorithmMap: document.getElementById("algorithmMap"),
  algoKeyInput: document.getElementById("algoKeyInput"),
  askInput: document.getElementById("askInput"),
  btnAsk: document.getElementById("btnAsk"),
  askOutput: document.getElementById("askOutput"),
  panelDock: document.getElementById("panelDock"),
  libraryModal: document.getElementById("libraryModal"),
  closeLibrary: document.getElementById("closeLibrary"),
  libraryList: document.getElementById("libraryList"),
  librarySearch: document.getElementById("librarySearch"),
};

let training = false;
let engineState = null;
let bestGenome = null;
let history = { best: [], avg: [] };
let chartCtx = ui.scoreChart.getContext("2d");

function resizeChart() {
  const ratio = window.devicePixelRatio || 1;
  ui.scoreChart.width = ui.scoreChart.clientWidth * ratio;
  ui.scoreChart.height = 180 * ratio;
  chartCtx = ui.scoreChart.getContext("2d");
  chartCtx.scale(ratio, ratio);
}

function drawChart() {
  const w = ui.scoreChart.clientWidth;
  const h = 180;
  chartCtx.clearRect(0, 0, w, h);
  chartCtx.strokeStyle = "#5ee4ff";
  chartCtx.beginPath();
  const max = Math.max(...history.best, ...history.avg, 1);
  history.best.forEach((val, idx) => {
    const x = (idx / Math.max(history.best.length - 1, 1)) * (w - 20) + 10;
    const y = h - (val / max) * (h - 20) - 10;
    if (idx === 0) chartCtx.moveTo(x, y);
    else chartCtx.lineTo(x, y);
  });
  chartCtx.stroke();

  chartCtx.strokeStyle = "#7cffb0";
  chartCtx.beginPath();
  history.avg.forEach((val, idx) => {
    const x = (idx / Math.max(history.avg.length - 1, 1)) * (w - 20) + 10;
    const y = h - (val / max) * (h - 20) - 10;
    if (idx === 0) chartCtx.moveTo(x, y);
    else chartCtx.lineTo(x, y);
  });
  chartCtx.stroke();
}

function parseDataset(text) {
  const data = JSON.parse(text);
  if (Array.isArray(data)) {
    return data.map((item) => ({ key: item.key ?? item.Key, value: item.value ?? item.Value }));
  }
  const samples = [];
  Object.entries(data).forEach(([k, v]) => {
    if (v && typeof v === "object" && "Key" in v && "Value" in v) {
      samples.push({ key: v.Key, value: v.Value });
    } else {
      samples.push({ key: k, value: v });
    }
  });
  return samples;
}

function parseCsv(text) {
  const rows = text.trim().split(/\r?\n/);
  const samples = [];
  rows.forEach((row) => {
    const [key, value] = row.split(",").map((cell) => cell.trim());
    if (key && value !== undefined) {
      samples.push({ key: isNaN(Number(key)) ? key : Number(key), value: isNaN(Number(value)) ? value : Number(value) });
    }
  });
  return samples;
}

function scoreValue(pred, target) {
  if (Array.isArray(target) && Array.isArray(pred)) {
    const paired = target.map((t, i) => scoreValue(pred[i], t));
    return paired.reduce((a, b) => a + b, 0) / paired.length;
  }
  if (typeof target === "number" && typeof pred === "number") {
    return Math.abs(target - pred);
  }
  if (typeof target === "string") {
    return pred === target ? 0 : 1;
  }
  return pred === target ? 0 : 1;
}

function buildParamLibrary(size) {
  const consts = [-10, -5, -2, -1, 1, 2, 5, 10];
  const ops = [
    { name: "identity", fn: (v) => v },
    { name: "add", fn: (v, g, c) => (typeof v === "number" ? v + c * (1 + g.strength) : v) },
    { name: "sub", fn: (v, g, c) => (typeof v === "number" ? v - c * (1 + g.strength) : v) },
    { name: "mul", fn: (v, g, c) => (typeof v === "number" ? v * c * (1 + g.strength) : v) },
    { name: "div", fn: (v, g, c) => (typeof v === "number" ? v / (c * (1 + g.strength)) : v) },
    { name: "first_letter", fn: (v) => String(v)[0] || "" },
    { name: "last_letter", fn: (v) => String(v).slice(-1) },
    { name: "upper", fn: (v) => String(v).toUpperCase() },
    { name: "lower", fn: (v) => String(v).toLowerCase() },
  ];
  const params = [];
  for (let i = 0; i < size; i++) {
    const op = ops[i % ops.length];
    const constant = consts[i % consts.length];
    const fn = (value, gene) => op.fn(value, gene, constant);
    params.push({ id: i + 1, name: op.name, fn });
  }
  return params;
}

function randomGene(allowed) {
  return {
    paramId: allowed[Math.floor(Math.random() * allowed.length)],
    strength: Math.random(),
  };
}

function executeGenome(key, genome, params) {
  let value = key;
  for (const gene of genome) {
    const param = params[gene.paramId - 1];
    try {
      value = param.fn(value, gene);
    } catch {
      return { ok: false, value: null };
    }
  }
  return { ok: true, value };
}

function evaluateAgent(agent, samples, params, tolerance) {
  let total = 0;
  let hits = 0;
  let zeroed = false;
  for (const sample of samples) {
    const result = executeGenome(sample.key, agent.genome, params);
    if (!result.ok) {
      zeroed = true;
      total += 1e9;
      continue;
    }
    const score = scoreValue(result.value, sample.value);
    total += score;
    if (score <= tolerance) hits += 1;
  }
  agent.score = total / samples.length;
  agent.accuracy = hits / samples.length;
  agent.zeroed = zeroed;
}

function evolveGeneration(samples) {
  const params = engineState.params;
  let zeroCount = 0;
  for (const agent of engineState.population) {
    evaluateAgent(agent, samples, params, engineState.tolerance);
    if (agent.zeroed) zeroCount += 1;
  }
  engineState.population.sort((a, b) => a.score - b.score);
  const survivors = engineState.population.slice(0, Math.ceil(engineState.population.length / 2));
  const top10 = engineState.population.slice(0, Math.min(10, engineState.population.length));
  const genePool = top10.flatMap((agent) => agent.genome);
  let salvageEvents = 0;

  const nextGen = survivors.map((agent) => ({
    id: agent.id,
    genome: agent.genome.map((g) => ({ ...g })),
    score: agent.score,
    accuracy: agent.accuracy,
  }));

  while (nextGen.length < engineState.population.length) {
    const parent = survivors[Math.floor(Math.random() * survivors.length)];
    const newGenome = parent.genome.map((gene) => {
      let g = { ...gene };
      if (genePool.length && Math.random() < 0.6) {
        g = { ...genePool[Math.floor(Math.random() * genePool.length)] };
        salvageEvents += 1;
      }
      if (Math.random() < engineState.mutationRate) {
        if (Math.random() < 0.5) {
          g.paramId = engineState.allowed[Math.floor(Math.random() * engineState.allowed.length)];
        }
        g.strength = Math.max(0, Math.min(1, g.strength + (Math.random() - 0.5) * engineState.mutationStrength));
      }
      return g;
    });
    nextGen.push({ id: nextGen.length + 1, genome: newGenome, score: 0, accuracy: 0 });
  }

  engineState.population = nextGen;
  return { best: engineState.population[0], zeroCount, salvageEvents };
}

function renderLeaderboard(agents) {
  ui.leaderboardBody.innerHTML = "";
  const header = document.createElement("div");
  header.className = "leaderboard-header";
  header.innerHTML = "<span>Rank</span><span>Agent</span><span>Fitness</span><span>Genome</span>";
  ui.leaderboardBody.appendChild(header);
  agents.slice(0, 5).forEach((agent, idx) => {
    const row = document.createElement("div");
    row.className = "leaderboard-row";
    if (agent.score <= 0.05) row.classList.add("good");
    else if (agent.score <= 0.5) row.classList.add("warn");
    else row.classList.add("bad");
    row.innerHTML = `
      <span>#${idx + 1}</span>
      <span>A${agent.id}</span>
      <span>${agent.score.toFixed(3)}</span>
      <span>${agent.genome.length}</span>
    `;
    ui.leaderboardBody.appendChild(row);
  });
}

function renderAlgorithm(genome) {
  ui.algorithmMap.innerHTML = "";
  if (!genome || genome.length === 0) {
    ui.algoTitle.textContent = "No genome yet.";
    ui.algoCount.textContent = "0 steps";
    return;
  }
  ui.algoTitle.textContent = "Algorithm Key";
  ui.algoCount.textContent = `${genome.length} steps`;
  ui.algoKeyInput.value = JSON.stringify(genome, null, 2);
  genome.forEach((gene, idx) => {
    const row = document.createElement("div");
    row.className = "algo-card";
    row.innerHTML = `
      <strong>${String(idx + 1).padStart(2, "0")}</strong>
      <div>Param ${gene.paramId}</div>
      <span class="status-blue">strength ${gene.strength.toFixed(2)}</span>
    `;
    ui.algorithmMap.appendChild(row);
  });
}

function updateDrawer() {
  const max = Number(ui.librarySize.value);
  ui.paramDrawer.querySelectorAll(".param-block").forEach((block, idx) => {
    block.classList.toggle("active", idx < max);
  });
}

function initDrawer() {
  ui.paramDrawer.innerHTML = "";
  for (let i = 0; i < 1000; i++) {
    const block = document.createElement("div");
    block.className = "param-block";
    block.style.background = i % 3 === 0 ? "var(--accent)" : i % 3 === 1 ? "var(--accent-2)" : "#ff7a50";
    ui.paramDrawer.appendChild(block);
  }
  updateDrawer();
}

function loadExample(name) {
  const example = examples[name];
  ui.datasetInput.value = JSON.stringify(example.data, null, 2);
  const samples = parseDataset(ui.datasetInput.value);
  ui.datasetStatus.textContent = `${samples.length} samples`;
}

function applyPreset(preset) {
  if (preset === "speed") {
    ui.populationSize.value = 80;
    ui.generationCount.value = 120;
  }
  if (preset === "accuracy") {
    ui.populationSize.value = 200;
    ui.generationCount.value = 300;
  }
  if (preset === "chaos") {
    ui.populationSize.value = 150;
    ui.generationCount.value = 200;
  }
}

function startTraining(samples) {
  const allowed = Array.from({ length: Number(ui.librarySize.value) }, (_, i) => i + 1);
  engineState = {
    params: buildParamLibrary(1000),
    allowed,
    population: Array.from({ length: Number(ui.populationSize.value) }, (_, idx) => ({
      id: idx + 1,
      genome: Array.from({ length: Number(ui.genomeLength.value) }, () => randomGene(allowed)),
      score: 0,
      accuracy: 0,
      zeroed: false,
    })),
    mutationRate: 0.2,
    mutationStrength: 0.35,
    tolerance: 0,
  };
  history = { best: [], avg: [] };
  training = true;
  let gen = 0;
  const maxGen = Number(ui.generationCount.value);

  function step() {
    if (!training || gen >= maxGen) {
      ui.statusMessage.textContent = training ? "Training complete." : "Stopped.";
      return;
    }
    const { best, zeroCount, salvageEvents } = evolveGeneration(samples);
    const avgScore =
      engineState.population.reduce((sum, agent) => sum + agent.score, 0) / engineState.population.length;
    history.best.push(best.score);
    history.avg.push(avgScore);
    renderLeaderboard(engineState.population);
    ui.graveyardCount.textContent = zeroCount;
    if (salvageEvents > 0) {
      ui.salvageLog.textContent = `Salvage injected ${salvageEvents} genes this generation.`;
      ui.salvageLog.className = "log status-red";
    } else {
      ui.salvageLog.className = "log status-blue";
    }
    bestGenome = { genome: best.genome, params: engineState.params };
    renderAlgorithm(best.genome);
    drawChart();
    gen += 1;
    requestAnimationFrame(step);
  }
  step();
}

function askQuestion() {
  const algoKeyRaw = ui.algoKeyInput.value.trim();
  let genomeToUse = bestGenome;
  if (algoKeyRaw) {
    try {
      const parsed = JSON.parse(algoKeyRaw);
      if (Array.isArray(parsed)) {
        genomeToUse = { genome: parsed, params: buildParamLibrary(1000) };
      }
    } catch {
      ui.askOutput.textContent = "Invalid Algorithm Key JSON.";
      return;
    }
  }
  if (!genomeToUse) {
    ui.askOutput.textContent = "Train first or paste an Algorithm Key.";
    return;
  }
  let key;
  const raw = ui.askInput.value.trim();
  if (!raw) return;
  try {
    key = JSON.parse(raw);
  } catch {
    key = raw;
  }
  const result = executeGenome(key, genomeToUse.genome, genomeToUse.params);
  ui.askOutput.textContent = result.ok ? JSON.stringify(result.value) : "Error";
}

ui.themeSelect.addEventListener("change", () => {
  ui.appRoot.className = `workspace ${ui.themeSelect.value}`;
});

ui.librarySize.addEventListener("input", () => {
  ui.libraryValue.textContent = ui.librarySize.value;
  updateDrawer();
});

ui.btnLibrary.addEventListener("click", () => {
  ui.libraryModal.classList.remove("hidden");
  renderLibraryList("");
});

ui.closeLibrary.addEventListener("click", () => {
  ui.libraryModal.classList.add("hidden");
});

ui.btnToggleDrawer.addEventListener("click", () => {
  ui.paramDrawer.classList.toggle("hidden");
});

ui.librarySearch.addEventListener("input", (e) => {
  renderLibraryList(e.target.value);
});

function renderLibraryList(query) {
  const params = buildParamLibrary(1000);
  const filtered = params.filter((p) => p.name.includes(query));
  ui.libraryList.innerHTML = filtered
    .slice(0, 200)
    .map((p) => `<div>Param ${p.id}: ${p.name}</div>`)
    .join("");
}

document.querySelectorAll("[data-close]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const panel = btn.getAttribute("data-close");
    const el = document.querySelector(`[data-panel='${panel}']`);
    if (el) el.classList.add("hidden");
  });
});

document.querySelectorAll("[data-open]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const panel = btn.getAttribute("data-open");
    const el = document.querySelector(`[data-panel='${panel}']`);
    if (el) el.classList.remove("hidden");
  });
});

ui.datasetInput.addEventListener("input", () => {
  try {
    const samples = parseDataset(ui.datasetInput.value);
    ui.datasetStatus.textContent = `${samples.length} samples`;
    ui.statusMessage.textContent = "Dataset loaded.";
  } catch {
    ui.statusMessage.textContent = "Invalid JSON dataset.";
  }
});

ui.fileInput.addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const text = reader.result;
    if (file.name.endsWith(".csv")) {
      const samples = parseCsv(text);
      ui.datasetInput.value = JSON.stringify(samples, null, 2);
      ui.datasetStatus.textContent = `${samples.length} samples`;
    } else {
      ui.datasetInput.value = text;
      ui.datasetStatus.textContent = `${parseDataset(text).length} samples`;
    }
  };
  reader.readAsText(file);
});

ui.btnTrain.addEventListener("click", () => {
  try {
    const samples = parseDataset(ui.datasetInput.value);
    ui.statusMessage.textContent = "Training...";
    startTraining(samples);
  } catch {
    ui.statusMessage.textContent = "Invalid JSON dataset.";
  }
});

ui.btnStop.addEventListener("click", () => {
  training = false;
});

ui.btnAsk.addEventListener("click", askQuestion);

ui.presetGroup.addEventListener("change", (event) => {
  applyPreset(event.target.value);
});

initDrawer();
resizeChart();
window.addEventListener("resize", resizeChart);
loadExample("market");
