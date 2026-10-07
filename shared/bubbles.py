"""Deterministic packed-bubble layout -> inline SVG (no dependencies).

Bubbles are seeded on rays by group (so each group forms a cluster around the
central core bubble), then relaxed: overlaps are pushed apart while everything is
pulled gently toward its group's anchor. The result is scaled into a fixed viewBox.
"""
import html, math

W = 720  # viewBox width (height computed)
PAD = 3  # gap between bubbles (viewBox units)


def layout(areas):
    groups = areas["groups"]
    gi = {g["id"]: k for k, g in enumerate(groups)}
    nodes = []
    core_r = 64.0
    nodes.append(dict(x=0.0, y=0.0, r=core_r, label=areas.get("core", ""), group=None, fixed=True))
    for b in areas["bubbles"]:
        nodes.append(dict(r=18.0 * math.sqrt(float(b.get("size", 4))), label=b["label"], group=b["group"], fixed=False))
    G = len(groups)
    # anchors: groups evenly spaced on a ring (ellipse, wider than tall)
    anchors = {}
    for g in groups:
        a = -math.pi / 2 + 2 * math.pi * gi[g["id"]] / G
        anchors[g["id"]] = (math.cos(a) * 200, math.sin(a) * 150)
    # seed: within a group, biggest first, spiral out from the anchor
    counts = {}
    for n in sorted(nodes[1:], key=lambda n: -n["r"]):
        k = counts.get(n["group"], 0); counts[n["group"]] = k + 1
        ax, ay = anchors[n["group"]]
        t = 1.3 * k
        n["x"] = ax + 22 * math.sqrt(k) * math.cos(t)
        n["y"] = ay + 22 * math.sqrt(k) * math.sin(t)
    # relax
    for it in range(1600):
        pull = 0.012 if it < 1200 else 0.004
        for n in nodes:
            if n["fixed"]:
                continue
            ax, ay = anchors[n["group"]]
            # pull toward own group anchor and, more weakly, toward the core
            n["x"] += (ax * 0.6 - n["x"]) * pull - n["x"] * pull * 0.5
            n["y"] += (ay * 0.6 - n["y"]) * pull * 1.3 - n["y"] * pull * 0.9
        for i in range(len(nodes)):
            a = nodes[i]
            for j in range(i + 1, len(nodes)):
                b = nodes[j]
                dx, dy = b["x"] - a["x"], b["y"] - a["y"]
                d = math.hypot(dx, dy) or 1e-6
                need = a["r"] + b["r"] + PAD
                if d < need:
                    push = (need - d) / d * 0.5
                    if a["fixed"]:
                        b["x"] += dx * push * 2; b["y"] += dy * push * 2
                    elif b["fixed"]:
                        a["x"] -= dx * push * 2; a["y"] -= dy * push * 2
                    else:
                        a["x"] -= dx * push; a["y"] -= dy * push
                        b["x"] += dx * push; b["y"] += dy * push
    # fit
    minx = min(n["x"] - n["r"] for n in nodes); maxx = max(n["x"] + n["r"] for n in nodes)
    miny = min(n["y"] - n["r"] for n in nodes); maxy = max(n["y"] + n["r"] for n in nodes)
    s = (W - 8) / (maxx - minx)
    H = (maxy - miny) * s + 8
    for n in nodes:
        n["x"] = (n["x"] - minx) * s + 4
        n["y"] = (n["y"] - miny) * s + 4
        n["r"] *= s
    return nodes, H


def svg(areas):
    nodes, H = layout(areas)
    colors = {g["id"]: g["color"] for g in areas["groups"]}
    out = [f'<svg class="bubbles" viewBox="0 0 {W} {H:.0f}" role="img" aria-labelledby="bub-title">',
           '<title id="bub-title">Research areas: ' + html.escape(", ".join(b["label"].replace("\n", " ") for b in areas["bubbles"])) + "</title>"]
    for n in nodes:
        lines = n["label"].split("\n")
        longest = max(len(l) for l in lines) or 1
        # font size: fit the longest line across ~1.7r, and the block of lines within ~1.3r
        fit = min(2 * n["r"] * 0.82 / (0.56 * longest), 1.3 * n["r"] / (1.16 * len(lines)))
        fs = min(fit, 0.30 * n["r"] + 6, 30 if n["fixed"] else 20)
        fs = max(fs, 11)
        cls = "core" if n["fixed"] else "b"
        style = "" if n["fixed"] else f' style="--c:{colors[n["group"]]}"'
        out.append(f'<g class="{cls}"{style}><circle cx="{n["x"]:.1f}" cy="{n["y"]:.1f}" r="{n["r"]:.1f}"/>')
        y0 = n["y"] - (len(lines) - 1) * fs * 0.58 + fs * 0.35
        out.append(f'<text x="{n["x"]:.1f}" font-size="{fs:.1f}">' + "".join(
            f'<tspan x="{n["x"]:.1f}" y="{y0 + i * fs * 1.16:.1f}">{html.escape(l)}</tspan>' for i, l in enumerate(lines)) + "</text></g>")
    out.append("</svg>")
    legend = '<ul class="bubbles-legend">' + "".join(
        f'<li><i style="background:{g["color"]}"></i>{html.escape(g["label"])}</li>' for g in areas["groups"]) + "</ul>"
    lst = '<div class="bubbles-list">' + "".join(
        f'<div><h4><i style="background:{g["color"]}"></i>{html.escape(g["label"])}</h4><ul>' +
        "".join(f'<li>{html.escape(b["label"].replace(chr(10), " ").replace("- ", "-"))}</li>' for b in areas["bubbles"] if b["group"] == g["id"]) +
        "</ul></div>" for g in areas["groups"]) + "</div>"
    return "\n".join(out) + legend + lst
