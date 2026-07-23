"""Storage-unit item watcher — MVP skeleton.

Continuous webcam connection; every --interval seconds one frame is sampled
and run through pretrained YOLO (stock COCO classes, CPU). Per-class count
diffs between consecutive samples become ADDED/REMOVED events, logged to
console + logs/events.csv, with annotated snapshots saved on change.
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
    """Build the CLI. Flags and defaults per docs/mvp-plan.md §2."""

    p = argparse.ArgumentParser(description="This Script provides all the Flags for the program.")
    p.add_argument("--interval", type=float, default=5.0)
    p.add_argument("--conf", type=float, default=0.5)
    p.add_argument("--model", default="yolo11n.pt")
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--logdir", default="logs")
    p.add_argument("--show", action="store_true")
    return p.parse_args()



def detect_counts(model, frame, conf: float, imgsz: int):
    """Run YOLO ONCE on one frame -> (Counter of class-name counts, annotated frame).

    One inference must produce BOTH outputs — never run the model twice per
    sample (CPU cost doubles).
    """
    results = model(frame, conf=conf, imgsz=imgsz, verbose=False)
    r = results[0]
    counts = Counter()
    for box in r.boxes:
        cls_id = int(box.cls)
        name = r.names[cls_id]
        counts[name] += 1
    annotated = r.plot()
    return counts, annotated


def diff_counts(prev: Counter, curr: Counter) -> list[Event]:
    """PURE function: per-class deltas between two samples -> list of Events."""
    names = sorted(set(prev) | set(curr))
    events = []
    for name in names:
        p = prev.get(name, 0)
        c = curr.get(name, 0)
        if c != p:
            events.append(Event(name, p, c))
    return events


def log_event(csv_path: Path, timestamp: str, event_kind: str,
              class_name: str, delta: int, prev: int, new: int) -> None:
    """Append one row to events.csv, creating it with a header first."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not csv_path.exists()
    with open(csv_path, mode='a', newline="") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["timestamp", "event", "class", "delta", "prev_count", "new_count"])
        w.writerow([timestamp, event_kind, class_name, delta, prev, new])


def save_snapshot(snap_dir: Path, annotated_frame, timestamp_compact: str,
                  reason: str) -> Path:
    """Write the annotated frame as logs/snapshots/YYYYMMDD-HHMMSS_<reason>.jpg."""
    snap_dir.mkdir(parents=True, exist_ok=True)
    path = snap_dir / f"{timestamp_compact}_{reason}.jpg"
    cv2.imwrite(str(path), annotated_frame)
    return path


def poll_quit() -> bool:
    """Pump the GUI event queue for one tick; report whether 'q' was pressed."""
    return cv2.waitKey(1) & 0xFF == ord('q')


def handle_sample(prev_counts: Counter | None, counts: Counter, csv_path: Path,
                   snap_dir: Path, annotated, ts: str, ts_compact: str) -> None:
    """Log a BASELINE row (first sample) or diff'd event rows (later samples)."""
    if prev_counts is None:
        for name in sorted(counts):
            log_event(csv_path, ts, "BASELINE", name, counts[name], 0, counts[name])
        save_snapshot(snap_dir, annotated, ts_compact, "baseline")
        print(f"BASELINE {dict(counts)}")
    else:
        events = diff_counts(prev_counts, counts)
        for ev in events:
            log_event(csv_path, ts, ev.kind, ev.class_name, ev.delta, ev.prev, ev.new)
            print(f"{ev.kind} {ev.class_name} ({ev.delta:+d})")
        if events:
            save_snapshot(snap_dir, annotated, ts_compact, "event")


def main() -> int:
    """Capture loop: continuous read, sampled detection, diff, log."""
    args = parse_args()
    from ultralytics import YOLO
    model = YOLO(args.model)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"Error: could not open camera {args.camera}")
        return 1

    prev_counts = None                  # None means "no baseline yet"
    last_sample = 0.0                   # time.monotonic() of last detection
    consecutive_failures = 0
    csv_path = Path(args.logdir) / "events.csv"
    snap_dir = Path(args.logdir) / "snapshots"

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                consecutive_failures += 1
                print(f"Warning: frame read failed ({consecutive_failures}/30)")
                if consecutive_failures >= 30:
                    print("Error: camera stopped responding")
                    return 1
                continue
            else:
                consecutive_failures = 0

            if args.show:
                cv2.imshow("live", frame)
                if poll_quit():
                    break
            if time.monotonic() - last_sample < args.interval:
                continue
            last_sample = time.monotonic()

            counts, annotated = detect_counts(model, frame, args.conf, args.imgsz)
            now = datetime.now()
            ts = now.isoformat(timespec="seconds")
            ts_compact = now.strftime("%Y%m%d-%H%M%S")

            handle_sample(prev_counts, counts, csv_path, snap_dir, annotated, ts, ts_compact)
            print(dict(counts))

            if args.show:
                cv2.imshow("detections", annotated)
                if poll_quit():
                    break
            prev_counts = counts

    finally:
        cap.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    sys.exit(main())
