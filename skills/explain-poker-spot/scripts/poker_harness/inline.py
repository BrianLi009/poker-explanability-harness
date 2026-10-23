"""A compact visual of a spot, sized to render inside the chat.

``render_inline`` returns an HTML fragment (no <html>/<head>/<body>) for an
inline widget tool such as the chat's visualizer: 680px wide, theme colours
from the host's CSS variables, no external requests. It shows, in the coach's
order:

* one tile per action of the node (the whole range's shape),
* preflop: the 13x13 grid coloured by each class's most-played action, mixed
  classes faded; clicking a class shows its strategy, per-action EVs when
  they were captured, and whether it is a border hand,
  postflop: the captured hand rows as strategy bars,
* the opponent's response as a bar, with the break-even fold line for a
  zero-equity bet,
* the first node of each other line.

The full dashboard (``dashboard``) remains the place for coverage, blockers,
rewind and every border table.
"""

from __future__ import annotations

import html
import json
import re

from .cards import all_hand_classes
from .framework import Report
from .shape import build_shape, norm_class
from .spot import Spot

JAM, RAISE, RAISE2, CALL, FOLD = "#A32D2D", "#EF9F27", "#D85A30", "#1D9E75", "#B4B2A9"


def action_colors(actions: list[str]) -> dict[str, str]:
    """GTO Wizard-like colours: all-in dark red, raises/bets amber then coral, call/check green, fold gray."""
    out: dict[str, str] = {}
    raises = 0
    for a in actions:
        low = a.lower()
        if re.search(r"all[\s-]?in|jam|shove", low):
            out[a] = JAM
        elif low.startswith(("raise", "bet")):
            out[a] = RAISE if raises == 0 else RAISE2
            raises += 1
        elif low.startswith(("call", "check")):
            out[a] = CALL
        elif low.startswith("fold"):
            out[a] = FOLD
        else:
            out[a] = "#7F77DD"
    return out


def _short(a: str) -> str:
    low = a.lower()
    if re.search(r"all[\s-]?in|jam|shove", low):
        return "jam"
    return re.sub(r"\s*\(.*?\)", "", a).strip().lower()


def inline_data(spot: Spot, report: Report) -> dict:
    node = spot.node
    actions = list(node.actions) if node else []
    colors = action_colors(actions)
    preflop = spot.module == "preflop"
    complete = bool(spot.data.get("hands_complete"))
    fold = next((a for a in actions if a.lower().startswith("fold")), None)

    rows: dict[str, dict] = {}
    for r in spot.hands:
        key = norm_class(r.hand) if preflop else r.hand
        if not key or not r.strategy or key in rows:
            continue
        rows[key] = {
            "s": [round(float(r.strategy.get(a, 0.0)), 1) for a in actions],
            "ev": [None if r.ev is None or a not in r.ev else round(float(r.ev[a]), 2) for a in actions] if r.ev else None,
            "evb": None if r.ev_best is None else round(float(r.ev_best), 2),
        }
    if preflop and complete and fold:
        for c in all_hand_classes():
            rows.setdefault(c, {"s": [100.0 if a == fold else 0.0 for a in actions], "ev": None, "evb": 0.0})

    borders: dict[str, str] = {}
    if preflop and node:
        shape = build_shape(node.actions, spot.hands, complete)
        for b in shape.borders:
            borders[b["worst"]] = "in"
            if b["below"]:
                borders.setdefault(b["below"], "out")

    hero = None
    if spot.hero_hand:
        key = norm_class(spot.hero_hand.hand) if preflop else spot.hero_hand.hand
        hero = key
        if key and key not in rows and spot.hero_hand.strategy:
            hh = spot.hero_hand
            rows[key] = {
                "s": [round(float(hh.strategy.get(a, 0.0)), 1) for a in actions],
                "ev": [None if not hh.ev or a not in hh.ev else round(float(hh.ev[a]), 2) for a in actions] if hh.ev else None,
                "evb": hh.ev_best,
            }

    def bar(player, facing, acts):
        acts = {a: float(v) for a, v in (acts or {}).items()}
        acts = dict(sorted(acts.items(), key=lambda kv: not kv[0].lower().startswith("fold")))  # fold first, so the break-even line reads against it
        cols = action_colors(list(acts))
        return {"player": player, "facing": facing, "parts": [[_short(a), round(v, 1), cols[a]] for a, v in acts.items() if v >= 0.05]}

    resp = spot.response
    response = bar(resp.player, resp.facing, resp.actions) if resp else None
    breakeven = None
    bet = spot.data.get("bet") or {}
    if response and bet.get("size") and bet.get("pot_before"):
        breakeven = round(100 * bet["size"] / (bet["size"] + bet["pot_before"]), 1)

    alts = []
    for alt in spot.data.get("alternatives") or []:
        steps = alt.get("steps") or []
        if steps and steps[0].get("actions"):
            s0 = steps[0]
            b = bar(s0.get("player"), alt.get("action") or s0.get("facing"), s0.get("actions"))
            b["label"] = f'{b["player"]} facing {b["facing"]}' if b["facing"] else (alt.get("line") or b["player"])
            alts.append(b)

    return {
        "title": spot.title,
        "hero": spot.hero,
        "preflop": preflop,
        "actions": [{"name": a, "short": _short(a), "pct": round(float(node.actions[a]), 1), "color": colors[a]} for a in actions],
        "tiles": [a for a in actions if float(node.actions[a]) >= 0.05],
        "rows": rows,
        "borders": borders,
        "hero_hand": hero,
        "response": response,
        "breakeven": breakeven,
        "alternatives": alts,
    }


