const taxonomyUrl = new URL("./data/taxonomy.json", import.meta.url).toString();
const lexiconUrl = new URL("./data/lexicon.json", import.meta.url).toString();

const state = {
  taxonomy: null,
  lexicon: null,
  vocab: [],
  vocabIndex: {},
  matrix: [],
  entryVectors: [],
  embedDim: 32,
  lastQuery: "",
  lastBest: "",
  theme: "dark",
};

const PARAM_LABELS = {
  p1: "size",
  p2: "aggression",
  p3: "intelligence",
  p4: "social_status",
  p5: "domestication",
  p6: "agency",
  p7: "toolness",
  p8: "artificialness",
  p9: "danger",
  p10: "empathy",
  p11: "arousal",
  p12: "edible",
  p13: "sweetness",
  p14: "diet",
};

const STOPWORDS = new Set([
  "the",
  "a",
  "an",
  "and",
  "or",
  "but",
  "if",
  "then",
  "with",
  "without",
  "in",
  "on",
  "at",
  "to",
  "of",
  "for",
  "from",
  "by",
  "about",
  "as",
  "into",
  "over",
  "after",
  "before",
  "under",
  "above",
  "is",
  "are",
  "was",
  "were",
  "be",
  "been",
  "being",
  "do",
  "does",
  "did",
  "doing",
  "this",
  "that",
  "these",
  "those",
  "it",
  "its",
  "their",
  "them",
  "you",
  "your",
  "i",
  "we",
  "they",
  "he",
  "she",
  "explain",
  "simple",
  "terms",
  "what",
  "why",
  "how",
  "who",
]);

