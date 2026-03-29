const state = {
  dataset: [],
  running: false,
  paused: false,
  generation: 0,
  bestFitness: 0,
  avgFitness: 0,
  maxGenerations: 300,
  targetAccuracy: 0.95,
  librarySize: 300,
  genomeLength: 8,
  timer: null,
  circumference: 0,
};

const el = {
  appRoot: document.getElementById("appRoot"),
  setupStage: document.getElementById("setupStage"),
  evolutionStage: document.getElementById("evolutionStage"),
  resultStage: document.getElementById("resultStage"),
  fileInput: document.getElementById("fileInput"),
  datasetInput: document.getElementById("datasetInput"),
  datasetStatus: document.getElementById("datasetStatus"),
  statusMessage: document.getElementById("statusMessage"),
  librarySize: document.getElementById("librarySize"),
  libraryValue: document.getElementById("libraryValue"),
  populationSize: document.getElementById("populationSize"),
  genomeLength: document.getElementById("genomeLength"),
  generationCount: document.getElementById("generationCount"),
  accuracyTarget: document.getElementById("accuracyTarget"),
  btnStart: document.getElementById("btnStart"),
  btnSample: document.getElementById("btnSample"),
  btnPause: document.getElementById("btnPause"),
  btnStop: document.getElementById("btnStop"),
  btnRestart: document.getElementById("btnRestart"),
  progressSvg: document.getElementById("progressSvg"),
  progressValue: document.getElementById("progressValue"),
  genValue: document.getElementById("genValue"),
  topFormulas: document.getElementById("topFormulas"),
  bestFitness: document.getElementById("bestFitness"),
  avgFitness: document.getElementById("avgFitness"),
  evolutionLog: document.getElementById("evolutionLog"),
  recipeChain: document.getElementById("recipeChain"),
  resultMeta: document.getElementById("resultMeta"),
};

const ringProgress = document.querySelector(".ring-progress");

function setMode(mode) {
  el.appRoot.dataset.mode = mode;
  el.setupStage.classList.toggle("hidden", mode !== "setup");
  el.evolutionStage.classList.toggle("hidden", mode !== "evolution");
  el.resultStage.classList.toggle("hidden", mode !== "result");
}

function updateDatasetStatus() {
  const count = state.dataset.length;
  el.datasetStatus.textContent = `${count} samples`;
}

function setStatus(text) {
  el.statusMessage.textContent = text;
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
  updateDatasetStatus();
  return state.dataset.length > 0;
}

function handleFileUpload(file) {
  const reader = new FileReader();
  reader.onload = () => {
    el.datasetInput.value = reader.result;
    loadDatasetFromText();
    setStatus("Training data loaded.");
  };
  reader.readAsText(file);
}

function generateFormula() {
  const steps = [];
  const ops = [
    "add",
    "sub",
    "mul",
    "div",
    "first_letter",
    "last_letter",
    "lower",
    "upper",
    "round",
    "abs",
  ];
  for (let i = 0; i < state.genomeLength; i += 1) {
    const paramId = String(Math.floor(Math.random() * state.librarySize)).padStart(3, "0");
    const op = ops[Math.floor(Math.random() * ops.length)];
    steps.push(`Param_${paramId}:${op}`);
  }
  return steps;
}

function updateTopFormulas() {
  el.topFormulas.innerHTML = "";
  for (let i = 0; i < 3; i += 1) {
    const card = document.createElement("div");
    card.className = "formula-card";
    card.textContent = generateFormula().join(" -> ");
    el.topFormulas.appendChild(card);
  }
}

function updateProgress(percent) {
  const pct = Math.min(1, Math.max(0, percent));
  const offset = state.circumference * (1 - pct);
  ringProgress.style.strokeDashoffset = offset.toFixed(2);
  el.progressValue.textContent = `${Math.round(pct * 100)}%`;
}

function resetEvolutionState() {
  state.generation = 0;
  state.bestFitness = 0;
  state.avgFitness = 0;
  state.running = true;
  state.paused = false;
  el.genValue.textContent = "0";
  el.bestFitness.textContent = "0.000";
  el.avgFitness.textContent = "0.000";
  updateProgress(0);
  updateTopFormulas();
  el.evolutionLog.textContent = "Initializing population...";
}

