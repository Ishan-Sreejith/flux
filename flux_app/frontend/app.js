const chat = document.getElementById("chat");
const form = document.getElementById("ask-form");
const input = document.getElementById("question");
const refresh = document.getElementById("refresh");
const askGrade = document.getElementById("ask-grade");
const trainInput = document.getElementById("train-input");
const trainButton = document.getElementById("train-submit");
const trainStatus = document.getElementById("train-status");
const trainDim = document.getElementById("train-dim");
const trainGrade = document.getElementById("train-grade");
const trainSources = document.getElementById("train-sources");
const trainWorkers = document.getElementById("train-workers");
const trainFull = document.getElementById("train-full");
const trainWord2Vec = document.getElementById("train-word2vec");

const sessionKey = "flux_session_id";
const apiOverrideKey = "flux_api_base";
const bodyApiDefault = document.body ? document.body.dataset.apiDefault : "";
const queryApi = new URLSearchParams(window.location.search).get("api");
if (queryApi) {
  localStorage.setItem(apiOverrideKey, queryApi);
}
const apiBase =
  localStorage.getItem(apiOverrideKey) ||
  (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? bodyApiDefault || "http://127.0.0.1:3001"
    : window.location.origin);
let sessionId = localStorage.getItem(sessionKey);
if (!sessionId) {
  sessionId = crypto.randomUUID();
  localStorage.setItem(sessionKey, sessionId);
}

const sliderContainer = document.getElementById("nlp-sliders");
const sliderCount = document.getElementById("nlp-count");

const nlpParams = [
  { key: "context_depth", label: "Context depth", min: 0, max: 100, value: 60 },
  { key: "intent_weight", label: "Intent weight", min: 0, max: 100, value: 60 },
  { key: "entity_weight", label: "Entity weight", min: 0, max: 100, value: 60 },
  { key: "coref_weight", label: "Coref weight", min: 0, max: 100, value: 60 },
  { key: "sentiment_weight", label: "Sentiment weight", min: 0, max: 100, value: 20 },
  { key: "topic_weight", label: "Topic weight", min: 0, max: 100, value: 50 },
  { key: "grammar_weight", label: "Grammar weight", min: 0, max: 100, value: 70 },
  { key: "structure_weight", label: "Structure weight", min: 0, max: 100, value: 70 },
  { key: "brevity", label: "Brevity", min: 0, max: 100, value: 50 },
  { key: "evidence_weight", label: "Evidence weight", min: 0, max: 100, value: 70 },
  { key: "synthesis_weight", label: "Synthesis weight", min: 0, max: 100, value: 80 },
  { key: "freshness_weight", label: "Freshness weight", min: 0, max: 100, value: 60 },
  { key: "contradiction_sensitivity", label: "Contradiction sensitivity", min: 0, max: 100, value: 50 },
  { key: "uncertainty_threshold", label: "Uncertainty threshold", min: 0, max: 100, value: 40 },
  { key: "example_weight", label: "Example weight", min: 0, max: 100, value: 55 },
  { key: "definition_weight", label: "Definition weight", min: 0, max: 100, value: 70 },
  { key: "why_weight", label: "Why weight", min: 0, max: 100, value: 40 },
  { key: "how_weight", label: "How weight", min: 0, max: 100, value: 40 },
  { key: "steps_weight", label: "Steps weight", min: 0, max: 100, value: 30 },
  { key: "analogy_weight", label: "Analogy weight", min: 0, max: 100, value: 25 },
  { key: "caution_weight", label: "Caution weight", min: 0, max: 100, value: 20 },
  { key: "bias_mitigation", label: "Bias mitigation", min: 0, max: 100, value: 40 },
  { key: "noise_filter", label: "Noise filter", min: 0, max: 100, value: 60 },
  { key: "repetition_penalty", label: "Repetition penalty", min: 0, max: 100, value: 50 },
  { key: "hedging_level", label: "Hedging level", min: 0, max: 100, value: 30 },
  { key: "formality", label: "Formality", min: 0, max: 100, value: 50 },
  { key: "readability_level", label: "Readability", min: 6, max: 16, value: 10 },
  { key: "max_sentences", label: "Max sentences", min: 1, max: 6, value: 3 },
  { key: "max_words_per_sentence", label: "Max words/sentence", min: 10, max: 30, value: 24 },
  { key: "keyword_boost", label: "Keyword boost", min: 0, max: 100, value: 50 },
  { key: "entity_boost", label: "Entity boost", min: 0, max: 100, value: 50 },
  { key: "topic_boost", label: "Topic boost", min: 0, max: 100, value: 50 },
  { key: "source_merge", label: "Source merge", min: 0, max: 100, value: 60 },
  { key: "source_diversity", label: "Source diversity", min: 0, max: 100, value: 40 },
  { key: "paraphrase_strength", label: "Paraphrase strength", min: 0, max: 100, value: 40 },
  { key: "clause_pruning", label: "Clause pruning", min: 0, max: 100, value: 60 },
  { key: "pronoun_resolution", label: "Pronoun resolution", min: 0, max: 100, value: 60 },
  { key: "temporal_sensitivity", label: "Temporal sensitivity", min: 0, max: 100, value: 40 },
  { key: "domain_specificity", label: "Domain specificity", min: 0, max: 100, value: 40 },
  { key: "summary_aggressiveness", label: "Summary aggressiveness", min: 0, max: 100, value: 60 },
  { key: "style_variance", label: "Style variance", min: 0, max: 100, value: 30 },
];

