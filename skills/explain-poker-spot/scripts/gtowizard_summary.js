// Best-effort capture of GTO Wizard's Summary tab into spot-file rows.
//
// How to use: open a node in GTO Wizard, click the Summary tab in the right
// panel (with no hand cell selected, so it lists every combo), then either
// paste this file into the browser console, or run it with Claude in Chrome's
// page JavaScript tool. It scrolls the virtualised table, reads every row and
// returns a JSON string you can paste into a spot file:
//
//   { "node": { "player": "?", "actions": {...} },   // range-weighted averages
//     "hands": [ { "hand": "A4s", "strategy": {...}, "ev_best": 0.05, "equity": 41.3, "weight": 1 }, ... ],
//     "combos": [ ... per-combo rows ... ] }      // only with includeCombos: true
//
// It reads the page the way GTO Wizard renders it today (Oct 2026); if the
// DOM changes, the selectors at the top are the only thing to update.
// It only reads what is on screen: nothing is sent anywhere.

async function gwCaptureSummary({ includeCombos = false } = {}) {
  const ROW_ANCHOR = '[data-tst="td_summary_idx"]'; // first cell of each Summary row
  const HEAD_CELL = ".gw_table_head_cell"; // column headers: Hand, Strategy, Range, EV/CSTE, EQ %, ...
  const CARD_VALUE = ".cardsymbols_value"; // rank text; suit is in a color-default-<s> class
  const RANKS = "23456789TJQKA";

  // Column names after Hand and Strategy (GTO Wizard shows EV or CSTE, EQ %, EQR %, blockers...).
  const headerNames = () => {
    let t = document.querySelector(ROW_ANCHOR)?.parentElement;
    for (let i = 0; i < 6 && t; i++, t = t.parentElement) {
      const hs = [...t.querySelectorAll(HEAD_CELL)].map((e) => e.innerText.trim().replace(/\s+/g, " "));
      if (hs.length) return hs.slice(2);
    }
    return ["Range", "EV"];
  };
  const readVisible = () =>
    [...document.querySelectorAll(ROW_ANCHOR)].map((first) => {
      const cells = [...first.parentElement.children];
      const hand = [...cells[0].querySelectorAll(CARD_VALUE)]
        .map((v) => v.textContent.trim() + ((v.className.match(/color-default-([shdc])/) || [])[1] || "?"))
        .join("");
      const strategy = {};
      const parts = cells[1].innerText.split("\n").map((x) => x.trim()).filter(Boolean);
      for (let i = 0; i + 1 < parts.length; i += 2) strategy[parts[i]] = parseFloat(parts[i + 1]);
      const cols = cells.slice(2).map((c) => parseFloat(c.innerText.trim().split("\n")[0]));
      const named = Object.fromEntries(names.map((n, i) => [n, cols[i]]).filter(([, v]) => !isNaN(v)));
      const ev = named.EV ?? named.CSTE;
      return { hand, strategy, weight: named.Range ?? cols[0], ev, equity: named["EQ %"], columns: named };
    });

  const first = document.querySelector(ROW_ANCHOR);
  const names = first ? headerNames() : [];
  if (!first) {
    return { error: "Open the Summary tab (no hand selected) first." };
  }
  let scroller = first;
  while (scroller && !(scroller.scrollHeight > scroller.clientHeight + 5 && getComputedStyle(scroller).overflowY !== "visible")) {
    scroller = scroller.parentElement;
  }
  const seen = new Map();
  if (scroller) scroller.scrollTop = 0;
  for (let k = 0; k < 500; k++) {
    await new Promise((r) => setTimeout(r, 120));
    for (const row of readVisible()) if (!seen.has(row.hand)) seen.set(row.hand, row);
    if (!scroller || scroller.scrollTop + scroller.clientHeight >= scroller.scrollHeight - 2) break;
    scroller.scrollTop += scroller.clientHeight * 0.8;
  }
  if (scroller) scroller.scrollTop = 0;
  const combos = [...seen.values()];

  const classOf = (h) => {
    const [a, sa, b, sb] = h;
    if (a === b) return a + b;
    const [hi, lo] = RANKS.indexOf(a) > RANKS.indexOf(b) ? [a, b] : [b, a];
    return hi + lo + (sa === sb ? "s" : "o");
  };
  const actions = Object.keys(combos[0]?.strategy || {});
  const byClass = {};
  const total = Object.fromEntries(actions.map((a) => [a, 0]));
  let W = 0;
  for (const c of combos) {
    const w = isNaN(c.weight) ? 0 : c.weight;
    const g = (byClass[classOf(c.hand)] ||= { w: 0, n: 0, ev: 0, eq: 0, eqw: 0, s: Object.fromEntries(actions.map((a) => [a, 0])) });
    g.w += w;
    g.n += 1;
    g.ev += w * (c.ev == null || isNaN(c.ev) ? 0 : c.ev);
    if (c.equity != null && !isNaN(c.equity)) {
      g.eq += w * c.equity;
      g.eqw += w;
    }
    for (const a of actions) {
      g.s[a] += w * (c.strategy[a] || 0);
      total[a] += w * (c.strategy[a] || 0);
    }
    W += w;
  }
  const hands = Object.entries(byClass)
    .filter(([, g]) => g.w > 0)
    .map(([hand, g]) => ({
      hand,
      weight: +(g.w / (hand.length === 2 ? 6 : hand.endsWith("s") ? 4 : 12)).toFixed(3),
      ev_best: +(g.ev / g.w).toFixed(3),
      ...(g.eqw > 0 ? { equity: +(g.eq / g.eqw).toFixed(1) } : {}),
      strategy: Object.fromEntries(actions.map((a) => [a, +(g.s[a] / g.w).toFixed(1)])),
    }));
  const out = {
    node: { player: "?", actions: Object.fromEntries(actions.map((a) => [a, +(total[a] / W).toFixed(2)])) },
    range_combos: +W.toFixed(2),
    combos_read: combos.length,
    columns: names,
    ev_column: names.includes("EV") ? "EV" : names.includes("CSTE") ? "CSTE (ICM chip-equivalent EV)" : null,
    hands,
  };
  if (includeCombos) out.combos = combos;
  return out;
}

// Last expression: the JSON string (the console prints it, the JS tool returns it).
JSON.stringify(await gwCaptureSummary({ includeCombos: false }));
