/**
 * Flux Evolver Core v0.0.3
 * Improved Neural Formula Studio
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
  genomeLength: 8,
  maxGenerations: 300,
  targetAccuracy: 0.95,
  appVersion: "0.0.3",
  changeCounter: 0,
};

const uiState = {
  activePanel: 'settings',
  guideIndex: 0
};

const guideSteps = [
  { title: "Protocol 1: Data Link", text: "Ingest a dataset via Data Architect to initialize search space." },
  { title: "Protocol 2: Logic Decompile", text: "Autoformat raw signals and decompile to human-readable strategies." },
  { title: "Protocol 3: Seed Evolution", text: "Configure population density and genome length to begin training." },
  { title: "Protocol 4: Interactive Mutator", text: "Pin or ban specific alleles to influence evolution in real-time." },
  { title: "Protocol 5: Deploy SDK", text: "Export optimized neural sequences as Python or JS modules." },
];

// Helper to get elements
const $ = (id) => document.getElementById(id);

/**
 * Log to system console
 */
function log(msg, type = 'default') {
  const consoleOut = $('consoleOutput');
  if (!consoleOut) return;
  const line = document.createElement("div");
  line.className = `log-line ${type}`;
  const now = new Date();
  const time = now.getHours().toString().padStart(2, '0') + ":" + now.getMinutes().toString().padStart(2, '0') + ":" + now.getSeconds().toString().padStart(2, '0');
  line.innerHTML = `<span class="log-time">[${time}]</span> ${msg}`;
  consoleOut.prepend(line);
}

/**
 * Resize canvas for high DPI
 */
function resizeCanvas(canvas) {
  const parent = canvas.parentElement;
  if (!parent) return null;
  const rect = parent.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const width = rect.width;
  const height = rect.height;
  
  if (canvas.width !== Math.floor(width * dpr) || canvas.height !== Math.floor(height * dpr)) {
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
  }
  
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, width, height };
}

/**
 * Main Training Loop
 */
function stepTraining() {
  if (!state.running) return;
  state.generation += 1;
  
  // Simulated fitness improvement (shrinking distance to target)
  const improvement = (1 - state.best) * (0.02 + Math.random() * 0.03);
  state.best = Math.min(1, state.best + improvement);
  state.history.push(state.best);
  
  if ($('genLabel')) $('genLabel').textContent = `GEN ${state.generation}`;
  if ($('bestLabel')) $('bestLabel').textContent = `${(state.best * 100).toFixed(2)}%`;
  
  updateLeaderboard();
  
  if (state.generation % 10 === 0) {
    log(`Epoch ${state.generation}: Alpha stabilizing at ${(state.best * 100).toFixed(2)}%`, "default");
  }

  const stopChecked = $('stopOnTarget') ? $('stopOnTarget').checked : false;
  if (state.generation >= state.maxGenerations || (stopChecked && state.best >= state.targetAccuracy)) {
    stopTraining();
    log("Simulation stabilized. Optimal formula found.", "success");
  }
}

function startTraining() {
  if (state.dataset.length === 0) {
    log("Inversion failed: No telemetry data linked.", "error");
    togglePanel('files');
    return;
  }
  
  state.running = true;
  state.generation = 0;
  state.best = 0;
  state.history = [];
  state.historyDisplay = [];
  
  $('appRoot').classList.add("training-running");
  log("Initializing neural evolution kernel...", "system");
  
  if (state.interval) clearInterval(state.interval);
  state.interval = setInterval(stepTraining, 150);
}

function stopTraining() {
  state.running = false;
  $('appRoot').classList.remove("training-running");
  if (state.interval) clearInterval(state.interval);
  if ($('statusMessage')) $('statusMessage').textContent = "System Standby";
}

/**
 * Charts
 */
