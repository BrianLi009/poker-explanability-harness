// Best-effort capture of GTO Wizard's Summary tab into spot-file rows.
//
// How to use: open a node in GTO Wizard, click the Summary tab in the right
// panel (with no hand cell selected, so it lists every combo), open the browser
// console and paste this file. It scrolls the virtualised table, reads every
// row and prints JSON you can paste into a spot file:
//
//   { "node": { "player": "?", "actions": {...} },   // range-weighted averages
//     "hands": [ { "hand": "A4s", "strategy": {...}, "ev_best": 0.05, "weight": 1 }, ... ],
//     "combos": [ ... per-combo rows ... ] }
//
// It reads the page the way GTO Wizard renders it today (Oct 2026); if the
// DOM changes, the selectors at the top are the only thing to update.
// It only reads what is on screen: nothing is sent anywhere.

(async () => {
  const ROW_ANCHOR = '[data-tst="td_summary_idx"]'; // first cell of each Summary row
  const CARD_VALUE = ".cardsymbols_value"; // rank text; suit is in a color-default-<s> class
  const RANKS = "23456789TJQKA";

  const readVisible = () =>
    [...document.querySelectorAll(ROW_ANCHOR)].map((first) => {
      const cells = [...first.parentElement.children];
      const hand = [...cells[0].querySelectorAll(CARD_VALUE)]
        .map((v) => v.textContent.trim() + ((v.className.match(/color-default-([shdc])/) || [])[1] || "?"))
        .join("");
      const strategy = {};
      const parts = cells[1].innerText.split("\n").map((x) => x.trim()).filter(Boolean);
      for (let i = 0; i + 1 < parts.length; i += 2) strategy[parts[i]] = parseFloat(parts[i + 1]);
      const cols = cells.slice(2).map((c) => c.innerText.trim().split("\n")[0]);
      return { hand, strategy, weight: parseFloat(cols[0]), ev: parseFloat(cols[1]) };
    });

  const first = document.querySelector(ROW_ANCHOR);
  if (!first) {
    console.warn("Open the Summary tab (no hand selected) first.");
    return;
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
    const g = (byClass[classOf(c.hand)] ||= { w: 0, n: 0, ev: 0, s: Object.fromEntries(actions.map((a) => [a, 0])) });
    g.w += w;
    g.n += 1;
    g.ev += w * (isNaN(c.ev) ? 0 : c.ev);
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
      strategy: Object.fromEntries(actions.map((a) => [a, +(g.s[a] / g.w).toFixed(1)])),
    }));
  const out = {
    node: { player: "?", actions: Object.fromEntries(actions.map((a) => [a, +(total[a] / W).toFixed(2)])) },
    range_combos: +W.toFixed(2),
    hands,
    combos,
  };
  console.log(JSON.stringify(out, null, 1));
  return out;
})();
