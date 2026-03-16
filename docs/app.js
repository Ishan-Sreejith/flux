const taxonomyUrl = "./data/taxonomy.json";
const lexiconUrl = "./data/lexicon.json";

const state = {
  taxonomy: null,
  lexicon: null,
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

async function loadData() {
  const [taxonomy, lexicon] = await Promise.all([
    fetch(taxonomyUrl).then((r) => r.json()),
    fetch(lexiconUrl).then((r) => r.json()),
  ]);
  state.taxonomy = taxonomy;
  state.lexicon = lexicon;
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

function synthesizeAnswer(subject, prime, params) {
  if (!subject) return "I need a specific subject to explain.";
  const traits = traitList(params);
  if (traits.length) {
    return `${subject} is a ${prime.toLowerCase()} that tends to be ${traits.slice(0, 5).join(", ")}.`;
  }
  return `${subject} is a ${prime.toLowerCase()} in this schema.`;
}

function simulateFlow(res) {
  if (!res) return "Flowchart: no result.";
  const steps = res.path.map((step, idx) => {
    const bit = res.bitstring[idx] || "?";
    return `${idx + 1}. ${step} -> bit ${bit}`;
  });
  const params = Object.entries(res.params || {})
    .map(([k, v]) => `${k}(${PARAM_LABELS[k] || ""})=${Number(v).toFixed(2)}`)
    .join(", ");
  return [
    `Prime: ${res.prime}`,
    `Bitstring: ${res.bitstring}`,
    `Path:`,
    ...steps,
    params ? `Params: ${params}` : "",
  ]
    .filter(Boolean)
    .join("\n");
}

function contentTokens(text) {
  const tokens = tokenize(text);
  return tokens.filter((t) => !STOPWORDS.has(t) && t.length > 2);
}

function mainTerm(text) {
  const tokens = contentTokens(text);
  return tokens[0] || tokenize(text)[0] || text;
}

async function wikidataLookup(term) {
  const params = new URLSearchParams({
    action: "wbsearchentities",
    format: "json",
    language: "en",
    limit: "1",
    search: term,
    origin: "*",
  });
  const url = `https://www.wikidata.org/w/api.php?${params.toString()}`;
  const data = await fetch(url).then((r) => r.json());
  const hit = data?.search?.[0];
  if (!hit) return "";
  return hit.description || "";
}

async function liveLookup(term) {
  const url = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(term)}`;
  const data = await fetch(url).then((r) => r.json());
  if (!data || data.type === "https://mediawiki.org/wiki/HyperSwitch/errors/not_found") return "";
  return data.extract || "";
}

function bind() {
  const btn = document.getElementById("qa-btn");
  const input = document.getElementById("qa-input");
  const output = document.getElementById("qa-output");
  const liveToggle = document.getElementById("qa-live");

  btn.addEventListener("click", async () => {
    const text = input.value.trim();
    if (!text) return;
    const tokens = contentTokens(text);
    const encoded = tokens.map((t) => encode(t)).filter(Boolean);
    const params = aggregateParams(encoded);
    const subject = tokens[0] || mainTerm(text);
    const main = encode(subject);
    const prime = main?.prime || encoded[0]?.prime || "Object";
    const synthesized = synthesizeAnswer(subject, prime, params);

    const useLive = liveToggle.checked;
    const liveText = useLive ? await liveLookup(mainTerm(text)) : "";
    const webHint = liveText || (await wikidataLookup(mainTerm(text)));

    const flow = simulateFlow({
      prime,
      bitstring: main?.bitstring || encoded[0]?.bitstring || "",
      params,
      path: main?.path || encoded[0]?.path || [],
    });

    output.value = [
      `Answer: ${synthesized}`,
      webHint ? `Web hint: ${webHint}` : "",
      useLive && liveText ? "Source: Live override" : "Source: Wikidata",
      "",
      "Flowchart Simulation:",
      flow,
    ]
      .filter(Boolean)
      .join("\n");
  });
}

await loadData();
bind();
