from __future__ import annotations
from ultralytics import YOLO
import argparse
import csv
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import cv2
import yaml

def load_config(path):
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def parse_args():
    config_p = argparse.ArgumentParser(add_help=False)
    config_p.add_argument("--config", default="base.yaml")
    config_args, _ = config_p.parse_known_args()

    p = argparse.ArgumentParser(parents=[config_p])
    p.add_argument("--interval", type=float, default=5.0)
    p.add_argument("--conf", type=float, default=0.5)
    p.add_argument("--model", default="yolo11n.pt")
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--logdir", default="logs")
    p.add_argument("--show", action="store_true")
    p.set_defaults(**load_config(Path(config_args.config)))
    return p.parse_args()


def detect_objects(model, frame, conf, imgsz):
    results = model(frame, conf=conf, imgsz=imgsz, verbose=False)
    r = results[0]
    counts = Counter()
    for box in r.boxes:
        cls_id = int(box.cls)
        name = r.names[cls_id]
        counts[name] += 1
    annotated = r.plot()
    return counts, annotated


def diff_counts(prev, curr):
    names = sorted(set(prev) | set(curr))
    events = []
    for name in names:
        p = prev.get(name, 0)
        c = curr.get(name, 0)
        if c == p:
            continue
        kind = "ADDED" if c > p else "REMOVED"
        events.append((name, p, c, c - p, kind))
    return events


def log_event(csv_path, timestamp, event_kind, class_name, delta, prev, new):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not csv_path.exists()
    with open(csv_path, mode='a', newline="") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["timestamp", "event", "class", "delta", "prev_count", "new_count"])
        w.writerow([timestamp, event_kind, class_name, delta, prev, new])


def show_frame(window, frame):
    cv2.imshow(window, frame)
    return cv2.waitKey(1) & 0xFF == ord('q')


def record_sample(prev_counts, counts, csv_path, snap_dir, annotated, ts, ts_compact):
    snap_dir.mkdir(parents=True, exist_ok=True)

    if prev_counts is None:
        for name in sorted(counts):
            log_event(csv_path, ts, "BASELINE", name, counts[name], 0, counts[name])
        snap_path = snap_dir / f"{ts_compact}_baseline.jpg"
        cv2.imwrite(str(snap_path), annotated)
        print(f"BASELINE {dict(counts)}")
        return

    events = diff_counts(prev_counts, counts)
    for name, p, c, delta, kind in events:
        log_event(csv_path, ts, kind, name, delta, p, c)
        print(f"{kind} {name} ({delta:+d})")

    if events:
        snap_path = snap_dir / f"{ts_compact}_event.jpg"
        cv2.imwrite(str(snap_path), annotated)
        # print("DEBUG", dict(counts))


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