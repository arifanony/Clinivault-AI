"""Single-page HTML for the observability UI (Manual Query Mode).

Plain HTML + vanilla JS, no framework. Renders the RunTrace produced
by pipeline.run_query() exactly as received: every value displayed
comes from the trace; missing fields render as an em dash rather than
being fabricated. All trace-derived strings are HTML-escaped.
"""

PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Clinivault AI — Observability Console</title>
<style>
  body { font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
         margin: 0; background: #f4f5f7; color: #1d2129; }
  header { background: #1f2d3d; color: #fff; padding: 12px 20px; }
  header h1 { font-size: 18px; margin: 0; font-weight: 600; }
  header .sub { font-size: 12px; color: #9fb3c8; margin-top: 2px; }
  main { max-width: 1200px; margin: 0 auto; padding: 16px 20px 60px; }
  .card { background: #fff; border: 1px solid #d9dee4; border-radius: 6px;
          margin-top: 16px; padding: 14px 16px; }
  .card h2 { font-size: 14px; margin: 0 0 10px; color: #1f2d3d;
             text-transform: uppercase; letter-spacing: .04em; }
  .controls { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
  .controls input[type=text] { flex: 1 1 420px; padding: 8px 10px; font-size: 14px;
                               border: 1px solid #c3ccd6; border-radius: 4px; }
  .controls input[type=number] { width: 80px; padding: 8px; border: 1px solid #c3ccd6;
                                 border-radius: 4px; }
  button { padding: 8px 16px; font-size: 14px; border: 0; border-radius: 4px;
           background: #2b6cb0; color: #fff; cursor: pointer; }
  button.secondary { background: #718096; }
  button:disabled { opacity: .55; cursor: wait; }
  .status { margin-top: 12px; padding: 8px 12px; border-radius: 4px; font-size: 13px; }
  .status.running { background: #fefcbf; }
  .status.ok { background: #c6f6d5; }
  .status.error { background: #fed7d7; color: #742a2a; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #e2e8f0; }
  th { background: #edf2f7; font-weight: 600; }
  tr.selected td { background: #ebf8ff; font-weight: 600; }
  .badge { display: inline-block; padding: 1px 8px; border-radius: 10px;
           font-size: 11px; font-weight: 600; }
  .badge.sel { background: #2b6cb0; color: #fff; }
  .badge.unsel { background: #cbd5e0; color: #2d3748; }
  .badge.ok { background: #c6f6d5; color: #22543d; }
  .badge.no { background: #fefcbf; color: #744210; }
  .badge.err { background: #fed7d7; color: #742a2a; }
  .kv { font-size: 13px; display: grid; grid-template-columns: 220px 1fr; row-gap: 4px; }
  .kv dt { color: #4a5568; }
  .kv dd { margin: 0; font-family: ui-monospace, Consolas, monospace; }
  pre.prompt { background: #1a202c; color: #e2e8f0; padding: 12px; border-radius: 4px;
               overflow: auto; max-height: 420px; font-size: 12px; white-space: pre-wrap;
               font-family: ui-monospace, Consolas, monospace; }
  details { margin-top: 8px; }
  summary { cursor: pointer; font-size: 13px; color: #2b6cb0; }
  .answer { background: #f0fff4; border: 1px solid #c6f6d5; border-radius: 4px;
            padding: 12px; white-space: pre-wrap; font-size: 13px; }
  .stages { display: flex; flex-wrap: wrap; gap: 8px; font-size: 12px; }
  .stage { border: 1px solid #d9dee4; border-radius: 4px; padding: 6px 10px; background: #fff; }
  .stage b { display: block; font-size: 12px; }
  .muted { color: #718096; }
  .hidden { display: none; }
</style>
</head>
<body>
<header>
  <h1>Clinivault AI — Observability Console</h1>
  <div class="sub">V1 · Manual Query Mode · developer/debug tool — renders the RunTrace from run_query() verbatim</div>
</header>
<main>

<div class="card">
  <div class="controls">
    <input type="text" id="query" value="criteria for the diagnosis of diabetes"
           placeholder="Query">
    <label for="top_k">Top-K</label>
    <input type="number" id="top_k" value="5" min="1" max="50">
    <button id="run" onclick="runQuery()">Run Query</button>
    <button class="secondary" onclick="resetAll()">Clear</button>
  </div>
  <div id="status" class="status hidden"></div>
</div>

<section id="trace" class="hidden">

  <div class="card">
    <h2>Pipeline Overview</h2>
    <div class="stages" id="stages"></div>
  </div>

  <div class="card">
    <h2>Retrieval Trace</h2>
    <dl class="kv" id="retrieval-meta"></dl>
    <details open><summary>Candidates (full ranked list; selected = passed downstream)</summary>
      <table id="candidates">
        <thead><tr><th>Rank</th><th>Selected</th><th>chunk_id</th><th>document_id</th>
                   <th>page</th><th>score</th></tr></thead>
        <tbody></tbody>
      </table>
    </details>
  </div>

  <div class="card">
    <h2>Context Trace</h2>
    <dl class="kv" id="context-meta"></dl>
    <details open><summary>Evidence supplied downstream (exact text)</summary>
      <div id="evidence"></div>
    </details>
  </div>

  <div class="card">
    <h2>Prompt (exact, as constructed)</h2>
    <pre class="prompt" id="prompt"></pre>
  </div>

  <div class="card">
    <h2>Generation Trace</h2>
    <dl class="kv" id="generation-meta"></dl>
    <details open><summary>Answer</summary><div class="answer" id="answer"></div></details>
  </div>

  <div class="card">
    <h2>Grounding Analysis</h2>
    <p style="font-size:13px; margin:4px 0;">Automatic claim-to-evidence evaluation is not available yet.</p>
    <p class="muted" style="font-size:12px;">This section is a placeholder for a future
    grounding evaluator. No claim mapping, scores, or pass/fail values are produced here.</p>
  </div>

  <div class="card">
    <details><summary>Raw RunTrace (JSON)</summary><pre class="prompt" id="raw"></pre></details>
  </div>

</section>
</main>

<script>
function esc(s) {
  if (s === null || s === undefined) return '';
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function dash(s) { return (s === null || s === undefined || s === '') ? '—' : esc(s); }
function ms(v) { return (typeof v === 'number') ? v.toFixed(2) + ' ms' : '—'; }
function num(v) { return (typeof v === 'number') ? esc(v) : '—'; }

function kvList(pairs) {
  return pairs.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${dash(v)}</dd>`).join('');
}

function setStatus(cls, msg) {
  const el = document.getElementById('status');
  el.className = 'status ' + cls;
  el.textContent = msg;
}

function runQuery() {
  const query = document.getElementById('query').value.trim();
  const topK = document.getElementById('top_k').value;
  document.getElementById('trace').classList.add('hidden');
  document.getElementById('run').disabled = true;
  setStatus('running', 'Running pipeline…');
  fetch('/api/query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query, top_k: topK})
  }).then(r => r.json().then(b => [r.status, b])).then(([code, body]) => {
    document.getElementById('run').disabled = false;
    if (!body.ok) { setStatus('error', 'Error: ' + (body.error || 'unknown error')); return; }
    setStatus('ok', 'Run complete.');
    renderTrace(body.trace);
  }).catch(e => {
    document.getElementById('run').disabled = false;
    setStatus('error', 'Request failed: ' + e);
  });
}

function resetAll() {
  document.getElementById('trace').classList.add('hidden');
  document.getElementById('status').className = 'status hidden';
  document.getElementById('query').value = 'criteria for the diagnosis of diabetes';
  document.getElementById('top_k').value = 5;
}

function renderTrace(t) {
  const rt = t.retrieval_trace || {}, ct = t.context_trace || {}, gt = t.generation_trace || {};
  const res = t.result || {};

  document.getElementById('trace').classList.remove('hidden');

  // Pipeline overview — real timings only; '—' when absent.
  const stages = [
    ['Embedding', rt.embedding_ms],
    ['Context', ct.context_ms],
    ['Prompt', (gt.timings || {}).prompt_construction_ms],
    ['Generation', (gt.timings || {}).llm_generation_ms]
  ];
  document.getElementById('stages').innerHTML = stages.map(([n, v]) =>
    `<div class="stage"><b>${esc(n)}</b><span class="muted">${ms(v)}</span></div>`).join('');

  // Retrieval panel.
  const rp = rt.provider || {};
  const cands = rt.candidates || [];
  document.getElementById('retrieval-meta').innerHTML = kvList([
    ['provider', rp.name], ['dimension', rp.dimension],
    ['embedding_ms', ms(rt.embedding_ms)], ['top_k', rt.top_k],
    ['total_candidates', rt.total_candidates],
    ['store document_id', (rt.store || {}).document_id]
  ]);
  document.querySelector('#candidates tbody').innerHTML = cands.map(c =>
    `<tr class="${c.selected ? 'selected' : ''}">` +
    `<td>${num(c.rank)}</td>` +
    `<td><span class="badge ${c.selected ? 'sel' : 'unsel'}">${c.selected ? 'selected' : 'not selected'}</span></td>` +
    `<td>${dash(c.chunk_id)}</td><td>${dash(c.document_id)}</td>` +
    `<td>${num(c.page_number)}</td><td>${num(c.score)}</td></tr>`).join('');

  // Context panel.
  const ev = ct.evidence || [];
  document.getElementById('context-meta').innerHTML = kvList([
    ['evidence_count', ct.evidence_count], ['input_retrieval_count', ct.input_retrieval_count],
    ['context_ms', ms(ct.context_ms)]
  ]);
  document.getElementById('evidence').innerHTML = ev.map(e =>
    `<div class="stage" style="margin-bottom:8px;"><b>rank ${num(e.rank)} · ${dash(e.chunk_id)} · doc ${dash(e.document_id)} · page ${num(e.page_number)} · score ${num(e.score)}</b>` +
    `<div style="white-space:pre-wrap; font-size:12px; margin-top:6px;">${esc(e.text)}</div></div>`).join('');

  // Prompt panel — exact text.
  document.getElementById('prompt').textContent = gt.prompt_text || '';

  // Generation panel.
  const tm = gt.timings || {}, nt = gt.nested_timings || {};
  document.getElementById('generation-meta').innerHTML = kvList([
    ['provider', gt.provider], ['model', gt.model], ['status', gt.status],
    ['provider_called', gt.provider_called],
    ['prompt_construction_ms', ms(tm.prompt_construction_ms)],
    ['llm_generation_ms', ms(tm.llm_generation_ms)],
    ['generation total_ms', ms(tm.total_ms)],
    ['query_embedding_ms', ms(nt.query_embedding_ms)],
    ['retrieval_ms', ms(nt.retrieval_ms)],
    ['context_construction_ms', ms(nt.context_construction_ms)],
    ['full pipeline total_ms', ms(nt.total_ms)],
    ['usage', gt.usage ? JSON.stringify(gt.usage) : null]
  ]);
  document.getElementById('answer').textContent = (gt.answer !== null && gt.answer !== undefined) ? gt.answer : '—';

  document.getElementById('raw').textContent = JSON.stringify(t, null, 2);
}
</script>
</body>
</html>
"""