function mulberry32(seed) {
  let t = seed >>> 0;
  return function () {
    t += 0x6d2b79f5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

async function loadData() {
  const [taxonomy, lexicon] = await Promise.all([
    fetch(taxonomyUrl).then((r) => r.json()),
    fetch(lexiconUrl).then((r) => r.json()),
  ]);
  state.taxonomy = taxonomy;
  state.lexicon = lexicon;
  buildVocab();
  buildMatrix();
  buildEntryVectors();
}

function tokenize(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter(Boolean);
}

function guessPrime(word) {
  const w = word.toLowerCase();
  if (["dog", "cat", "wolf", "bird", "fish"].some((k) => w.includes(k))) return "Animal";
  if (["apple", "banana", "bread", "steak", "fruit", "food"].some((k) => w.includes(k))) return "Food";
  if (["feel", "happy", "sad", "fear"].some((k) => w.includes(k))) return "Feeling";
  if (["run", "fight", "hug", "move"].some((k) => w.includes(k))) return "Action";
  return "Object";
}

function pathGuess(text, prime) {
  const low = text.toLowerCase();
  if (prime === "Animal") {
    const mammal = ["mammal", "dog", "cat", "cow", "wolf"].some((k) => low.includes(k)) ? "Mammal" : "Non-Mammal";
    const domestic = ["domestic", "pet", "tame"].some((k) => low.includes(k)) ? "Domestic" : "Wild";
    const carn = ["carnivore", "predator", "meat"].some((k) => low.includes(k)) ? "Carnivore" : "Herbivore";
    return [mammal, domestic, carn];
  }
  if (prime === "Object") {
    const tool = ["tool", "device", "instrument"].some((k) => low.includes(k)) ? "Tool" : "Non-Tool";
    const mech = ["mechanical", "engine", "machine"].some((k) => low.includes(k)) ? "Mechanical" : "Natural";
    return [tool, mech];
  }
  if (prime === "Action") {
    const violence = ["attack", "violence", "fight", "harm"].some((k) => low.includes(k)) ? "Violence" : "Cooperation";
    return [violence];
  }
  if (prime === "Feeling") {
    const positive = ["happy", "joy", "pleasure", "positive"].some((k) => low.includes(k)) ? "Positive" : "Negative";
    const calm = ["calm", "peace", "relax"].some((k) => low.includes(k)) ? "Calm" : "Arousal";
    return [positive, calm];
  }
  if (prime === "Food") {
    const fruit = ["fruit", "apple", "banana", "berry"].some((k) => low.includes(k)) ? "Fruit" : "Non-Fruit";
    const fresh = ["fresh", "raw"].some((k) => low.includes(k)) ? "Fresh" : "Cooked";
    return [fruit, fresh];
  }
  return [];
}

function traverse(tree, path) {
  let bitstring = "";
  const params = {};
  let node = tree;
  for (const step of path) {
    const name = node.name || "";
    const yesName = node.yes?.name || "";
    const noName = node.no?.name || "";
    const stepLow = step.toLowerCase();
    let isYes = true;
    if (stepLow === name.toLowerCase()) isYes = true;
    else if (yesName && stepLow === yesName.toLowerCase()) isYes = true;
    else if (noName && stepLow === noName.toLowerCase()) isYes = false;
    const bit = node[isYes ? "bit_on_yes" : "bit_on_no"] || "0";
    bitstring += bit;
    const updates = node[isYes ? "params_on_yes" : "params_on_no"] || {};
    for (const [k, v] of Object.entries(updates)) {
      params[k] = Number(v);
    }
    node = node[isYes ? "yes" : "no"];
    if (!node) break;
  }
  return { bitstring, params };
}

function encode(word) {
  const key = word.trim().toLowerCase();
  const entry = state.lexicon[key];
  let prime = entry?.prime || guessPrime(key);
  let path = entry?.path || pathGuess(key, prime);
  const tree = state.taxonomy.primes[prime]?.tree;
  if (!tree) return null;
  const { bitstring, params } = traverse(tree, path);
  const overrides = entry?.overrides || {};
  for (const [k, v] of Object.entries(overrides)) {
    params[k] = Number(v);
  }
  return { prime, bitstring, params, path };
}

function buildVocab() {
  const vocabSet = new Set();
  const addTokens = (text) => {
    tokenize(text).forEach((tok) => {
      if (!STOPWORDS.has(tok)) vocabSet.add(tok);
    });
  };
  Object.keys(state.lexicon || {}).forEach((word) => {
    const entry = state.lexicon[word];
    addTokens(word);
    if (entry?.prime) addTokens(entry.prime);
    if (entry?.path) addTokens(entry.path.join(" "));
  });
  const taxonomyText = JSON.stringify(state.taxonomy || {});
  addTokens(taxonomyText);
  state.vocab = Array.from(vocabSet).slice(0, 1200);
  state.vocabIndex = Object.fromEntries(state.vocab.map((w, i) => [w, i]));
}

function buildMatrix() {
  const embedDim = state.embedDim;
  const vocabSize = state.vocab.length;
  const stored = loadMatrix(embedDim);
  if (stored && stored.length === embedDim && stored[0]?.length === vocabSize) {
    state.matrix = stored;
    return;
  }
  const rng = mulberry32(1337);
  const matrix = [];
  for (let i = 0; i < embedDim; i++) {
    const row = new Array(vocabSize).fill(0);
    for (let j = 0; j < vocabSize; j++) {
      row[j] = (rng() - 0.5) * 0.2;
    }
    matrix.push(row);
  }
  state.matrix = matrix;
  saveMatrix();
}

function vectorize(text) {
  const vec = new Array(state.vocab.length).fill(0);
  for (const tok of tokenize(text)) {
    if (STOPWORDS.has(tok)) continue;
    const idx = state.vocabIndex[tok];
    if (idx !== undefined) vec[idx] += 1;
  }
  return vec;
}

function matmul(matrix, vec) {
  const out = new Array(matrix.length).fill(0);
  for (let i = 0; i < matrix.length; i++) {
    let sum = 0;
    const row = matrix[i];
    for (let j = 0; j < vec.length; j++) {
      sum += row[j] * vec[j];
    }
    out[i] = Math.tanh(sum);
  }
  return out;
}

function normalize(vec) {
  const norm = Math.sqrt(vec.reduce((acc, v) => acc + v * v, 0)) || 1;
  return vec.map((v) => v / norm);
}

function embedText(text) {
  const bow = vectorize(text);
  return normalize(matmul(state.matrix, bow));
}

function buildEntryVectors() {
  state.entryVectors = Object.keys(state.lexicon || {}).map((word) => {
    const entry = state.lexicon[word];
    const text = `${word} ${entry?.prime || ""} ${(entry?.path || []).join(" ")}`;
    return {
      word,
      text,
      vector: embedText(text),
    };
  });
}

function cosine(a, b) {
  let sum = 0;
  for (let i = 0; i < a.length; i++) sum += a[i] * b[i];
  return sum;
}

function searchEntries(query, k = 5) {
  const qvec = embedText(query);
  const scored = state.entryVectors.map((item) => ({
    ...item,
    score: cosine(qvec, item.vector),
  }));
  scored.sort((a, b) => b.score - a.score);
  return { qvec, results: scored.slice(0, k) };
}

function aggregateParams(results) {
  const out = {};
  if (!results.length) return out;
  for (const res of results) {
    for (const [k, v] of Object.entries(res.params || {})) {
      out[k] = (out[k] || 0) + Number(v);
    }
  }
  for (const k of Object.keys(out)) {
    out[k] /= results.length;
  }
  return out;
}

function traitList(params) {
  const traits = [];
  if ((params.p12 || 0) > 0.7) traits.push("edible");
  if ((params.p13 || 0) > 0.7) traits.push("sweet");
  if ((params.p14 || 0) > 0.7) traits.push("carnivorous");
  if ((params.p5 || 0) > 0.7) traits.push("domesticated");
  if ((params.p2 || 0) > 0.7) traits.push("aggressive");
  if ((params.p9 || 0) > 0.7) traits.push("dangerous");
  if ((params.p7 || 0) > 0.7) traits.push("tool-like");
  if ((params.p8 || 0) > 0.7) traits.push("artificial");
  if ((params.p8 || 0) < 0.3) traits.push("natural");
  if ((params.p10 || 0) > 0.7) traits.push("friendly");
  if ((params.p1 || 0) > 0.7) traits.push("large");
  if ((params.p1 || 0) < 0.3) traits.push("small");
  if ((params.p3 || 0) > 0.7) traits.push("intelligent");
  if ((params.p6 || 0) > 0.7) traits.push("agentic");
  return traits;
}

async function wikiSummary(query) {
  const title = encodeURIComponent(query.trim().replace(/\s+/g, "_"));
  if (!title) return "";
  const url = `https://en.wikipedia.org/api/rest_v1/page/summary/${title}`;
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 2500);
    const res = await fetch(url, { signal: ctrl.signal });
    clearTimeout(t);
    if (!res.ok) return "";
    const data = await res.json();
    return data.extract || "";
  } catch {
    return "";
  }
}

