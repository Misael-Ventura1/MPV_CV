"""Storage-unit item watcher — MVP skeleton.

Continuous webcam connection; every --interval seconds one frame is sampled
and run through pretrained YOLO (stock COCO classes, CPU). Per-class count
diffs between consecutive samples become ADDED/REMOVED events, logged to
console + logs/events.csv, with annotated snapshots saved on change.
"""

from __future__ import annotations
from ultralytics import YOLO
import argparse
import csv
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2 
import yaml


@dataclass(frozen=True)
class Event:
    class_name: str
    prev: int
    new: int

    @property
    def delta(self):
        return self.new - self.prev

    @property
    def kind(self):
        return "ADDED" if self.delta > 0 else "REMOVED"

def load_config(path: Path):
    
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def parse_args():

    config_p = argparse.ArgumentParser(add_help=False)
    config_p.add_argument("--config", default="base.yaml", help="YAML file of default flag values")
    config_args, _ = config_p.parse_known_args()

    p = argparse.ArgumentParser(
        description="Base.yaml provides all the Flags for the program. User can override.",
        parents=[config_p],
    )
    p.add_argument("--interval", type=float, default=5.0)
    p.add_argument("--conf", type=float, default=0.5)
    p.add_argument("--model", default="yolo11n.pt")
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--logdir", default="logs")
    p.add_argument("--show", action="store_true")
    p.set_defaults(**load_config(Path(config_args.config)))
    return p.parse_args()



def detect_objects(model, frame, conf: float, imgsz: int):

    results = model(frame, conf=conf, imgsz=imgsz, verbose=False)
    r = results[0]
    counts = Counter()
    for box in r.boxes:            
        cls_id = int(box.cls)      
        name = r.names[cls_id]     
        counts[name] += 1
    annotated = r.plot()       
    return counts, annotated


def diff_counts(prev: Counter, curr: Counter):
    names = sorted(set(prev) | set(curr))
    events = []
    for name in names:
        p = prev.get(name, 0)
        c = curr.get(name, 0)
        if c != p:
            events.append(Event(name, p, c))
    return events


def log_event(csv_path: Path, timestamp: str, event_kind: str, class_name: str, delta: int, prev: int, new: int):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not csv_path.exists()
    with open(csv_path, mode='a', newline="") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["timestamp", "event", "class", "delta", "prev_count", "new_count"])
        w.writerow([timestamp, event_kind, class_name, delta, prev, new])


def save_snapshot(snap_dir: Path, annotated_frame, timestamp_compact: str, reason: str):
    snap_dir.mkdir(parents=True, exist_ok=True)
    path = snap_dir / f"{timestamp_compact}_{reason}.jpg"
    cv2.imwrite(str(path), annotated_frame)
    return path


def show_frame(window: str, frame) -> bool:
    cv2.imshow(window, frame)
    return cv2.waitKey(1) & 0xFF == ord('q')


def record_sample(prev_counts: Counter | None, counts: Counter, csv_path: Path, snap_dir: Path, annotated, ts: str, ts_compact: str):
    if prev_counts is None:
        for name in sorted(counts):
            log_event(csv_path, ts, "BASELINE", name, counts[name], 0, counts[name])
        save_snapshot(snap_dir, annotated, ts_compact, "baseline")
        print(f"BASELINE {dict(counts)}")
    else:
        events = diff_counts(prev_counts, counts)
        for event in events:
            log_event(csv_path, ts, event.kind, event.class_name, event.delta, event.prev, event.new)
            print(f"{event.kind} {event.class_name} ({event.delta:+d})")
        if events:
            save_snapshot(snap_dir, annotated, ts_compact, "event")


def main():
    args = parse_args()
    model = YOLO(args.model)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print("could not open camera", args.camera)
        return 1
    print("running, press 'q' in a window to quit")

    csv_path = Path(args.logdir) / "events.csv"
    snap_dir = Path(args.logdir) / "snapshots"
    prev_counts = None
    last_sample = 0.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("lost camera connection")
                break

            if args.show and show_frame("live", frame):
                break
    
            if time.monotonic() - last_sample < args.interval:
                continue
            last_sample = time.monotonic()

            counts, annotated = detect_objects(model, frame, args.conf, args.imgsz)
            now = datetime.now()
            record_sample(prev_counts, counts, csv_path, snap_dir, annotated,
                          now.isoformat(timespec="seconds"), now.strftime("%Y%m%d-%H%M%S"))
            print(dict(counts))
            prev_counts = counts

            if args.show and show_frame("detections", annotated):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    sys.exit(main())