function renderSliders() {
  if (!sliderContainer) return;
  sliderContainer.innerHTML = "";
  nlpParams.forEach((param) => {
    const row = document.createElement("div");
    row.className = "slider";
    const label = document.createElement("label");
    label.textContent = `${param.label} (${param.value})`;
    const input = document.createElement("input");
    input.type = "range";
    input.min = param.min;
    input.max = param.max;
    input.value = param.value;
    input.addEventListener("input", () => {
      param.value = Number(input.value);
      label.textContent = `${param.label} (${param.value})`;
      scheduleSync();
    });
    row.appendChild(label);
    row.appendChild(input);
    sliderContainer.appendChild(row);
  });
  if (sliderCount) {
    sliderCount.textContent = String(nlpParams.length);
  }
}

async function syncParams() {
  const payload = { session_id: sessionId, nlp_params: {} };
  nlpParams.forEach((param) => {
    payload.nlp_params[param.key] = param.value;
  });
  await fetch(`${apiBase}/config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

let syncTimer = null;
function scheduleSync() {
  if (syncTimer) clearTimeout(syncTimer);
  syncTimer = setTimeout(() => {
    syncParams();
  }, 300);
}

renderSliders();
syncParams();

if (trainStatus) {
  trainStatus.textContent = "Ready";
}

function addMessage(text, role) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

function addBadge(node, badgeText) {
  if (!badgeText) return;
  const badge = document.createElement("div");
  badge.className = "badge";
  badge.textContent = badgeText;
  node.appendChild(badge);
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question) return;
  addMessage(question, "user");
  input.value = "";

  const bot = addMessage("", "bot");
  const params = new URLSearchParams({
    question,
    refresh: refresh.checked ? "1" : "0",
    grade_level: String(Number(askGrade.value || 10)),
    session_id: sessionId,
  });

  const source = new EventSource(`${apiBase}/ask_stream?${params.toString()}`);
  let buffer = "";
  source.onmessage = (event) => {
    const payload = JSON.parse(event.data);
    if (payload.delta) {
      buffer += payload.delta;
      bot.textContent = buffer;
    }
    if (payload.done) {
      source.close();
      bot.textContent = payload.answer || buffer;
      const badge = payload.meta && payload.meta.badge ? payload.meta.badge : "";
      addBadge(bot, badge);
    }
  };

  source.onerror = () => {
    source.close();
    bot.textContent = "Connection error.";
  };
});

trainButton.addEventListener("click", async () => {
  const raw = trainInput.value || "";
  const questions = raw
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  if (questions.length === 0) {
    trainStatus.textContent = "Add at least one line to train.";
    return;
  }

  trainStatus.textContent = `Training ${questions.length} items...`;
  trainButton.disabled = true;

  try {
    const response = await fetch(`${apiBase}/train`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        questions,
        dim: Number(trainDim.value || 200),
        grade_level: Number(trainGrade.value || 10),
        max_sources: Number(trainSources.value || 1),
        workers: Number(trainWorkers.value || 6),
        full: trainFull.checked,
        use_word2vec: trainWord2Vec.checked,
        session_id: sessionId,
      }),
    });
    const payload = await response.json();
    if (response.ok) {
      trainStatus.textContent = `Trained ${payload.trained} items.`;
    } else {
      trainStatus.textContent = payload.error || "Training failed.";
    }
  } catch (err) {
    trainStatus.textContent = "Training request failed.";
  } finally {
    trainButton.disabled = false;
  }
});