function formatAnswer(question, matches, params, prime) {
  const traits = traitList(params);
  const sentences = [];
  sentences.push(`Answer to: ${question}`);
  sentences.push(`Prime: ${prime}`);
  sentences.push(traits.length ? `Traits: ${traits.slice(0, 6).join(", ")}` : "Traits: mixed");
  if (matches.length) {
    const top = matches[0];
    sentences.push(`Best match: ${top.word} (${top.score.toFixed(3)})`);
  }
  return sentences.join("\n");
}

function saveMatrix() {
  const key = `flux_lite_matrix_v1_${state.embedDim}`;
  const payload = {
    vocabSig: state.vocab.slice(0, 200).join("|"),
    matrix: state.matrix,
  };
  localStorage.setItem(key, JSON.stringify(payload));
}

function loadMatrix(dim) {
  const key = `flux_lite_matrix_v1_${dim}`;
  const raw = localStorage.getItem(key);
  if (!raw) return null;
  try {
    const payload = JSON.parse(raw);
    const sig = state.vocab.slice(0, 200).join("|");
    if (payload.vocabSig !== sig) return null;
    return payload.matrix;
  } catch {
    return null;
  }
}

function resetMatrix() {
  const key = `flux_lite_matrix_v1_${state.embedDim}`;
  localStorage.removeItem(key);
  buildMatrix();
  buildEntryVectors();
}

function learnFrom(query, targetText, lr) {
  const bow = vectorize(query);
  const pred = embedText(query);
  const target = embedText(targetText);
  const error = target.map((v, i) => v - pred[i]);
  for (let i = 0; i < state.matrix.length; i++) {
    const row = state.matrix[i];
    const e = error[i];
    if (e === 0) continue;
    for (let j = 0; j < row.length; j++) {
      if (bow[j] !== 0) row[j] += lr * e * bow[j];
    }
  }
  buildEntryVectors();
  saveMatrix();
}

