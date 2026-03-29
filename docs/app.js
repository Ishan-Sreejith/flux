const examples = {
  market: {
    description: "Linear numeric demo",
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
    description: "Planet index (synthetic)",
    data: [
      { key: 1, value: 15 },
      { key: 2, value: 20 },
      { key: 3, value: 25 },
      { key: 4, value: 30 },
      { key: 5, value: 35 },
      { key: 6, value: 40 },
      { key: 7, value: 45 },
      { key: 8, value: 50 },
    ],
  },
  voyager: {
    description: "Vector output demo",
    data: {
      Entry_01: { Key: [10, 12000, 3.3, 900], Value: [2.6, 13200] },
      Entry_02: { Key: [20, 13000, 4.2, 850], Value: [5.8, 14690] },
      Entry_03: { Key: [30, 14000, 5.1, 800], Value: [9.0, 16280] },
      Entry_04: { Key: [40, 15000, 5.97, 750], Value: [12.2, 18000] },
      Entry_05: { Key: [50, 15500, 6.5, 700], Value: [14.8, 19600] },
      Entry_06: { Key: [60, 16000, 7.2, 650], Value: [17.6, 21420] },
    },
  },
};

const ui = {
  datasetInput: document.getElementById("datasetInput"),
  datasetStatus: document.getElementById("datasetStatus"),
  statusMessage: document.getElementById("statusMessage"),
  themeSelect: document.getElementById("themeSelect"),
  appRoot: document.getElementById("appRoot"),
  exampleSelect: document.getElementById("exampleSelect"),
  btnLoadExample: document.getElementById("btnLoadExample"),
  librarySize: document.getElementById("librarySize"),
  libraryValue: document.getElementById("libraryValue"),
  modeSelect: document.getElementById("modeSelect"),
  populationSize: document.getElementById("populationSize"),
  generationCount: document.getElementById("generationCount"),
  initialRandomness: document.getElementById("initialRandomness"),
  btnTrain: document.getElementById("btnTrain"),
  btnStop: document.getElementById("btnStop"),
  bestScore: document.getElementById("bestScore"),
  currentGen: document.getElementById("currentGen"),
  trainStatus: document.getElementById("trainStatus"),
  algorithmMap: document.getElementById("algorithmMap"),
  askInput: document.getElementById("askInput"),
  btnAsk: document.getElementById("btnAsk"),
  askOutput: document.getElementById("askOutput"),
  scoreChart: document.getElementById("scoreChart"),
  algoTitle: document.getElementById("algoTitle"),
  algoCount: document.getElementById("algoCount"),
};

let training = false;
let bestGenome = null;
let history = [];
let chartCtx = ui.scoreChart.getContext("2d");
let engineState = null;

function resizeChart() {
  ui.scoreChart.width = ui.scoreChart.clientWidth * window.devicePixelRatio;
  ui.scoreChart.height = 160 * window.devicePixelRatio;
  chartCtx = ui.scoreChart.getContext("2d");
  chartCtx.scale(window.devicePixelRatio, window.devicePixelRatio);
}

