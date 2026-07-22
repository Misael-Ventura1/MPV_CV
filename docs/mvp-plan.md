# Storage Unit CV — MVP (Part A) Implementation Plan

## Context

Building the MVP from `storage_unit_cv_plan (1).md` (in Downloads): a CV system
that watches a storage unit via a **continuous webcam connection**, samples a
frame every N seconds, runs **pretrained YOLO** (stock COCO classes, CPU-only),
and emits **add/remove events from per-class count diffs** between consecutive
snapshots. Due **Thursday evening (2026-07-23)** together with a **flow
diagram** and a **PowerPoint deck** for the user's manager.

Part B (custom training, motion triggering, robustness, tracking) is explicitly
out of scope. Working mode for Part A: write working code directly; after each
piece works, explain what it does, why this approach, and the key parameters.

User decisions from brainstorming:
- **Video source:** built-in/USB webcam (`cv2.VideoCapture(0)`)
- **Deck:** PowerPoint `.pptx`, generated with `python-pptx`
- **Diagram:** build fresh; drawn as **native pptx shapes** (editable in
  PowerPoint, no mermaid-cli/Node dependency) + Mermaid source kept in docs
- Repo `C:\Users\vmisa\Desktop\CV_Tracking\MV-CV` is empty (git init done, no commits)

## Environment (settled)

- **Python 3.12** venv: `py -3.12 -m venv .venv` (3.14 is the default install
  but torch/ultralytics wheel support is safest on 3.12; both are present)
- Deps: `ultralytics` (pulls CPU torch + torchvision on Windows PyPI),
  `opencv-python`, `python-pptx`; dev: `pytest`
- Model: **YOLO11n** (`yolo11n.pt`, auto-downloads ~5.4 MB on first run).
  CPU inference ~100–300 ms per 640 px frame — trivial at 5 s intervals.

## Repo layout

```
MV-CV/
  .gitignore              # .venv, logs/, *.pt, __pycache__
  requirements.txt
  README.md               # setup + run instructions, Mermaid flow diagram
  watcher.py              # the MVP script (single file, deliberate)
  tests/test_events.py    # unit tests for the count-diff logic only
  deck/build_deck.py      # generates presentation.pptx
  deck/presentation.pptx  # generated output (committed)
  docs/mvp-plan.md        # copy of this approved plan, for the repo record
  logs/                   # runtime output (gitignored): events.csv, snapshots/
```

Single-file `watcher.py` (not a package): fastest to build, and easiest to walk
through function-by-function in the presentation. Functions keep boundaries
clean: `parse_args`, `sample_frames` (capture), `detect_counts` (YOLO),
`diff_counts` (events), `log_event` / `save_snapshot` (output), `main` loop.

## watcher.py behavior

1. **Capture** — open webcam once and keep the connection; `read()` frames
   continuously in a loop (cheap on CPU, keeps the buffer fresh so samples are
   current), but only hand a frame to detection when `--interval` seconds
   (default 5) have elapsed. This matches the plan's "continuous video
   connection, detection on sampled frames" requirement.
2. **Detect** — `model(frame, conf=0.5, imgsz=640, verbose=False)`; aggregate
   to a `Counter` of class-name → count. `--conf` and `--model` are CLI flags.
3. **Events** — first snapshot logs a BASELINE (no events). Then per class:
   count up → `ADDED xN`, count down → `REMOVED xN`. Pure function, unit-tested.
4. **Output** — every sample: console line with current counts. Every event:
   console line + append to `logs/events.csv`
   (`timestamp,event,class,delta,prev_count,new_count`) + save the annotated
   frame (boxes drawn) to `logs/snapshots/` — these become the deck screenshots.
5. Clean Ctrl+C shutdown; `--show` flag for a live preview window (handy while
   staging the demo, off by default).

Known limitations to state honestly (in deck, README): COCO has **no "box"
class** — nearest stand-ins are suitcase/handbag/backpack; good demo objects
that COCO detects well: bottle, cup, book, backpack, laptop, teddy bear,
scissors, vase. Count-diff can't see equal-count swaps; a single flickered
detection produces a false event (hysteresis is Part B); lighting untested.

## Flow diagram (content)

Webcam (continuous) → frame buffer → [every N s] sample frame → YOLO11n (CPU,
stock COCO) → per-class counts → diff vs previous counts → no change → wait /
change → ADDED/REMOVED events → console + events.csv + annotated snapshot.
Drawn as native shapes on a deck slide; same diagram as Mermaid in README.

## Deck outline (build_deck.py)

1. Title — Storage Unit Item Detection: MVP
2. The problem — watch unit, know what's there, detect add/remove
3. MVP architecture — the flow diagram (native shapes)
4. Key design choices — CPU-only → sampled frames not full-rate video; stock
   YOLO stand-in classes (explicitly named); count-diff not tracking
5. Demo — annotated snapshots + events.csv excerpt from a real staged run
   (script tolerates missing screenshots with placeholders so the deck always builds)
6. Known limitations — stand-in classes, flicker false-events, lighting untested, swaps invisible
7. Roadmap — Part B phases 1–6, one line each
8. Next steps / ask

## Build order (Thursday)

1. Scaffold: `.gitignore`, `requirements.txt`, venv, install deps (torch is a
   ~200 MB download — kick off first), copy this plan to `docs/mvp-plan.md`, first commit
2. `watcher.py` + `tests/test_events.py` (diff logic test-first; it's a pure function)
3. Live smoke test with webcam; adjust `--conf` if detections flicker
4. Staged demo run: add/remove 2–3 known-good objects; collect events.csv + snapshots
5. `deck/build_deck.py` → presentation.pptx with real screenshots
6. README (setup, usage, Mermaid diagram, limitations)
7. Explanations after each working piece (per Part A working mode); commit at each milestone

## Verification

- `pytest` green on the diff-logic tests
- Live run: stage bottle/cup/backpack add+remove → console shows BASELINE then
  ADDED/REMOVED lines; `logs/events.csv` rows match; annotated snapshots saved
- `python deck/build_deck.py` produces `presentation.pptx` that opens in
  PowerPoint with diagram + real screenshots
- README steps reproduce from a clean clone (venv → install → run)
