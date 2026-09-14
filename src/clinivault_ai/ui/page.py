"""Single-page HTML for the Clinivault AI RAG investigation console.

Plain HTML + vanilla JS, no framework. Renders the RunTrace produced by
pipeline.run_query() exactly as received: every value displayed comes from
the trace. All trace-derived strings are HTML-escaped. The page flows:
Retrieval -> Context -> Prompt -> Generation -> Answer. Retrieval rows are
expandable to show exact retrieved text, selected state, and whether the
chunk reached context.
"""

from __future__ import annotations

PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Clinivault AI — RAG Investigation Console</title>
<style>
  :root { --ink:#1d2129; --muted:#5f6b7a; --line:#d9dee4; --bg:#f4f5f7;
          --brand:#1f2d3d; --accent:#2b6cb0; }
  * { box-sizing: border-box; }
  body { margin:0; font-family:-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
         background:var(--bg); color:var(--ink); }
  header { background:var(--brand); color:#fff; padding:14px 22px; }
  header h1 { margin:0; font-size:20px; font-weight:700; }
  header .sub { font-size:12px; color:#b8c7db; margin-top:3px; letter-spacing:.02em; }
  main { max-width:1280px; margin:0 auto; padding:16px 22px 60px; }
  .card { background:#fff; border:1px solid var(--line); border-radius:6px;
          margin-top:16px; padding:14px 16px; }
  .card > h2 { font-size:13px; margin:0 0 4px; color:var(--brand);
               text-transform:uppercase; letter-spacing:.05em; }
  .card > .desc { font-size:12px; color:var(--muted); margin:2px 0 10px; }
  .controls { display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
  label.tk { font-size:13px; color:var(--muted); }
  .controls input[type=text] { flex:1 1 460px; padding:9px 10px; font-size:14px;
                               border:1px solid #c3ccd6; border-radius:5px; }
  .controls input[type=number] { width:78px; padding:9px; font-size:14px;
                                 border:1px solid #c3ccd6; border-radius:5px; }
  button { padding:9px 18px; font-size:14px; border:0; border-radius:5px;
           background:var(--accent); color:#fff; cursor:pointer; }
  button.secondary { background:#718096; }
  button:disabled { opacity:.55; cursor:wait; }
  .status { margin-top:12px; padding:8px 12px; border-radius:5px; font-size:13px; }
  .status.running { background:#fefcbf; }
  .status.ok { background:#c6f6d5; color:#22543d; }
  .status.error { background:#fed7d7; color:#742a2a; }
  .status.warn { background:#feebc8; color:#7b341e; }
  .hidden { display:none; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th, td { text-align:left; padding:6px 8px; border-bottom:1px solid #e2e8f0; vertical-align:top; }
  th { background:#edf2f7; font-weight:600; }
  .badge { display:inline-block; padding:1px 9px; border-radius:10px; font-size:11px; font-weight:600; }
  .badge.sel { background:var(--accent); color:#fff; }
  .badge.unsel { background:#cbd5e0; color:#2d3748; }
  .badge.pass { background:#c6f6d5; color:#22543d; }
  .badge.nopass { background:#fed7d7; color:#742a2a; }
  .badge.ok { background:#c6f6d5; color:#22543d; }
  .badge.no { background:#fefcbf; color:#744210; }
  .badge.err { background:#fed7d7; color:#742a2a; }
  .kv { font-size:12.5px; display:grid; grid-template-columns:200px 1fr; row-gap:4px; }
  .kv.retr { grid-template-columns:170px 1fr; }
  .kv dt { color:var(--muted); }
  .kv dd { margin:0; font-family:ui-monospace,Consolas,monospace; word-break:break-word; }
pre.mono { background:#1a202c; color:#e2e8f0; padding:12px; border-radius:5px;
             overflow:auto; max-height:480px; font-size:12px; white-space:pre-wrap;
             font-family:ui-monospace,Consolas,monospace; }
  details.chunk { margin:0; border-top:1px solid #e2e8f0; }
  details.chunk > summary { cursor:pointer; padding:7px 4px; font-size:13px; }
  details.chunk > summary:hover { background:#f7fafc; }
  .chunk-body { padding:6px 4px 12px; }
  .chip { display:inline-block; margin:0 6px 4px 0; padding:1px 8px; border-radius:11px;
          font-size:11px; font-weight:600; }
  .chip.sel { background:#b3e0ff; color:#04324d; }
  .chip.pass { background:#c6f6d5; color:#22543d; }
  .chip.unsel { background:#e2e8f0; color:#4a5568; }
  .chip.nopass { background:#fed7d7; color:#742a2a; }
  .chunk-text { white-space:pre-wrap; font-size:12px; word-break:break-word;
                background:#f7fafc; border:1px solid #e2e8f0; border-radius:5px;
                padding:10px; max-height:320px; overflow:auto; }
  .evidence { background:#f8fbfe; border:1px solid #dbe7f3; border-radius:6px;
              padding:10px 12px; margin-bottom:10px; }
  .evidence .head { font-size:12.5px; font-weight:600; margin-bottom:6px; }
  .evidence .text { white-space:pre-wrap; font-size:12px; word-break:break-word; }
  .stages { display:flex; flex-wrap:wrap; gap:8px; font-size:12px; }
  .stage { border:1px solid var(--line); border-radius:5px; padding:6px 10px; background:#fff; }
  .stage b { display:block; font-size:12px; color:var(--brand); }
  .stage .muted { color:var(--muted); font-family:ui-monospace,Consolas,monospace; }
  .arrow { color:var(--accent); text-decoration:none; cursor:pointer; }
  .arrow:hover { text-decoration:underline; }
  .answer { background:#f0fff4; border:1px solid #c6f6d5; border-radius:6px;
            padding:12px; white-space:pre-wrap; font-size:13px; word-break:break-word; }
  .note { background:#fefcbf; border:1px solid #f6e05e; border-radius:5px;
          padding:8px 12px; font-size:12.5px; color:#744210; }
  .muted { color:var(--muted); }
  summary.noev { cursor:pointer; font-size:13px; color:var(--accent); }
</style>
</head>
<body>
<header>
  <h1>Clinivault AI</h1>
  <div class="sub">RAG Observability / Investigation Console &mdash; Manual Query Mode</div>
</header>
<main>
  <div class="card">
    <h2>Run Query</h2>
    <div class="desc">Execute the real pipeline (retrieval &rarr; context &rarr; generation) and inspect every stage.</div>
    <div class="controls">
      <input type="text" id="query" value="criteria for the diagnosis of diabetes"
             autocomplete="off" spellcheck="false"
             placeholder="Enter a query over the indexed document(s)">
      <label class="tk" for="top_k">Top-K</label>
      <input type="number" id="top_k" value="5" min="1" max="50" step="1">
      <button id="run">Run Query</button>
      <button class="secondary" id="reset">Reset</button>
    </div>
    <div id="status" class="status hidden"></div>
  </div>

  <div class="card">
    <h2>Pipeline</h2>
    <div class="desc">Actual stage timings from the trace; &ldquo;&mdash;&rdquo; when a stage produced no measurement.</div>
    <div class="stages" id="stages"></div>
  </div>

  <div class="card">
    <h2>Retrieval</h2>
    <div class="desc">All chunks the retriever scored, in rank order. Expand a row to see the exact retrieved text, the selected state, and whether it reached context.</div>
    <div class="kv retr" id="retrieval-meta"></div>
    <table>
      <thead><tr><th>Rank</th><th>Selected</th><th>To Context</th><th>Chunk ID</th><th>Doc</th><th>Page</th><th>Score</th></tr></thead>
      <tbody id="cand-tbody"></tbody>
    </table>
  </div>

  <div class="card">
    <h2>Context / Evidence Sent to Generator</h2>
    <div class="desc">The exact evidence items that actually reached generation (context_trace).</div>
    <div class="kv" id="context-meta"></div>
    <div id="evidence"></div>
  </div>

  <div class="card">
    <h2>Prompt Sent to Generator</h2>
    <div class="desc">Exact prompt text (generation_trace.prompt_text), shown verbatim.</div>
    <pre class="mono" id="prompt"></pre>
  </div>

  <div class="card">
    <h2>Generation</h2>
    <div class="desc">Provider, timing, token usage, and the generated answer.</div>
    <div class="kv" id="generation-meta"></div>
    <h3 style="margin:14px 0 6px;font-size:13px;">Generated Answer</h3>
    <div class="answer" id="answer"></div>
  </div>

  <div class="card">
    <h2>Grounding Analysis</h2>
    <div class="note">Automatic claim-to-evidence evaluation is not available yet.</div>
  </div>

  <div class="card">
    <details>
      <summary class="noev">Raw Run Trace</summary>
      <pre class="mono" id="raw" style="margin-top:8px;"></pre>
    </details>
  </div>
</main>
<script>
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
    return '&#' + c.charCodeAt(0) + ';';
  });
}
function dash(v) { return (v === null || v === undefined || v === '') ? '—' : esc(v); }
function num(v) { return (typeof v === 'number') ? String(Number.isInteger(v) ? v : +v.toFixed(4)) : dash(v); }
function ms(v) {
  if (typeof v !== 'number') return '—';
  if (v >= 1000) return (v / 1000).toFixed(2) + ' s';
  return v.toFixed(2) + ' ms';
}
function setStatus(cls, text) {
  var el = document.getElementById('status');
  el.className = 'status ' + cls;
  el.textContent = text;
}
function runQuery() {
  var q = document.getElementById('query').value;
  var k = document.getElementById('top_k').value;
  setStatus('running', 'Running pipeline…');
  document.getElementById('run').disabled = true;
  fetch('/api/query', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: q, top_k: k })
  }).then(function (r) { return r.json().then(function (b) { return { ok: r.ok, body: b }; }); })
    .then(function (res) {
      document.getElementById('run').disabled = false;
      if (!res.body.ok) { setStatus('error', 'Error: ' + res.body.error); return; }
      setStatus('ok', 'Complete');
      renderTrace(res.body.trace);
    })
    .catch(function (e) {
      document.getElementById('run').disabled = false;
      setStatus('error', 'Request failed: ' + e);
    });
}
function resetAll() {
  document.getElementById('query').value = 'criteria for the diagnosis of diabetes';
  document.getElementById('top_k').value = 5;
  document.getElementById('status').className = 'status hidden';
}
function renderTrace(t) {
  var rt = t.retrieval_trace || {}, ct = t.context_trace || {}, gt = t.generation_trace || {};
  var res = t.result || {};
  var noEv = (gt.status === 'no_evidence' || res.status === 'no_evidence');

  var nst = gt.nested_timings || {};
  var stages = [
    ['Query', rt.query || gt.query],
    ['Embedding', rt.embedding_ms],
    ['Retrieval', nst.retrieval_ms],
    ['Context', ct.context_ms],
    ['Prompt', (gt.timings || {}).prompt_construction_ms],
    ['Generation', (gt.timings || {}).llm_generation_ms]
  ];
  document.getElementById('stages').innerHTML = stages.map(function (s) {
    return '<div class="stage"><b>' + esc(s[0]) + '</b><span class="muted">' + (ms(s[1])) + '</span></div>';
  }).join('');

  var rp = rt.provider || {}, st = rt.store || {};
  document.getElementById('retrieval-meta').innerHTML = kvHtml([
    ['embedding provider', rp.name], ['dimension', rp.dimension],
    ['query embedding', ms(rt.embedding_ms)], ['configured top_k', rt.top_k],
    ['retrieval', ms(nst.retrieval_ms)],
    ['indexed candidates', rt.total_candidates],
    ['store document', st.document_id]
  ]);

  var ev = ct.evidence || [];
  var ctxIds = {}; ev.forEach(function (e) { ctxIds[e.chunk_id] = true; });

  var cands = rt.candidates || [];
  document.getElementById('cand-tbody').innerHTML = cands.map(function (c) {
    var sel = !!c.selected, passed = !!ctxIds[c.chunk_id];
    return '<details class="chunk" data-cid="' + esc(c.chunk_id) + '">' +
      '<summary><strong>' + num(c.rank) + '</strong> &nbsp;' +
      '<span class="badge ' + (sel ? 'sel' : 'unsel') + '">' + (sel ? 'SELECTED' : 'not selected') + '</span> ' +
      '<span class="badge ' + (passed ? 'pass' : 'nopass') + '">' + (passed ? 'TO CONTEXT' : 'NOT to context') + '</span> &nbsp;' +
      '<span class="mono">' + dash(c.chunk_id) + '</span> &middot; doc ' + dash(c.document_id) +
      ' &middot; page ' + num(c.page_number) + ' &middot; score ' + num(c.score) + '</summary>' +
      '<div class="chunk-body">' +
      '<span class="chip ' + (sel ? 'sel' : 'unsel') + '">Selected: ' + (sel ? 'YES' : 'NO') + '</span>' +
      '<span class="chip ' + (passed ? 'pass' : 'nopass') + '">Passed to Context: ' + (passed ? 'YES' : 'NO') + '</span>' +
      (passed ? '<a class="arrow" href="#ctx-' + esc(c.chunk_id) + '">&#8595; see in Context</a>' : '') +
      '<div class="chunk-text">' + dash(c.text || 'retrieved text unavailable') + '</div>' +
      '</div></details>';
  }).join('');

  document.getElementById('context-meta').innerHTML = kvHtml([
    ['input retrieval count', ct.input_retrieval_count],
    ['evidence count', ct.evidence_count],
    ['context construction', ms(ct.context_ms)]
  ]);
  document.getElementById('evidence').innerHTML = ev.map(function (e) {
    return '<div class="evidence" id="ctx-' + esc(e.chunk_id) + '">' +
      '<div class="head">rank ' + num(e.rank) + ' &middot; ' + dash(e.chunk_id) +
      ' &middot; doc ' + dash(e.document_id) + ' &middot; page ' + num(e.page_number) +
      ' &middot; score ' + num(e.score) + '</div>' +
      '<div class="text">' + esc(e.text) + '</div></div>';
  }).join('');
document.getElementById('prompt').textContent = noEv ? '' : (gt.prompt_text || '');

  var tm = gt.timings || {};
  document.getElementById('generation-meta').innerHTML = kvHtml([
    ['provider', gt.provider], ['model', gt.model], ['status', gt.status],
    ['provider_called', gt.provider_called],
    ['prompt construction', ms(tm.prompt_construction_ms)],
    ['llm generation', ms(tm.llm_generation_ms)],
    ['generation total', ms(tm.total_ms)],
    ['query embedding', ms(nst.query_embedding_ms)],
    ['retrieval', ms(nst.retrieval_ms)],
    ['context construction', ms(nst.context_construction_ms)],
    ['full pipeline total', ms(nst.total_ms)],
    ['token usage', gt.usage ? JSON.stringify(gt.usage) : null]
  ]);
  if (noEv) {
    document.getElementById('answer').textContent = 'No evidence was supplied; generation was not called (status: no_evidence).';
  } else {
    document.getElementById('answer').textContent = (gt.answer != null) ? gt.answer : '—';
  }

  document.getElementById('raw').textContent = JSON.stringify(t, null, 2);
}
function kvHtml(pairs) {
  return pairs.map(function (p) {
    var v = (p[1] === null || p[1] === undefined || p[1] === '') ? '—' :
            (typeof p[1] === 'number' ? p[1] : esc(String(p[1])));
    return '<dt>' + esc(p[0]) + '</dt><dd>' + v + '</dd>';
  }).join('');
}
document.getElementById('run').addEventListener('click', runQuery);
document.getElementById('reset').addEventListener('click', resetAll);
document.getElementById('query').addEventListener('keydown', function (e) { if (e.key === 'Enter') runQuery(); });
</script>
</body>
</html>
"""