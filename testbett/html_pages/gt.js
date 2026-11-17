// Ground truth export: every [data-gt] element -> type, box, text, state, plus text spans for text scoring.
function S(){ return +(new URLSearchParams(location.search).get('s') || 1); }
function exportGT(){
  const out = {size: [1920, 1080], elements: [], spans: [], zorder: []};
  const R = r => [Math.round(r.left), Math.round(r.top), Math.round(r.right), Math.round(r.bottom)];
  const vis = e => { let x = e; while (x && x.nodeType === 1) { const s = getComputedStyle(x);
      if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) return false; x = x.parentElement; }
      const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const tbox = e => { const rg = document.createRange(); rg.selectNodeContents(e); return R(rg.getBoundingClientRect()); };
  let n = 0;
  document.querySelectorAll('[data-gt]').forEach(e => {
    if (!vis(e)) return;
    const t = e.dataset.gt; let text = '', st = {}, box = R(e.getBoundingClientRect()), span = null;
    if (t === 'textfield') {
      if (e.tagName === 'SELECT') text = e.options[e.selectedIndex].text;
      else { text = e.value || e.placeholder || ''; st.placeholder = !e.value && !!e.placeholder; }
      st.focused = e.classList.contains('focus');
      if (e.type === 'password') { st.password = true; text = ''; }
      if (text) span = [box[0] + 8, box[1] + 4, box[2] - 8, box[3] - 4];
    } else if (t === 'checkbox') {
      const inp = e.querySelector('input'), lab = e.querySelector('span');
      box = R(inp.getBoundingClientRect()); text = lab.innerText.trim(); st.checked = inp.checked; span = tbox(lab);
    } else if (t === 'progressbar') { st.value = +e.dataset.value; }
    else if (['window', 'list', 'panel', 'toast', 'image'].includes(t)) { text = e.dataset.title || ''; }
    else if (t === 'icon') { text = e.dataset.label || ''; if (e.dataset.labelEl) { const l = document.getElementById(e.dataset.labelEl); span = tbox(l); } }
    else { text = e.innerText.trim().replace(/\s+/g, ' '); if (text) span = tbox(e); if (t === 'text' && text) box = span; }
    if (e.classList.contains('sel')) st.selected = true;
    if (t === 'window') out.zorder.push('h' + n);
    out.elements.push({id: 'h' + (n++), type: t, box, text, state: st, ignore: e.dataset.ignore === '1', parent: null});
    if (span && text) out.spans.push({text, box: span, owner: 'h' + (n - 1)});
  });
  // occlusion: elements under an overlay (data-overlay) are ignored when partly hidden, dropped when hidden
  const ov = [...document.querySelectorAll('[data-overlay]')].filter(vis).map(e => [e, R(e.getBoundingClientRect())]);
  const els = [...document.querySelectorAll('[data-gt]')].filter(vis);
  out.elements = out.elements.filter((g, i) => {
    const node = els[i];
    for (const [o, b] of ov) {
      if (o === node || o.contains(node)) continue;
      const ix = Math.max(0, Math.min(b[2], g.box[2]) - Math.max(b[0], g.box[0]));
      const iy = Math.max(0, Math.min(b[3], g.box[3]) - Math.max(b[1], g.box[1]));
      const a = (g.box[2] - g.box[0]) * (g.box[3] - g.box[1]);
      if (ix * iy >= 0.97 * a) return false;
      if (ix * iy > 0) g.ignore = true;
    }
    return true;
  });
  const keep = new Set(out.elements.map(g => g.id));
  out.spans = out.spans.filter(sp => keep.has(sp.owner) && !out.elements.find(g => g.id === sp.owner).ignore);
  out.zorder.reverse();
  let pre = document.getElementById('gt');
  if (!pre) { pre = document.createElement('pre'); pre.id = 'gt'; pre.style.display = 'none'; document.body.appendChild(pre); }
  pre.textContent = JSON.stringify(out);
}
window.addEventListener('load', () => { if (window.applyState) applyState(S()); exportGT(); });
