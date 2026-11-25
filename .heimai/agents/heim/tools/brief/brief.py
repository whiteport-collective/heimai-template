#!/usr/bin/env python3
"""Start a brief from the suite templates, and check what is still open in one.

    new   <brief-folder> [--docs 01,10,11,20,21] [--project NAME] [--person NAME] [--lang sv|en]
          [--brand-folder PATH] [--brand] [--extra "Title" --level why|what|how] [--heim DIR]
    check <brief-folder>

The suite's numbers follow decision 26: why 00-09, what 10-19, how 20-29. Folders
are found through the Heim's floor plan (../heim-floor/floor.py); templates in
<tool dir>/../../templates/brief/. Never overwrites a file. See tool.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "heim-floor"))
import floor  # noqa: E402

SUITE = {
    "01": "01-brief.md",
    "10": "10-content-language.md",
    "11": "11-visual-direction.md",
    "20": "20-platform-requirements.md",
    "21": "21-keyword-analysis.md",
}
ALWAYS = ("presentation.md", "highlights.yaml")
BRAND_FILES = {"brand-tone-of-voice.md": "tone-of-voice.md",
               "brand-visual-direction.md": "visual-identity/visual-direction.md"}
LEVELS = {"why": (0, 9), "what": (10, 19), "how": (20, 29)}
RESERVED = {"why": [0, 1], "what": [10, 11], "how": [20, 21]}   # 00-intake.md and the suite

NEEDED = re.compile(r"\[needed(?::[^\]]*)?\]")
LEGEND = re.compile(r"\[needed:\s*(…|\.\.\.)\s*\]")
NEEDED_LINE =re.compile(r"^\s*`?\[needed(?::[^\]]*)?\]`?\s*$")
PLACEHOLDER = re.compile(r"\{\{[^{}]+\}\}")
DRAFT = re.compile(r"\*\(draft[):]", re.IGNORECASE)
HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
BRAND_REF = re.compile(r"`([^`\s]*brand[^`\s]*)`|\]\(([^)\s]*brand[^)\s]*)\)", re.IGNORECASE)


def existing_ancestor(p: Path) -> Path:
    p = p.resolve()
    while not p.exists():
        p = p.parent
    return p


def load_floor(folder: Path, heim: str | None):
    try:
        return floor.load(start=existing_ancestor(folder), heim=heim)
    except floor.FloorError as e:
        print(f"Note: {e}; going on without the Heim's floor plan.")
        return None


def slugify(title: str) -> str:
    t = unicodedata.normalize("NFKD", title.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def fill(text: str, values: dict) -> str:
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def write_new(path: Path, text: str, written: list, skipped: list) -> None:
    if path.exists():
        skipped.append(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(text)
    written.append(path)


def project_name(folder: Path, f) -> str:
    """The feature: of the project the brief folder is in, else the Heim's name, else the folder above."""
    for d in [folder.parent, folder.parent.parent]:
        card = d / "feature.yaml"
        if card.is_file():
            try:
                name = floor.read_card(card)[0].get("feature")
                if name:
                    return str(name)
            except floor.FloorError:
                pass
    return f.name if f else folder.parent.name


def next_number(folder: Path, level: str, planned: list[str]) -> int:
    lo, hi = LEVELS[level]
    used = set(RESERVED[level])
    names = [p.name for p in folder.glob("*")] if folder.is_dir() else []
    for name in names + planned:
        m = re.match(r"^(\d\d)-", name)
        if m and lo <= int(m.group(1)) <= hi:
            used.add(int(m.group(1)))
    n = max(used) + 1
    if n > hi:
        raise ValueError(f"no free number left at the {level} level ({lo:02d}-{hi:02d})")
    return n