const EVAL_PROMPTS = [
  { prompt: "Explain dogs in simple terms", expected: ["animal", "dog", "pet"] },
  { prompt: "What is a wolf?", expected: ["animal", "wolf", "wild"] },
  { prompt: "Define apple", expected: ["food", "fruit", "sweet"] },
  { prompt: "Describe fear", expected: ["feeling", "negative"] },
  { prompt: "Explain running", expected: ["action", "move"] },
];

function scoreAnswer(answer, expected) {
  const low = answer.toLowerCase();
  const hits = expected.filter((k) => low.includes(k)).length;
  return hits / expected.length;
}

function runEvaluation() {
  const list = document.getElementById("eval-list");
  const scoreEl = document.getElementById("eval-score");
  const statusEl = document.getElementById("eval-status");
  if (list) list.innerHTML = "";
  let total = 0;
  EVAL_PROMPTS.forEach((item) => {
    const tokens = tokenize(item.prompt).filter((t) => !STOPWORDS.has(t));
    const encoded = tokens.map((t) => encode(t)).filter(Boolean);
    const params = aggregateParams(encoded);
    const prime = encoded[0]?.prime || guessPrime(item.prompt);
    const search = searchEntries(item.prompt, 3);
    const summary = formatAnswer(item.prompt, search.results, params, prime);
    const score = scoreAnswer(summary, item.expected);
    total += score;
    if (list) {
      const li = document.createElement("li");
      li.textContent = `${item.prompt} -> ${score.toFixed(2)}`;
      list.appendChild(li);
    }
  });
  const avg = total / EVAL_PROMPTS.length;
  if (scoreEl) scoreEl.textContent = avg.toFixed(2);
  if (statusEl) statusEl.textContent = `Completed in ${EVAL_PROMPTS.length} prompts.`;
}

function renderMatches(matches, target) {
  if (!target) return;
  target.innerHTML = "";
  matches.forEach((m) => {
    const li = document.createElement("li");
    li.textContent = `${m.word} (${m.score.toFixed(3)})`;
    target.appendChild(li);
  });
}

function renderStats(vec, target) {
  if (!target) return;
  const maxVal = Math.max(...vec);
  const minVal = Math.min(...vec);
  const mean = vec.reduce((acc, v) => acc + v, 0) / vec.length;
  target.textContent = `dim=32\nmean=${mean.toFixed(3)}\nmin=${minVal.toFixed(3)}\nmax=${maxVal.toFixed(3)}`;
}

function runQuery() {
  const input = document.getElementById("qa-input");
  const output = document.getElementById("qa-output");
  const matchesEl = document.getElementById("qa-matches");
  const statsEl = document.getElementById("qa-stats");
  const live = document.getElementById("qa-live");
  const autoLearn = document.getElementById("auto-learn");
  const learnRateEl = document.getElementById("learn-rate");
  const learnStatus = document.getElementById("learn-status");
  const question = input.value.trim();
  if (!question) return;

  const tokens = tokenize(question).filter((t) => !STOPWORDS.has(t));
  const encoded = tokens.map((t) => encode(t)).filter(Boolean);
  const params = aggregateParams(encoded);
  const prime = encoded[0]?.prime || guessPrime(question);
  const search = searchEntries(question, 5);
  const summary = formatAnswer(question, search.results, params, prime);
  state.lastQuery = question;
  state.lastBest = search.results[0]?.word || "";

  renderMatches(search.results, matchesEl);
  renderStats(search.qvec, statsEl);

  if (autoLearn?.checked && state.lastBest) {
    const lr = Number(learnRateEl?.value || 0.03);
    learnFrom(question, state.lastBest, lr);
    if (learnStatus) learnStatus.textContent = `Auto-learned from ${state.lastBest}.`;
  }

  if (live.checked) {
    output.value = summary + "\n\nFetching Wikipedia summary...";
    wikiSummary(question).then((extra) => {
      output.value = extra ? `${summary}\n\nWeb summary:\n${extra}` : summary;
    });
  } else {
    output.value = summary;
  }
}

