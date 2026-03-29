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
};

let training = false;
let bestGenome = null;
let bestScore = Infinity;
let history = [];
let chartCtx = ui.scoreChart.getContext("2d");

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
  const ops = [
    { name: "identity", fn: (v) => v, category: "core" },
    { name: "to_float", fn: (v) => (typeof v === "number" ? v : parseFloat(v)), category: "math" },
    { name: "add", fn: (v, g) => (typeof v === "number" ? v + g.constant : v), category: "math" },
    { name: "mul", fn: (v, g) => (typeof v === "number" ? v * g.constant : v), category: "math" },
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
    params.push({ id: i + 1, name: op.name, fn: op.fn, category: op.category });
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
    randomness: randomness,
    intensity: Math.random(),
    constant: (Math.random() - 0.5) * 10,
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

function evolve(samples, config) {
  const params = buildParamLibrary(config.librarySize);
  const allowed = filterParams(params, config.mode);
  const population = Array.from({ length: config.population }, () => ({
    genome: Array.from({ length: 6 }, () => randomGene(allowed, config.initialRandomness)),
  }));

  let best = population[0];
  let bestScoreLocal = Infinity;
  for (const agent of population) {
    let total = 0;
    let failed = false;
    for (const sample of samples) {
      const result = executeGenome(sample.key, agent.genome, params);
      if (!result.ok) {
        failed = true;
        break;
      }
      total += scoreValue(result.value, sample.value);
    }
    const score = failed ? Infinity : total / samples.length;
    agent.score = score;
    if (score < bestScoreLocal) {
      bestScoreLocal = score;
      best = agent;
    }
  }
  return { best, bestScore: bestScoreLocal, params };
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
  function step() {
    if (!training || gen >= generations) {
      ui.trainStatus.textContent = training ? "done" : "stopped";
      ui.statusMessage.textContent = training ? "Training complete." : "Stopped.";
      return;
    }
    const { best, bestScore: score, params } = evolve(samples, config);
    bestGenome = { genome: best.genome, params };
    bestScore = score;
    history.push(score);
    ui.bestScore.textContent = score.toFixed(4);
    ui.currentGen.textContent = String(gen + 1);
    ui.trainStatus.textContent = "running";
    ui.algorithmMap.textContent = best.genome
      .map((g, i) => `${i + 1}. Param_${g.paramId} randomness=${g.randomness.toFixed(2)} intensity=${g.intensity.toFixed(2)}`)
      .join("\n");
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

loadExample();
resizeChart();
window.addEventListener("resize", resizeChart);
