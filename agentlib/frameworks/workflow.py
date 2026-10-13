"""Run library workflows as a tracked review folder.

    python -m agentlib workflow list
    python -m agentlib workflow show secure-software-delivery
    python -m agentlib workflow init secure-software-delivery --dir reviews/ssd-2026-10-13 \
        --input system-description=docs/system.md
    python -m agentlib workflow status reviews/ssd-2026-10-13
    python -m agentlib workflow gate reviews/ssd-2026-10-13 scope --result pass --by "J. Smith" --note "L2 agreed"

``init`` writes ``state.json`` (the workflow definition, inputs and gate records), a ``PLAN.md`` with
every stage, its agent, skills, tools and gate criteria, and one stub file per artefact (outputs with a
template start from the template). ``status`` reports which artefacts are still stubs and which gates are
recorded, and names the next actionable stage. ``gate`` records a gate decision but refuses while the
stage's artefacts are stubs or an earlier stage has not passed its gate. Gate records are evidence of
*who decided*, not a substitute for the decision.
"""
from __future__ import annotations

import datetime as _dt
import json
import shutil
import sys
from pathlib import Path

import yaml

from agentlib.paths import repo_root

STUB_MARK = "<!-- agentlib:stub -->"
STATE = "state.json"
RESULTS = ("pass", "fail", "waived")


class WorkflowError(ValueError):
    pass