def cmd_new(a) -> int:
    folder = Path(a.folder)
    tpl = floor.templates_dir(__file__) / "brief"
    if not tpl.is_dir():
        print(f"Error: no templates at {tpl}", file=sys.stderr)
        return 2
    docs = []
    for d in (a.docs or "01").split(","):
        d = d.strip().zfill(2)
        if d not in SUITE:
            print(f"Error: no suite document {d}; choose from {', '.join(SUITE)}", file=sys.stderr)
            return 2
        docs.append(d)
    if a.extra and not a.level:
        print("Error: --extra needs --level why|what|how", file=sys.stderr)
        return 2

    f = load_floor(folder, a.heim)
    if a.brand and not f:
        print("Error: --brand needs a Heim (its name: fills the brand documents)", file=sys.stderr)
        return 2

    # the brand folder: --brand-folder, else 03-brand/ or brand/ under heimdocs, else ../03-brand/
    found = floor.brand_folder(f) if f else None
    if a.brand_folder:
        brand = Path(a.brand_folder).resolve()
    elif found:
        brand = found
    elif a.brand and f:
        brand = f.heimdocs / "03-brand"
    else:
        brand = None
    brand_rel = (Path(os.path.relpath(brand, folder.resolve())).as_posix() + "/") if brand else "../03-brand/"

    values = {
        "project": a.project or project_name(folder.resolve(), f),
        "date": dt.date.today().isoformat(),
        "person": a.person or "[needed: the person's name]",
        "lang": a.lang or (str(f.config.get("language")) if f and f.config.get("language") else "en"),
        "brand": brand_rel,
        "organization": f.name if f else "[needed: the organization]",
    }

    written, skipped = [], []
    for d in docs:
        write_new(folder / SUITE[d], fill((tpl / SUITE[d]).read_text(encoding="utf-8"), values), written, skipped)
    for name in ALWAYS:
        write_new(folder / name, fill((tpl / name).read_text(encoding="utf-8"), values), written, skipped)
    if a.extra:
        try:
            n = next_number(folder, a.level, [SUITE[d] for d in docs])
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2
        slug = slugify(a.extra)
        if not slug:
            print("Error: the --extra title has no letters or digits", file=sys.stderr)
            return 2
        body = (f"# {a.extra}\n{values['date']} · Draft, Saga with {values['person']}\n\n"
                f"[needed: what this document says]\n")
        write_new(folder / f"{n:02d}-{slug}.md", body, written, skipped)
    if a.brand:
        for src, dest in BRAND_FILES.items():
            write_new(brand / dest, fill((tpl / src).read_text(encoding="utf-8"), values), written, skipped)

    print(f"Brief folder: {folder.resolve()}")
    if f:
        print(f"Heim: {f.name} ({f.root})")
    print(f"Brand: {brand_rel}{'' if brand and brand.is_dir() else '  (does not exist yet)'}")
    show = f.rel if f else str
    for p in written:
        print(f"  wrote    {show(p)}")
    for p in skipped:
        print(f"  skipped  {show(p)}  (exists, left as it is)")
    return 0


# ---------- check ----------