function drawFitness() {
  const canvas = $('fitnessChart');
  if (!canvas) return;
  const size = resizeCanvas(canvas);
  if (!size) return;
  const { ctx, width, height } = size;
  
  ctx.clearRect(0, 0, width, height);
  const padding = { left: 40, right: 10, top: 10, bottom: 25 };
  const pW = width - padding.left - padding.right;
  const pH = height - padding.top - padding.bottom;

  // Grid
  ctx.strokeStyle = "rgba(255,255,255,0.05)";
  ctx.lineWidth = 1;
  for(let i=0; i<=4; i++) {
    const y = padding.top + (pH * (1 - i/4));
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
  }

  if (state.historyDisplay.length < 2) return;

  // Line
  ctx.beginPath();
  ctx.lineWidth = 2.5;
  ctx.strokeStyle = "#00d2ff";
  ctx.lineJoin = "round";

  const stepX = pW / (state.historyDisplay.length - 1);
  state.historyDisplay.forEach((v, i) => {
    const x = padding.left + i * stepX;
    const y = padding.top + (1 - v) * pH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Area
  ctx.lineTo(padding.left + pW, padding.top + pH);
  ctx.lineTo(padding.left, padding.top + pH);
  ctx.fillStyle = "rgba(0, 210, 255, 0.05)";
  ctx.fill();
}

function updateLeaderboard() {
  const lb = $('leaderboard');
  if (!lb) return;
  lb.innerHTML = "";
  for(let i=0; i<6; i++) {
    const row = document.createElement('div');
    row.className = "leaderboard-row";
    const fitness = (state.best * 100 - i * 2.1).toFixed(2);
    row.innerHTML = `
      <span class="rank">#${i+1}</span>
      <span class="formula">P${Math.floor(Math.random()*999)}:mul → P${Math.floor(Math.random()*999)}:add</span>
      <span class="score">${Math.max(0, fitness)}%</span>
    `;
    lb.appendChild(row);
  }
}

/**
 * Presets & Data
 */
function loadExample(id) {
  const paths = {
    animals: "data/animals.json",
    taxonomy: "data/taxonomy.json",
    lexicon: "data/lexicon.json",
    market: "data/market_linear.json",
    solar: "data/solar_system.json",
    slingshot: "data/slingshot_data.json"
  };
  
  const path = paths[id];
  if (!path) {
    log(`Preset ID "${id}" not found.`, "error");
    return;
  }

  log(`Linking telemetry stream: ${id}...`, "system");
  
  fetch(path)
    .then(r => {
      if (!r.ok) throw new Error(`HTTP error! status: ${r.status}`);
      return r.json();
    })
    .then(data => {
      if ($('datasetInput')) {
        $('datasetInput').value = JSON.stringify(data, null, 2);
        state.dataset = Array.isArray(data) ? data : Object.values(data);
        
        if ($('datasetStatus')) $('datasetStatus').textContent = `${state.dataset.length} items`;
        if ($('fileName')) $('fileName').textContent = `${id}.json`;
        
        if ($('exampleModal')) $('exampleModal').classList.add('hidden');
        log(`Data stream "${id}" linked and validated.`, "success");
      }
    })
    .catch(e => {
      log(`Stream failed: ${e.message}`, "error");
      console.error("Fetch error:", e);
    });
}

/**
 * UI Controls
 */
function togglePanel(panel) {
  const sp = $('slidePanel');
  if (uiState.activePanel === panel && sp && !sp.classList.contains('collapsed')) {
    sp.classList.add('collapsed');
  } else {
    sp.classList.remove('collapsed');
    uiState.activePanel = panel;
    document.querySelectorAll('.icon-btn').forEach(b => b.classList.toggle('active', b.dataset.panel === panel));
    document.querySelectorAll('.panel-section').forEach(s => s.classList.toggle('active', s.dataset.panelSection === panel));
  }
}

function setMode(mode) {
  document.querySelectorAll('.mode-pill').forEach(p => p.classList.toggle('active', p.dataset.mode === mode));
  $('askPanel').classList.toggle('hidden', mode !== 'ask');
  $('fitnessCard').classList.toggle('hidden', mode === 'ask');
  $('leaderboardCard').classList.toggle('hidden', mode === 'ask');
  log(`Kernel mode set to: ${mode.toUpperCase()}`);
}

function init() {
  // Navigation
  document.querySelectorAll('.icon-btn').forEach(b => {
    b.onclick = () => togglePanel(b.dataset.panel);
  });

  // Controls
  if ($('btnStart')) $('btnStart').onclick = startTraining;
  if ($('btnStop')) $('btnStop').onclick = stopTraining;
  if ($('btnSample')) $('btnSample').onclick = () => $('exampleModal').classList.remove('hidden');
  if ($('btnExampleClose')) $('btnExampleClose').onclick = () => $('exampleModal').classList.add('hidden');
  if ($('btnClearConsole')) $('btnClearConsole').onclick = () => $('consoleOutput').innerHTML = "";

  // Preset Cards
  document.querySelectorAll('.example-card').forEach(c => {
    c.onclick = () => {
      const exId = c.getAttribute('data-example');
      loadExample(exId);
    };
  });

  // Modes
  document.querySelectorAll('.mode-pill').forEach(p => {
    p.onclick = () => setMode(p.dataset.mode);
  });

  // Guide
  if ($('btnGuideNext')) $('btnGuideNext').onclick = () => {
    uiState.guideIndex = (uiState.guideIndex + 1) % guideSteps.length;
    const step = guideSteps[uiState.guideIndex];
    if ($('guideTitle')) $('guideTitle').textContent = step.title;
    if ($('guideText')) $('guideText').textContent = step.text;
    if ($('guideStep')) $('guideStep').textContent = `${uiState.guideIndex + 1} / ${guideSteps.length}`;
  };

  // Animation Frame
  function loop() {
    if (state.history.length > 0) {
      if (state.historyDisplay.length < state.history.length) {
        state.historyDisplay.push(state.history[state.historyDisplay.length]);
      }
      state.historyDisplay = state.historyDisplay.map((v, i) => v + (state.history[i] - v) * 0.1);
    }
    drawFitness();
    requestAnimationFrame(loop);
  }
  loop();

  log("Flux Neural Evolution Kernel Ready.");
}

window.onload = init;