def load_workflow(wid: str, root: Path | None = None) -> dict:
    root = root or repo_root()
    path = root / "workflows" / f"{wid}.yaml"
    if not path.is_file():
        known = sorted(p.stem for p in (root / "workflows").glob("*.yaml"))
        raise WorkflowError(f"unknown workflow '{wid}'; known: {', '.join(known)}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _artefact_file(name: str) -> str:
    return f"{name}.md"


def _stub(title: str, stage: dict | None, wf: dict) -> str:
    who = f"Produced by stage `{stage['id']}` ({stage['agent']}); skills: {', '.join(stage['skills']) or '-'}." if stage else "Workflow input."
    return f"# {title}\n\n{STUB_MARK}\n\n{who}\nWorkflow: `{wf['id']}` v{wf['version']}. Replace this stub with the artefact.\n"


def plan_markdown(wf: dict) -> str:
    lines = [f"# {wf['title']}", "", wf["description"].strip(), "",
             f"Workflow `{wf['id']}` v{wf['version']}. Sources: {', '.join(wf.get('sources', [])) or '-'}.", "",
             "## Inputs", ""]
    for io in wf.get("inputs", []):
        lines.append(f"- `{io['name']}`{' (required)' if io.get('required') else ''}: {io['description']}")
    lines += ["", "## Stages", ""]
    for n, st in enumerate(wf["stages"], 1):
        lines += [f"### {n}. {st['title']} (`{st['id']}`)", "",
                  f"- Agent: `{st['agent']}`; skills: {', '.join(f'`{s}`' for s in st['skills']) or '-'}",
                  f"- Consumes: {', '.join(st.get('consumes', [])) or '-'}",
                  f"- Produces: {', '.join(st['produces'])}"]
        if st.get("tools"):
            lines.append(f"- Tools: {'; '.join(f'`{t}`' for t in st['tools'])}")
        if st.get("instructions"):
            lines.append(f"- Instructions: {' '.join(st['instructions'].split())}")
        lines.append(f"- Gate ({st['gate']['decision']}):")
        lines += [f"  - [ ] {c}" for c in st["gate"]["criteria"]]
        if st["gate"].get("check"):
            lines.append(f"  - Check: `{st['gate']['check']}`")
        lines.append("")
    lines += ["## Outputs", ""] + [f"- `{o['name']}`: {o['description']}" for o in wf.get("outputs", [])]
    return "\n".join(lines) + "\n"


def init(wid: str, directory: Path, inputs: dict[str, str] | None = None, root: Path | None = None) -> list[str]:
    root = root or repo_root()
    wf = load_workflow(wid, root)
    directory = Path(directory)
    if (directory / STATE).exists():
        raise WorkflowError(f"{directory} already contains a workflow ({STATE}); use status")
    inputs = inputs or {}
    declared = {i["name"] for i in wf.get("inputs", [])}
    unknown = set(inputs) - declared
    if unknown:
        raise WorkflowError(f"unknown input(s) {sorted(unknown)}; declared: {sorted(declared)}")
    directory.mkdir(parents=True, exist_ok=True)
    created = []
    templates = {o["name"]: o.get("template") for o in wf.get("outputs", []) if o.get("template")}
    for st in wf["stages"]:
        for art in st["produces"]:
            target = directory / _artefact_file(art)
            if target.exists():
                continue
            if art in templates and (root / templates[art]).is_file():
                body = (root / templates[art]).read_text(encoding="utf-8")
                target.write_text(f"{STUB_MARK}\n\n{body}", encoding="utf-8")
            else:
                target.write_text(_stub(art, st, wf), encoding="utf-8")
            created.append(target.name)
    (directory / "PLAN.md").write_text(plan_markdown(wf), encoding="utf-8")
    created.append("PLAN.md")
    missing_required = sorted(i["name"] for i in wf.get("inputs", []) if i.get("required") and i["name"] not in inputs)
    state = {"workflow": wf, "created": _dt.date.today().isoformat(), "inputs": inputs,
             "missing_required_inputs": missing_required, "gates": {}}
    (directory / STATE).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    created.append(STATE)
    return created


def _load_state(directory: Path) -> dict:
    path = Path(directory) / STATE
    if not path.is_file():
        raise WorkflowError(f"{directory} is not a workflow folder (no {STATE}); run `workflow init`")
    return json.loads(path.read_text(encoding="utf-8"))


def _is_stub(path: Path) -> bool:
    return not path.is_file() or STUB_MARK in path.read_text(encoding="utf-8")


def status(directory: Path) -> dict:
    directory = Path(directory)
    state = _load_state(directory)
    wf = state["workflow"]
    stages, next_stage, blocked = [], None, False
    for st in wf["stages"]:
        stubs = [a for a in st["produces"] if _is_stub(directory / _artefact_file(a))]
        gate = state["gates"].get(st["id"])
        passed = bool(gate) and gate["result"] in ("pass", "waived")
        stages.append({"id": st["id"], "title": st["title"], "agent": st["agent"], "pending_artefacts": stubs,
                       "gate": gate, "done": passed and not stubs})
        if next_stage is None and not (passed and not stubs):
            next_stage = st["id"]
            blocked = bool(gate) and gate["result"] == "fail"
    inputs_missing = [i for i in state.get("missing_required_inputs", []) if i not in state["inputs"]]
    return {"workflow": wf["id"], "stages": stages, "next_stage": next_stage, "blocked_by_failed_gate": blocked,
            "missing_required_inputs": inputs_missing, "complete": next_stage is None}


def record_gate(directory: Path, stage_id: str, result: str, by: str, note: str = "") -> dict:
    directory = Path(directory)
    state = _load_state(directory)
    wf = state["workflow"]
    ids = [s["id"] for s in wf["stages"]]
    if stage_id not in ids:
        raise WorkflowError(f"unknown stage '{stage_id}'; stages: {', '.join(ids)}")
    if result not in RESULTS:
        raise WorkflowError(f"result must be one of {RESULTS}")
    if not by.strip():
        raise WorkflowError("--by (the accountable decision-maker) is required")
    idx = ids.index(stage_id)
    for prev in wf["stages"][:idx]:
        g = state["gates"].get(prev["id"])
        if not g or g["result"] not in ("pass", "waived"):
            raise WorkflowError(f"earlier stage '{prev['id']}' has not passed its gate")
    stage = wf["stages"][idx]
    stubs = [a for a in stage["produces"] if _is_stub(directory / _artefact_file(a))]
    if stubs and result == "pass":
        raise WorkflowError(f"cannot pass '{stage_id}': artefacts still stubs: {', '.join(stubs)}")
    if result == "waived" and not note.strip():
        raise WorkflowError("a waived gate needs --note with the justification")
    state["gates"][stage_id] = {"result": result, "by": by, "note": note, "decision_type": stage["gate"]["decision"],
                                "date": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
                                "criteria": stage["gate"]["criteria"]}
    (directory / STATE).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return state["gates"][stage_id]


# ------------------------------------------------------------------ CLI
def _cmd_list(args) -> int:
    root = repo_root()
    for p in sorted((root / "workflows").glob("*.yaml")):
        wf = yaml.safe_load(p.read_text(encoding="utf-8"))
        print(f"{wf['id']:34} {len(wf['stages'])} stages  {wf['title']}")
    return 0


def _cmd_show(args) -> int:
    print(plan_markdown(load_workflow(args.id)))
    return 0


def _cmd_init(args) -> int:
    inputs = {}
    for item in args.input or []:
        if "=" not in item:
            raise WorkflowError(f"--input expects name=path, got '{item}'")
        k, v = item.split("=", 1)
        inputs[k] = v
    directory = Path(args.dir or f"reviews/{args.id}-{_dt.date.today().isoformat()}")
    created = init(args.id, directory, inputs)
    print(f"Initialised {args.id} in {directory}: {len(created)} files ({', '.join(created)})")
    st = status(directory)
    if st["missing_required_inputs"]:
        print(f"Missing required inputs: {', '.join(st['missing_required_inputs'])}")
    print(f"Next stage: {st['next_stage']}")
    return 0


def _cmd_status(args) -> int:
    st = status(Path(args.dir))
    if args.format == "json":
        print(json.dumps(st, indent=2))
    else:
        print(f"Workflow {st['workflow']}: {'COMPLETE' if st['complete'] else 'in progress'}")
        if st["missing_required_inputs"]:
            print(f"  missing required inputs: {', '.join(st['missing_required_inputs'])}")
        for s in st["stages"]:
            gate = s["gate"]["result"] + " by " + s["gate"]["by"] if s["gate"] else "not recorded"
            mark = "x" if s["done"] else " "
            pend = f"; stubs: {', '.join(s['pending_artefacts'])}" if s["pending_artefacts"] else ""
            print(f"  [{mark}] {s['id']:22} agent={s['agent']:30} gate={gate}{pend}")
        if not st["complete"]:
            print(f"Next: {st['next_stage']}{' (BLOCKED: gate failed)' if st['blocked_by_failed_gate'] else ''}")
    return 0 if st["complete"] else 3


def _cmd_gate(args) -> int:
    g = record_gate(Path(args.dir), args.stage, args.result, args.by, args.note or "")
    print(f"Recorded gate {args.stage}: {g['result']} by {g['by']} at {g['date']}")
    return 0


def _wrap(fn):
    def run(args):
        try:
            return fn(args)
        except WorkflowError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    return run


def register(sub) -> None:
    p = sub.add_parser("workflow", help="scaffold, track and gate library workflows in a review folder")
    s = p.add_subparsers(dest="workflow_cmd", required=True)
    s.add_parser("list", help="list workflows").set_defaults(func=_wrap(_cmd_list))
    sh = s.add_parser("show", help="print a workflow plan")
    sh.add_argument("id")
    sh.set_defaults(func=_wrap(_cmd_show))
    i = s.add_parser("init", help="create a review folder with plan, state and artefact stubs")
    i.add_argument("id")
    i.add_argument("--dir", help="folder (default reviews/<id>-<date>)")
    i.add_argument("--input", action="append", help="name=path for a workflow input (repeatable)")
    i.set_defaults(func=_wrap(_cmd_init))
    st = s.add_parser("status", help="report progress; exit 0 when complete, 3 when in progress")
    st.add_argument("dir")
    st.add_argument("--format", choices=["text", "json"], default="text")
    st.set_defaults(func=_wrap(_cmd_status))
    g = s.add_parser("gate", help="record a gate decision for a stage")
    g.add_argument("dir")
    g.add_argument("stage")
    g.add_argument("--result", required=True, choices=RESULTS)
    g.add_argument("--by", required=True, help="accountable decision-maker (person or role)")
    g.add_argument("--note")
    g.set_defaults(func=_wrap(_cmd_gate))