def render_inline(spot: Spot, report: Report) -> str:
    d = inline_data(spot, report)
    payload = json.dumps(d).replace("</", "<\\/")
    tiles = "".join(
        f'<div style="background:var(--surface-1);border-radius:var(--radius);padding:10px 12px">'
        f'<div style="font-size:12px;color:var(--text-secondary);display:flex;align-items:center;gap:6px">'
        f'<span style="width:10px;height:10px;border-radius:2px;background:{a["color"]}"></span>{html.escape(a["short"])}</div>'
        f'<div style="font-size:20px;font-weight:500">{a["pct"]:.1f}%</div></div>'
        for a in d["actions"] if a["name"] in d["tiles"]
    )
    summary = html.escape(f'{d["title"]}: ' + ", ".join(f'{a["short"]} {a["pct"]:.1f}%' for a in d["actions"]))
    return _TEMPLATE.replace("__SUMMARY__", summary).replace("__TILES__", tiles).replace("__DATA__", payload)


_TEMPLATE = """<h2 class="sr-only">__SUMMARY__</h2>
<style>
.ph-g{display:grid;grid-template-columns:repeat(13,minmax(0,1fr));gap:2px}
.ph-c{aspect-ratio:1/1;border:0;padding:0;border-radius:3px;font-size:11px;line-height:1;cursor:pointer;display:flex;align-items:center;justify-content:center;font-family:var(--font-sans)}
.ph-c.sel{outline:2px solid var(--text-primary);outline-offset:1px}
.ph-bar{display:flex;height:22px;border-radius:4px;overflow:hidden;gap:2px;position:relative}
.ph-bar div{display:flex;align-items:center;padding:0 6px;font-size:11px;color:#fff;white-space:nowrap;overflow:hidden}
.ph-l{font-size:13px;color:var(--text-secondary);margin:0 0 4px}
</style>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin:0 0 14px">__TILES__</div>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;align-items:start">
<div id="ph-left"></div>
<div style="display:flex;flex-direction:column;gap:14px">
<div style="border:0.5px solid var(--border);border-radius:12px;padding:12px 14px">
<div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap"><span id="ph-hn" style="font-size:22px;font-weight:500"></span><span id="ph-hv" style="font-size:13px;color:var(--text-secondary)"></span></div>
<div class="ph-bar" id="ph-hb" style="margin:8px 0 6px"></div>
<div id="ph-he" style="font-size:13px;color:var(--text-secondary)"></div>
</div>
<div id="ph-resp"></div>
</div>
</div>
<script>
const PH=__DATA__;
const ink=c=>c==="#B4B2A9"||c==="#EF9F27"?"#2C2C2A":"#fff";
function bar(parts,line){let h=parts.map(p=>`<div style="background:${p[2]};color:${ink(p[2])};width:${p[1]}%">${p[1]>=12?p[0]+" "+p[1].toFixed(1)+"%":""}</div>`).join("");
if(line!=null)h+=`<span style="position:absolute;top:-3px;bottom:-3px;left:${line}%;width:2px;background:var(--text-primary)"></span>`;return `<div class="ph-bar">${h}</div>`}
function show(h){const r=PH.rows[h];if(!r)return;const A=PH.actions;
document.getElementById("ph-hn").textContent=h;const m=Math.max(...r.s),k=r.s.indexOf(m);
document.getElementById("ph-hv").textContent="mostly "+A[k].short+(r.evb!=null?", best EV "+(+r.evb).toFixed(2)+"bb":"")+(PH.borders[h]?" · border hand":"");
document.getElementById("ph-hb").innerHTML=r.s.map((v,i)=>v>=0.5?`<div style="background:${A[i].color};color:${ink(A[i].color)};width:${v}%">${v>=12?A[i].short+" "+Math.round(v)+"%":""}</div>`:"").join("");
let e="";if(r.ev){const ev=r.ev.map((x,i)=>x==null?null:[A[i].short,x]).filter(Boolean);ev.sort((a,b)=>b[1]-a[1]);
e="EV by action: "+ev.map(x=>x[0]+" "+x[1].toFixed(2)).join(", ")+".";if(ev.length>1&&ev[0][1]-ev[1][1]<=0.02)e+=" Near-tie: a coin-flip choice.";}
else e="Per-action EVs weren't captured for this hand.";document.getElementById("ph-he").textContent=e;
document.querySelectorAll(".ph-c").forEach(c=>c.classList.toggle("sel",c.dataset.h===h))}
const left=document.getElementById("ph-left");
if(PH.preflop){const R="AKQJT98765432",g=document.createElement("div");g.className="ph-g";
for(let i=0;i<13;i++)for(let j=0;j<13;j++){const a=R[i],b=R[j],h=i===j?a+b:i<j?a+b+"s":b+a+"o",r=PH.rows[h];
const c=document.createElement("button");c.className="ph-c";c.dataset.h=h;c.textContent=h;
if(r){const m=Math.max(...r.s),k=r.s.indexOf(m),col=PH.actions[k].color;c.style.background=col;c.style.color=ink(col);c.style.opacity=m<80?0.55:1;
c.setAttribute("aria-label",h+": "+PH.actions[k].short+" "+Math.round(m)+"%");c.onclick=()=>show(h)}
else{c.style.background="transparent";c.style.border="0.5px dashed var(--border-strong)";c.style.color="var(--text-muted)";c.setAttribute("aria-label",h+": not captured")}
g.appendChild(c)}left.appendChild(g);
const lg=document.createElement("div");lg.style.cssText="display:flex;flex-wrap:wrap;gap:12px;font-size:12px;color:var(--text-secondary);margin-top:10px";
lg.innerHTML=PH.actions.map(a=>`<span style="display:inline-flex;align-items:center;gap:5px"><span style="width:10px;height:10px;border-radius:2px;background:${a.color}"></span>${a.short}</span>`).join("")+`<span>faded = mixed</span>`;left.appendChild(lg)}
else{left.innerHTML=Object.entries(PH.rows).slice(0,14).map(([h,r])=>`<button onclick="show('${h}')" style="display:grid;grid-template-columns:70px minmax(0,1fr);gap:8px;align-items:center;width:100%;border:0;background:transparent;padding:3px 0;cursor:pointer"><span class="ph-c" data-h="${h}" style="aspect-ratio:auto;font-size:13px;color:var(--text-primary)">${h}</span>${bar(r.s.map((v,i)=>[PH.actions[i].short,v,PH.actions[i].color]).filter(p=>p[1]>=0.5))}</button>`).join("")}
let rh="";if(PH.response){rh+=`<div><div class="ph-l">${PH.response.player} facing ${PH.response.facing||"the bet"}</div>${bar(PH.response.parts,PH.breakeven!=null?PH.breakeven:null)}`;
if(PH.breakeven!=null)rh+=`<div style="font-size:12px;color:var(--text-muted);margin-top:4px">Line: a zero-equity bet needs ${PH.breakeven.toFixed(1)}% folds</div>`;rh+="</div>"}
PH.alternatives.forEach(a=>{rh+=`<div style="margin-top:12px"><div class="ph-l">${a.label}</div>${bar(a.parts)}</div>`});
document.getElementById("ph-resp").innerHTML=rh;
const first=PH.hero_hand&&PH.rows[PH.hero_hand]?PH.hero_hand:Object.keys(PH.rows)[0];if(first)show(first);
</script>"""