function terminalWrite(message) {
  const log = document.getElementById("term-log");
  if (!log) return;
  log.textContent += `${message}\n`;
  log.scrollTop = log.scrollHeight;
}

function handleTerminalCommand(line) {
  const trimmed = line.trim();
  if (!trimmed) return;
  const [cmd, ...rest] = trimmed.split(" ");
  const arg = rest.join(" ").trim();
  if (cmd === "help") {
    terminalWrite("Commands: help, ask <question>, search <query>, encode <word>, clear");
    return;
  }
  if (cmd === "clear") {
    const log = document.getElementById("term-log");
    if (log) log.textContent = "";
    return;
  }
  if (cmd === "encode") {
    const res = encode(arg);
    terminalWrite(res ? JSON.stringify(res, null, 2) : "No match.");
    return;
  }
  if (cmd === "search") {
    const search = searchEntries(arg || trimmed, 5);
    search.results.forEach((r) => terminalWrite(`${r.word} (${r.score.toFixed(3)})`));
    return;
  }
  if (cmd === "ask") {
    const q = arg || trimmed;
    const tokens = tokenize(q).filter((t) => !STOPWORDS.has(t));
    const encoded = tokens.map((t) => encode(t)).filter(Boolean);
    const params = aggregateParams(encoded);
    const prime = encoded[0]?.prime || guessPrime(q);
    const search = searchEntries(q, 5);
    terminalWrite(formatAnswer(q, search.results, params, prime));
    return;
  }
  terminalWrite("Unknown command. Type help.");
}

document.getElementById("qa-btn").addEventListener("click", runQuery);
document.getElementById("qa-input").addEventListener("keydown", (event) => {
  if (event.key === "Enter") runQuery();
});

document.getElementById("term-input").addEventListener("keydown", (event) => {
  if (event.key !== "Enter") return;
  const line = event.target.value;
  event.target.value = "";
  terminalWrite(`flux> ${line}`);
  handleTerminalCommand(line);
});

loadData().then(() => {
  const sizeSelect = document.getElementById("model-size");
  const learnBtn = document.getElementById("learn-btn");
  const resetBtn = document.getElementById("reset-btn");
  const learnStatus = document.getElementById("learn-status");
  const evalBtn = document.getElementById("eval-btn");
  const themeToggle = document.getElementById("theme-toggle");

  const savedTheme = localStorage.getItem("flux_lite_theme");
  if (savedTheme === "light") {
    document.body.classList.add("light");
    state.theme = "light";
    if (themeToggle) themeToggle.checked = true;
  }

  if (sizeSelect) {
    sizeSelect.value = String(state.embedDim);
    sizeSelect.addEventListener("change", () => {
      state.embedDim = Number(sizeSelect.value || 32);
      buildMatrix();
      buildEntryVectors();
      if (learnStatus) learnStatus.textContent = `Model resized to ${state.embedDim}.`;
    });
  }
  if (learnBtn) {
    learnBtn.addEventListener("click", () => {
      if (!state.lastQuery || !state.lastBest) {
        if (learnStatus) learnStatus.textContent = "Ask a question first.";
        return;
      }
      const lr = Number(document.getElementById("learn-rate")?.value || 0.03);
      learnFrom(state.lastQuery, state.lastBest, lr);
      if (learnStatus) learnStatus.textContent = `Learned from ${state.lastBest}.`;
    });
  }
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      resetMatrix();
      if (learnStatus) learnStatus.textContent = "Model reset.";
    });
  }
  if (evalBtn) {
    evalBtn.addEventListener("click", () => {
      const status = document.getElementById("eval-status");
      if (status) status.textContent = "Running...";
      setTimeout(runEvaluation, 50);
    });
  }
  if (themeToggle) {
    themeToggle.addEventListener("change", () => {
      if (themeToggle.checked) {
        document.body.classList.add("light");
        state.theme = "light";
        localStorage.setItem("flux_lite_theme", "light");
      } else {
        document.body.classList.remove("light");
        state.theme = "dark";
        localStorage.setItem("flux_lite_theme", "dark");
      }
    });
  }
  terminalWrite("Flux Lite terminal ready. Type help.");
});