def scan_doc(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    res = {"empty": [], "needed": [], "placeholders": [], "drafts": 0}
    for i, line in enumerate(lines, 1):
        if LEGEND.search(line):   # the line that explains the marks, not a mark itself
            continue
        for m in NEEDED.finditer(line):
            res["needed"].append((i, m.group(0)))
        for m in PLACEHOLDER.finditer(line):
            res["placeholders"].append((i, m.group(0)))
        res["drafts"] += len(DRAFT.findall(line))
    if path.suffix.lower() != ".md":
        return res

    # sections: a heading whose body (up to the next heading) is empty or only [needed] lines,
    # and which has no deeper heading under it
    start = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                start = j + 1
                break
    heads, fence = [], False
    for i in range(start, len(lines)):
        s = lines[i].strip()
        if s.startswith("```") or s.startswith("~~~"):
            fence = not fence
            continue
        m = None if fence else HEADING.match(lines[i])
        if m:
            heads.append((i, len(m.group(1)), m.group(2)))
    for k, (i, level, title) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        has_child = k + 1 < len(heads) and heads[k + 1][1] > level
        body = [ln for ln in lines[i + 1:end] if ln.strip() and ln.strip() not in ("---", "***")
                and not ln.strip().startswith("<!--")]
        if not has_child and all(NEEDED_LINE.match(ln) for ln in body):
            res["empty"].append((i + 1, title))
    return res


def brand_refs(folder: Path, path: Path) -> list[tuple[str, bool]]:
    """(the brand folder a 10-/11- document points to, whether it exists)."""
    out, seen = [], set()
    text = path.read_text(encoding="utf-8", errors="replace")
    for m in BRAND_REF.finditer(text):
        ref = (m.group(1) or m.group(2)).split("#")[0]
        if "{{" in ref or "://" in ref:
            continue
        parts = ref.replace("\\", "/").split("/")
        idx = next(i for i, p in enumerate(parts) if "brand" in p.lower())
        target = "/".join(parts[:idx + 1]) + "/"
        if target in seen:
            continue
        seen.add(target)
        out.append((target, (folder / target).is_dir()))
    return out


def short(s: str, n: int = 90) -> str:
    return s if len(s) <= n else s[:n - 1] + "…"


def cmd_check(a) -> int:
    folder = Path(a.folder)
    if not folder.is_dir():
        print(f"Error: {folder} is not a folder", file=sys.stderr)
        return 2
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in (".md", ".yaml", ".yml"))
    drafts_skipped = [p for p in files if ".draft-" in p.name]
    files = [p for p in files if p not in drafts_skipped]
    if not files:
        print(f"Error: no markdown or YAML documents in {folder}", file=sys.stderr)
        return 2

    print(f"Brief: {folder.resolve()}")
    totals = {"empty": 0, "needed": 0, "placeholders": 0, "drafts": 0, "brand": 0}
    for p in files:
        try:
            r = scan_doc(p)
        except OSError as e:
            print(f"Error: cannot read {p}: {e}", file=sys.stderr)
            return 2
        open_here = r["empty"] or r["needed"] or r["placeholders"]
        print(f"\n{p.name}: " + ("open" if open_here else "nothing open")
              + (f", {r['drafts']} *(draft)* marks" if r["drafts"] else ""))
        if r["empty"]:
            print("  empty sections: " + ", ".join(f"{t} (l.{i})" for i, t in r["empty"]))
        for i, t in r["needed"]:
            print(f"  l.{i:<4} {short(t)}")
        for i, t in r["placeholders"]:
            print(f"  l.{i:<4} placeholder {t}")
        for k in ("empty", "needed", "placeholders"):
            totals[k] += len(r[k])
        totals["drafts"] += r["drafts"]

    print()
    pointers = [p for p in files if re.match(r"^1[01]-", p.name) and p.suffix.lower() == ".md"]
    if not pointers:
        print("Brand: no 10- or 11- document")
    for p in pointers:
        refs = brand_refs(folder, p)
        if not refs:
            print(f"Brand: {p.name} points to no brand folder")
        for target, ok in refs:
            print(f"Brand: {p.name} -> {target} " + ("(exists)" if ok else "(MISSING)"))
            totals["brand"] += 0 if ok else 1
    if drafts_skipped:
        print(f"Skipped personal drafts: {', '.join(p.name for p in drafts_skipped)}")

    is_open = totals["empty"] or totals["needed"] or totals["placeholders"] or totals["brand"]
    print(f"\n{len(files)} documents: {totals['empty']} empty sections, {totals['needed']} [needed] markers, "
          f"{totals['placeholders']} placeholders, {totals['drafts']} draft marks, "
          f"{totals['brand']} missing brand folders. " + ("Open." if is_open else "Nothing open."))
    return 1 if is_open else 0


def main() -> int:
    floor.utf8_stdout()
    ap = argparse.ArgumentParser(description="Start a brief from the templates, or check what is open (see tool.md).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new", help="write suite documents into a brief folder, never overwriting")
    n.add_argument("folder")
    n.add_argument("--docs", help="comma-separated suite numbers: 01,10,11,20,21 (default 01)")
    n.add_argument("--project")
    n.add_argument("--person")
    n.add_argument("--lang")
    n.add_argument("--brand-folder", help="the brand folder, if not 03-brand/ or brand/ under heimdocs")
    n.add_argument("--brand", action="store_true", help="also write the brand's tone of voice and visual direction")
    n.add_argument("--extra", help="an extra document's title")
    n.add_argument("--level", choices=list(LEVELS), help="the extra document's level")
    n.add_argument("--heim")
    c = sub.add_parser("check", help="list empty sections, [needed] markers, placeholders and draft marks")
    c.add_argument("folder")
    a = ap.parse_args()
    try:
        return cmd_new(a) if a.cmd == "new" else cmd_check(a)
    except (OSError, floor.FloorError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
