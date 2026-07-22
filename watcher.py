"""Storage-unit item watcher — MVP skeleton.

Continuous webcam connection; every --interval seconds one frame is sampled
and run through pretrained YOLO (stock COCO classes, CPU). Per-class count
diffs between consecutive samples become ADDED/REMOVED events, logged to
console + logs/events.csv, with annotated snapshots saved on change.

FILL-IN WORKFLOW (see docs/mvp-plan.md for the full contract):
  Each function below has numbered pseudocode in its docstring/comments and a
  `raise NotImplementedError` stub. Implement in this order:
    1. diff_counts        (pure logic — make tests/test_events.py pass)
    2. detect_counts      (YOLO inference on one frame)
    3. log_event / save_snapshot  (output plumbing)
    4. main               (capture loop wiring it all together)
  Run `pytest` after step 1; run `python watcher.py --show` after step 4.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2  # opencv-python

# NOTE: `from ultralytics import YOLO` is deliberately NOT imported at module
# level — it drags in torch (~seconds of import time), which would slow every
# `pytest` run that imports this module. main() imports it lazily instead.


@dataclass(frozen=True)
class Event:
    """One per-class count change between two consecutive samples.

    Provided complete (data container, no logic to learn here).
    Invariant: delta == new - prev, and delta != 0 for any emitted Event.
    """

    class_name: str
    prev: int
    new: int

    @property
    def delta(self) -> int:
        return self.new - self.prev

    @property
    def kind(self) -> str:
        return "ADDED" if self.delta > 0 else "REMOVED"


def parse_args() -> argparse.Namespace:
    """Build the CLI. Flags and defaults per docs/mvp-plan.md §2.

    Pseudocode:
      1. p = argparse.ArgumentParser(description=...)
      2. p.add_argument("--interval", type=float, default=5.0)   # seconds between samples
      3. p.add_argument("--conf",     type=float, default=0.5)   # YOLO confidence threshold
      4. p.add_argument("--model",    default="yolo11n.pt")      # weights (auto-downloads)
      5. p.add_argument("--camera",   type=int, default=0)       # OpenCV camera index
      6. p.add_argument("--imgsz",    type=int, default=640)     # inference image size
      7. p.add_argument("--logdir",   default="logs")            # events.csv + snapshots/
      8. p.add_argument("--show", action="store_true")           # live preview windows
      9. return p.parse_args()
    """
    raise NotImplementedError("TODO: build argparse parser (pseudocode above)")


def detect_counts(model, frame, conf: float, imgsz: int):
    """Run YOLO ONCE on one frame -> (Counter of class-name counts, annotated frame).

    One inference must produce BOTH outputs — never run the model twice per
    sample (CPU cost doubles).

    Pseudocode:
      1. results = model(frame, conf=conf, imgsz=imgsz, verbose=False)
         # ultralytics returns a list; single image -> take results[0]
      2. r = results[0]
      3. counts = Counter()
      4. for box in r.boxes:
           cls_id = int(box.cls)          # tensor -> int
           name = r.names[cls_id]         # e.g. "bottle"
           counts[name] += 1
      5. annotated = r.plot()             # frame copy with boxes/labels drawn
      6. return counts, annotated
    """
    raise NotImplementedError("TODO: YOLO inference + per-class Counter")


def diff_counts(prev: Counter, curr: Counter) -> list[Event]:
    """PURE function: per-class deltas between two samples -> list of Events.

    The unit-tested core (tests/test_events.py). No I/O, no globals, no model.

    Rules (docs/mvp-plan.md §2 "Event semantics"):
      - Missing keys count as 0 (class appearing/vanishing needs no special case)
      - delta == 0 -> no Event for that class
      - Iterate the UNION of class names in sorted() order (deterministic)
      - One Event per changed class, magnitude in delta (e.g. -2 = two removed)

    Pseudocode:
      1. names = sorted(set(prev) | set(curr))
      2. events = []
      3. for name in names:
           p = prev.get(name, 0); c = curr.get(name, 0)
           if c != p: events.append(Event(name, p, c))
      4. return events

    Tricky bit: Counter[missing] returns 0 on its own, but sorted-union
    iteration is still needed — iterating only `curr` would miss removals.
    """
    raise NotImplementedError("TODO: implement the count diff (pseudocode above)")


def log_event(csv_path: Path, timestamp: str, event_kind: str,
              class_name: str, delta: int, prev: int, new: int) -> None:
    """Append one row to events.csv, creating it with a header first.

    Schema (docs/mvp-plan.md §2): timestamp,event,class,delta,prev_count,new_count

    Pseudocode:
      1. csv_path.parent.mkdir(parents=True, exist_ok=True)
      2. is_new = not csv_path.exists()
      3. open csv_path in append mode, newline=""   # newline="" matters on Windows
      4. w = csv.writer(f)
      5. if is_new: w.writerow(["timestamp", "event", "class", "delta",
                                "prev_count", "new_count"])
      6. w.writerow([timestamp, event_kind, class_name, delta, prev, new])
    """
    raise NotImplementedError("TODO: append CSV row (pseudocode above)")


def save_snapshot(snap_dir: Path, annotated_frame, timestamp_compact: str,
                  reason: str) -> Path:
    """Write the annotated frame as logs/snapshots/YYYYMMDD-HHMMSS_<reason>.jpg.

    reason is "baseline" or "event".

    Pseudocode:
      1. snap_dir.mkdir(parents=True, exist_ok=True)
      2. path = snap_dir / f"{timestamp_compact}_{reason}.jpg"
      3. cv2.imwrite(str(path), annotated_frame)
      4. return path
    """
    raise NotImplementedError("TODO: save annotated jpg (pseudocode above)")


def main() -> int:
    """Capture loop: continuous read, sampled detection, diff, log.

    Pseudocode (docs/mvp-plan.md §2 "Capture loop" + "Failure handling"):

      1. args = parse_args()
      2. from ultralytics import YOLO          # lazy import (see module note)
         model = YOLO(args.model)              # first run auto-downloads weights
      3. cap = cv2.VideoCapture(args.camera)
         if not cap.isOpened():
             print error naming args.camera -> return 1
      4. state:
           prev_counts = None                  # None means "no baseline yet"
           last_sample = 0.0                   # time.monotonic() of last detection
           consecutive_failures = 0
           csv_path = Path(args.logdir) / "events.csv"
           snap_dir = Path(args.logdir) / "snapshots"
      5. try / except KeyboardInterrupt / finally:
         LOOP forever:
           a. ok, frame = cap.read()           # read EVERY frame: keeps driver
                                               # buffer fresh so samples are current
           b. if not ok:
                consecutive_failures += 1; warn
                if consecutive_failures >= 30: error -> return 1  # camera gone
                continue
              else consecutive_failures = 0
           c. if args.show: cv2.imshow("live", frame); cv2.waitKey(1)
              # waitKey(1) pumps the GUI event loop — windows freeze without it
           d. if time.monotonic() - last_sample < args.interval: continue
              last_sample = time.monotonic()
           e. counts, annotated = detect_counts(model, frame, args.conf, args.imgsz)
              now = datetime.now()
              ts = now.isoformat(timespec="seconds")        # CSV timestamp
              ts_compact = now.strftime("%Y%m%d-%H%M%S")    # snapshot filename
           f. if prev_counts is None:                       # BASELINE sample
                for name in sorted(counts):
                    log_event(csv_path, ts, "BASELINE", name,
                              counts[name], 0, counts[name])
                save_snapshot(snap_dir, annotated, ts_compact, "baseline")
                print BASELINE line with counts
              else:
                events = diff_counts(prev_counts, counts)
                for ev in events:
                    log_event(csv_path, ts, ev.kind, ev.class_name,
                              ev.delta, ev.prev, ev.new)
                    print event line
                if events:
                    save_snapshot(snap_dir, annotated, ts_compact, "event")
           g. print one summary line of current counts (every sample)
           h. if args.show: cv2.imshow("detections", annotated); cv2.waitKey(1)
              # second window holds the last annotated sample, no flicker
           i. prev_counts = counts
      6. except KeyboardInterrupt: pass        # Ctrl+C = normal shutdown
      7. finally: cap.release(); cv2.destroyAllWindows()
      8. return 0
    """
    raise NotImplementedError("TODO: capture loop (pseudocode above)")


if __name__ == "__main__":
    sys.exit(main())
