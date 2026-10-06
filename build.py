#!/usr/bin/env python3
"""
Static-site builder for both sites.

    pip install jinja2 pyyaml
    python build.py            # builds dist/personal and dist/lab
    python build.py personal   # just one
    python build.py --serve    # build, then serve dist/ on http://localhost:8000

Content lives in YAML (shared/data/*.yaml, <site>/site.yaml); page layouts are
Jinja templates in <site>/pages/. All links are relative, so the output works
under a sub-path such as users.cs.utah.edu/~shankar/ as well as a domain root.
"""
import datetime, html, re, shutil, sys
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
SHARED = ROOT / "shared"
SITES = ["personal", "lab"]

TAG_LABELS = {
    "operator-learning": "Operator learning",
    "physics-informed": "Physics-informed & trustworthy ML",
    "meshless": "Kernel & meshless methods",
    "mechanics": "Mechanics & robotics",
    "biomechanics": "Biofluids & biomechanics",
    "hpc": "HPC",
    "other": "Other",
}


def load(p):
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def data():
    d = {p.stem: load(p) for p in (SHARED / "data").glob("*.yaml")}
    pubs = d["publications"]["publications"]
    group = set(d["publications"].get("group_members", []))
    for i, p in enumerate(pubs):
        p["id"] = f"p{i+1}"
        p["authors_html"] = ", ".join(fmt_author(a, group) for a in p["authors"])
    # thrust -> paper objects, thrust -> grants
    for t in d["research"]["thrusts"]:
        t["paper_objs"] = [p for pref in t.get("papers", []) for p in pubs
                           if p["title"].lower().startswith(pref.lower())]
        t["grants"] = [g for g in d["grants"]["grants"] if g.get("thrust") == t["id"] and g["status"] == "active"]
    tags = {}
    for p in pubs:
        for t in p["tags"]:
            tags[t] = tags.get(t, 0) + 1
    d["pub_tags"] = [(k, TAG_LABELS.get(k, k), tags[k]) for k in TAG_LABELS if k in tags]
    d["active_grants"] = [g for g in d["grants"]["grants"] if g["status"] == "active"]
    d["active_sponsors"] = list(dict.fromkeys(sp for g in d["active_grants"] for sp in (g.get("sponsors") or [g["sponsor"]])))
    d["past_grants"] = [g for g in d["grants"]["grants"] if g["status"] != "active"]
    d["pubs_by_year"] = group_by_year(pubs)
    return d


def fmt_author(a, group):
    s = html.escape(a)
    if a.replace("Dr. ", "") == "Varun Shankar":
        return f"<b>{s}</b>"
    if a in group:
        return f"<u>{s}</u>"
    return s


def group_by_year(pubs):
    out = []
    for p in pubs:
        key = "In review" if p["status"] == "review" else str(p["year"])
        if not out or out[-1][0] != key:
            out.append((key, []))
        out[-1][1].append(p)
    # merge duplicate "In review" buckets
    merged = {}
    order = []
    for k, v in out:
        if k not in merged:
            merged[k] = []
            order.append(k)
        merged[k].extend(v)
    return [(k, merged[k]) for k in order]


def initials(name):
    parts = [w for w in re.sub(r"^Dr\.\s*", "", name).split() if w[0].isalpha()]
    return (parts[0][0] + parts[-1][0]).upper() if parts else "?"


def build(site):
    src = ROOT / site
    out = ROOT / "dist" / site
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    cfg = load(src / "site.yaml")
    env = Environment(
        loader=FileSystemLoader([str(src / "pages"), str(SHARED / "templates")]),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True, lstrip_blocks=True,
    )
    env.filters["initials"] = initials
    def nicedate(v):
        v = str(v)
        m = re.match(r"(\d{4})-(\d{2})", v)
        return datetime.date(int(m[1]), int(m[2]), 1).strftime("%b %Y") if m else v
    env.filters["nicedate"] = nicedate
    # an image reference is only emitted if the file is actually present
    env.filters["exists"] = lambda rel: bool(rel) and ((src / "static" / rel).exists() or (SHARED / "static" / rel).exists())
    env.globals.update(site=cfg, d=data(), tag_labels=TAG_LABELS,
                       year=datetime.date.today().year,
                       built=datetime.date.today().strftime("%B %Y"))
    for tpl in sorted((src / "pages").glob("*.html")):
        if tpl.name.startswith("_"):
            continue
        html_out = env.get_template(tpl.name).render(page=tpl.stem)
        (out / tpl.name).write_text(html_out, encoding="utf-8")
    # static assets: shared first, then site-specific overrides
    for s in [SHARED / "static", src / "static"]:
        if s.exists():
            shutil.copytree(s, out, dirs_exist_ok=True)
    n = len(list(out.glob("*.html")))
    print(f"built {site}: {n} pages -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for s in (args or SITES):
        build(s)
    if "--serve" in sys.argv:
        import http.server, functools, socketserver
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT / "dist"))
        with socketserver.TCPServer(("", 8000), h) as srv:
            print("serving http://localhost:8000/personal/ and http://localhost:8000/lab/")
            srv.serve_forever()