function startEvolution() {
  if (!loadDatasetFromText()) {
    setStatus("Add training data to start evolution.");
    return;
  }
  state.librarySize = Number(el.librarySize.value);
  state.genomeLength = Number(el.genomeLength.value);
  state.maxGenerations = Number(el.generationCount.value);
  state.targetAccuracy = Number(el.accuracyTarget.value);
  setStatus("Running evolution.");
  setMode("evolution");
  resetEvolutionState();

  if (state.timer) {
    clearInterval(state.timer);
  }
  state.timer = setInterval(stepEvolution, 240);
}

function stopEvolution() {
  state.running = false;
  state.paused = false;
  if (state.timer) {
    clearInterval(state.timer);
    state.timer = null;
  }
  setMode("setup");
  setStatus("Ready.");
}

function pauseEvolution() {
  if (!state.running) {
    return;
  }
  state.paused = !state.paused;
  el.btnPause.textContent = state.paused ? "Resume" : "Pause";
  el.evolutionLog.textContent = state.paused ? "Paused." : "Resumed.";
}

function stepEvolution() {
  if (!state.running || state.paused) {
    return;
  }
  state.generation += 1;
  const improvement = (1 - state.bestFitness) * (0.08 + Math.random() * 0.12);
  state.bestFitness = Math.min(1, state.bestFitness + improvement);
  state.avgFitness = Math.min(1, state.bestFitness * (0.65 + Math.random() * 0.1));

  el.genValue.textContent = String(state.generation);
  el.bestFitness.textContent = state.bestFitness.toFixed(3);
  el.avgFitness.textContent = state.avgFitness.toFixed(3);
  updateProgress(state.bestFitness);

  if (state.generation % 2 === 0) {
    updateTopFormulas();
  }

  el.evolutionLog.textContent = `Generation ${state.generation} | best fitness ${state.bestFitness.toFixed(
    3
  )}`;

  if (state.bestFitness >= state.targetAccuracy || state.generation >= state.maxGenerations) {
    finishEvolution();
  }
}

function finishEvolution() {
  state.running = false;
  if (state.timer) {
    clearInterval(state.timer);
    state.timer = null;
  }
  const steps = generateFormula();
  el.recipeChain.innerHTML = "";
  steps.forEach((step) => {
    const chip = document.createElement("div");
    chip.className = "recipe-step";
    chip.textContent = step;
    el.recipeChain.appendChild(chip);
  });
  el.resultMeta.textContent = `Generations: ${state.generation} | Best fitness: ${state.bestFitness.toFixed(
    3
  )} | Target: ${state.targetAccuracy.toFixed(2)}`;
  setMode("result");
  setStatus("Evolution complete.");
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
        {
          Example: { Key: "mars", Value: "red" },
          Entry2: { Key: "jupiter", Value: "gas" },
        },
        null,
        2
      );
      loadDatasetFromText();
      setStatus("Sample data loaded.");
    });
}

function initRing() {
  const radius = 92;
  state.circumference = 2 * Math.PI * radius;
  ringProgress.style.strokeDasharray = state.circumference.toFixed(2);
  ringProgress.style.strokeDashoffset = state.circumference.toFixed(2);
}

el.fileInput.addEventListener("change", (event) => {
  const file = event.target.files && event.target.files[0];
  if (file) {
    handleFileUpload(file);
  }
});

el.datasetInput.addEventListener("input", () => {
  loadDatasetFromText();
  setStatus("Dataset updated.");
});

el.librarySize.addEventListener("input", () => {
  el.libraryValue.textContent = el.librarySize.value;
});

el.btnStart.addEventListener("click", startEvolution);
el.btnStop.addEventListener("click", stopEvolution);
el.btnPause.addEventListener("click", pauseEvolution);
el.btnRestart.addEventListener("click", () => {
  setMode("setup");
  setStatus("Ready.");
});
el.btnSample.addEventListener("click", loadSample);

initRing();
updateDatasetStatus();