function drawChart() {
  const w = ui.scoreChart.clientWidth;
  const h = 160;
  chartCtx.clearRect(0, 0, w, h);
  chartCtx.strokeStyle = "#5ee4ff";
  chartCtx.beginPath();
  const max = Math.max(...history, 1);
  history.forEach((val, idx) => {
    const x = (idx / Math.max(history.length - 1, 1)) * (w - 20) + 10;
    const y = h - (val / max) * (h - 20) - 10;
    if (idx === 0) {
      chartCtx.moveTo(x, y);
    } else {
      chartCtx.lineTo(x, y);
    }
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

function scoreValue(pred, target) {
  if (Array.isArray(target) && Array.isArray(pred)) {
    const lenPenalty = Math.abs(target.length - pred.length);
    const pairs = target.map((t, i) => scoreValue(pred[i], t));
    return (pairs.reduce((a, b) => a + b, 0) / pairs.length) + lenPenalty;
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
    { name: "identity", fn: (v) => v, category: "core" },
    { name: "to_float", fn: (v) => (typeof v === "number" ? v : parseFloat(v)), category: "math" },
    { name: "add", fn: (v, g, c) => (typeof v === "number" ? v + c * (1 + g.strength) : v), category: "math" },
    { name: "mul", fn: (v, g, c) => (typeof v === "number" ? v * c * (1 + g.strength) : v), category: "math" },
    { name: "sin", fn: (v) => (typeof v === "number" ? Math.sin(v) : v), category: "math" },
    { name: "cos", fn: (v) => (typeof v === "number" ? Math.cos(v) : v), category: "math" },
    { name: "upper", fn: (v) => (typeof v === "string" ? v.toUpperCase() : v), category: "text" },
    { name: "lower", fn: (v) => (typeof v === "string" ? v.toLowerCase() : v), category: "text" },
    { name: "length", fn: (v) => (Array.isArray(v) ? v.length : String(v).length), category: "text" },
    { name: "list_sum", fn: (v) => (Array.isArray(v) ? v.reduce((a, b) => a + (typeof b === "number" ? b : 0), 0) : v), category: "list" },
    { name: "split_sum", fn: (v) => {
      if (!Array.isArray(v)) return v;
      const mid = Math.floor(v.length / 2);
      const left = v.slice(0, mid).reduce((a, b) => a + (typeof b === "number" ? b : 0), 0);
      const right = v.slice(mid).reduce((a, b) => a + (typeof b === "number" ? b : 0), 0);
      return [left, right];
    }, category: "list" },
  ];
  const params = [];
  for (let i = 0; i < size; i++) {
    const op = ops[i % ops.length];
    const constant = consts[i % consts.length];
    const fn = (value, gene) => op.fn(value, gene, constant);
    params.push({ id: i + 1, name: op.name, fn, category: op.category });
  }
  return params;
}

function filterParams(params, mode) {
  if (mode === "all") return params.map((p) => p.id);
  return params.filter((p) => p.category === mode || p.category === "core").map((p) => p.id);
}

function randomGene(allowed, randomness) {
  return {
    paramId: allowed[Math.floor(Math.random() * allowed.length)],
    strength: Math.random(),
  };
}

function applyGene(value, gene, params) {
  const param = params[gene.paramId - 1];
  try {
    return param.fn(value, gene);
  } catch {
    return null;
  }
}

function executeGenome(key, genome, params) {
  let value = key;
  for (const gene of genome) {
    value = applyGene(value, gene, params);
    if (value === null || value === undefined) return { ok: false, value: null };
  }
  return { ok: true, value };
}

function evaluateAgent(agent, samples, params, tolerance) {
  let total = 0;
  let hits = 0;
  for (const sample of samples) {
    const result = executeGenome(sample.key, agent.genome, params);
    if (!result.ok) {
      total += 1e9;
      continue;
    }
    const score = scoreValue(result.value, sample.value);
    total += score;
    if (score <= tolerance) hits += 1;
  }
  agent.score = total / samples.length;
  agent.accuracy = hits / samples.length;
}

function evolveGeneration(samples, tolerance) {
  const params = engineState.params;
  for (const agent of engineState.population) {
    evaluateAgent(agent, samples, params, tolerance);
  }
  engineState.population.sort((a, b) => a.score - b.score);
  const survivors = engineState.population.slice(0, Math.ceil(engineState.population.length / 2));
  const top10 = engineState.population.slice(0, Math.min(10, engineState.population.length));
  const genePool = top10.flatMap((agent) => agent.genome);

  const nextGen = survivors.map((agent) => ({
    genome: agent.genome.map((g) => ({ ...g })),
    score: agent.score,
    accuracy: agent.accuracy,
  }));

  while (nextGen.length < engineState.population.length) {
    const parent = survivors[Math.floor(Math.random() * survivors.length)];
    const newGenome = parent.genome.map((gene) => {
      let g = { ...gene };
      if (genePool.length && Math.random() < 0.5) {
        g = { ...genePool[Math.floor(Math.random() * genePool.length)] };
      }
      if (Math.random() < engineState.mutationRate) {
        if (Math.random() < 0.5) {
          g.paramId = engineState.allowed[Math.floor(Math.random() * engineState.allowed.length)];
        }
        g.strength = Math.max(0, Math.min(1, g.strength + (Math.random() - 0.5) * engineState.mutationStrength));
      }
      return g;
    });
    nextGen.push({ genome: newGenome, score: 0, accuracy: 0 });
  }

  engineState.population = nextGen;
  const best = engineState.population[0];
  return { best, params };
}

function trainLoop(samples) {
  const generations = Number(ui.generationCount.value);
  const config = {
    librarySize: Number(ui.librarySize.value),
    population: Number(ui.populationSize.value),
    mode: ui.modeSelect.value,
    initialRandomness: Number(ui.initialRandomness.value),
  };

  let gen = 0;
  training = true;
  history = [];
  const params = buildParamLibrary(config.librarySize);
  const allowed = filterParams(params, config.mode);
  engineState = {
    params,
    allowed,
    population: Array.from({ length: config.population }, () => ({
      genome: Array.from({ length: 8 }, () => randomGene(allowed, config.initialRandomness)),
      score: 0,
      accuracy: 0,
    })),
    mutationRate: 0.2,
    mutationStrength: 0.35,
  };
  const tolerance = 0;
  function step() {
    if (!training || gen >= generations) {
      ui.trainStatus.textContent = training ? "done" : "stopped";
      ui.statusMessage.textContent = training ? "Training complete." : "Stopped.";
      return;
    }
    const { best, params } = evolveGeneration(samples, tolerance);
    bestGenome = { genome: best.genome, params };
    history.push(best.accuracy);
    ui.bestScore.textContent = best.accuracy.toFixed(3);
    ui.currentGen.textContent = String(gen + 1);
    ui.trainStatus.textContent = "running";
    renderAlgorithm(best.genome);
    drawChart();
    gen += 1;
    requestAnimationFrame(step);
  }
  step();
}

function askQuestion() {
  if (!bestGenome) {
    ui.askOutput.textContent = "Train first.";
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
  const result = executeGenome(key, bestGenome.genome, bestGenome.params);
  ui.askOutput.textContent = result.ok ? JSON.stringify(result.value) : "Error";
}

function updateDatasetStatus(samples) {
  ui.datasetStatus.textContent = `${samples.length} samples`;
}

function loadExample() {
  const example = examples[ui.exampleSelect.value];
  ui.datasetInput.value = JSON.stringify(example.data, null, 2);
  updateDatasetStatus(parseDataset(ui.datasetInput.value));
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
  genome.forEach((gene, idx) => {
    const row = document.createElement("div");
    row.className = "algo-step";
    row.innerHTML = `
      <strong>${String(idx + 1).padStart(2, "0")}</strong>
      <div>Param ${gene.paramId}</div>
      <span>strength ${gene.strength.toFixed(2)}</span>
    `;
    ui.algorithmMap.appendChild(row);
  });
}

ui.btnLoadExample.addEventListener("click", loadExample);
ui.datasetInput.addEventListener("input", () => {
  try {
    const samples = parseDataset(ui.datasetInput.value);
    updateDatasetStatus(samples);
    ui.statusMessage.textContent = "Dataset loaded.";
  } catch {
    ui.datasetStatus.textContent = "0 samples";
    ui.statusMessage.textContent = "Invalid JSON dataset.";
  }
});
ui.btnTrain.addEventListener("click", () => {
  try {
    const samples = parseDataset(ui.datasetInput.value);
    updateDatasetStatus(samples);
    ui.statusMessage.textContent = "Training...";
    trainLoop(samples);
  } catch (err) {
    ui.statusMessage.textContent = "Invalid JSON dataset.";
  }
});
ui.btnStop.addEventListener("click", () => {
  training = false;
  ui.trainStatus.textContent = "stopped";
});
ui.btnAsk.addEventListener("click", askQuestion);
ui.librarySize.addEventListener("input", () => (ui.libraryValue.textContent = ui.librarySize.value));
ui.themeSelect.addEventListener("change", () => {
  ui.appRoot.className = `page ${ui.themeSelect.value}`;
});

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

loadExample();
resizeChart();
window.addEventListener("resize", resizeChart);
