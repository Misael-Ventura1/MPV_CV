# Storage unit item detection — MVP plan + post-MVP roadmap

## Context and deadline
Building a computer vision system that watches a storage unit and:
1. Detects and classifies items currently in view
2. Determines when an item is **added** or **removed**

**MVP, flow diagram, and presentation are due Thursday evening.** That's
roughly one working day, so this plan is split in two:

- **Part A — MVP**: the smallest version that demonstrably works, to be built
  now, directly, without slowing down for exploration or teaching.
- **Part B — Post-MVP roadmap**: the real exploration work (data collection,
  architecture comparisons, motion-trigger tuning, robustness testing).
  This is *not* this week's problem — don't let it bleed into MVP scope.

---

## Part A — MVP (due Thursday evening)

### Working mode for this part only
Claude Code should write the MVP code directly rather than pseudocode or a
scaffold — speed matters more than teaching right now. After each piece is
written, explain how it works (what it does, why this approach, what the key
parameters are) so it's still a learning artifact, not just a black box —
but the explanation comes *after* working code, not instead of it.

### Scope — keep it deliberately narrow
- [ ] **Capture**: continuous video connection, but detection only runs on a
      sampled frame every N seconds (e.g. every 5–10s), not every frame.
      This matters because there's no dedicated GPU — running YOLO on every
      frame of real continuous video isn't realistic on CPU alone (expect
      only a few frames per second at best from the detector itself, so
      trying to keep up with a full video framerate will cause lag or
      dropped frames). Sampling frames from the live stream gets the
      simplicity and CPU-friendliness of a snapshot approach while still
      keeping a continuous video connection as the input source.
      No motion triggering yet — that's Part B.
- [ ] **Detection**: pretrained YOLO (stock classes, no custom training).
      If the actual storage items aren't in the stock classes, use
      whatever closest generic class is available (e.g. "box", "bottle")
      as a stand-in and say so explicitly in the presentation — custom
      training is Part B, not Part A.
- [ ] **Event logic**: simple count-diff between consecutive snapshots per
      class. No tracking, no hysteresis tuning — just "count went up" /
      "count went down" logic.
- [ ] **Output**: log the count and change events to console or a simple
      file. A live dashboard or alert system is out of scope for the MVP.

### Explicitly out of scope for MVP (don't build these yet)
- Custom-trained model on real storage items
- Motion-triggered capture
- Robustness handling for lighting changes
- Tracking across frames / continuous video

### MVP deliverables checklist
- [ ] Working script that takes snapshots on an interval and runs detection
- [ ] Count-diff logic producing add/remove events in a log
- [ ] Flow diagram of the actual MVP architecture (already built earlier in
      this conversation — update it if the real implementation ends up
      differing from what's drawn)
- [ ] Presentation deck for your manager covering: the problem, the MVP
      architecture diagram, a short demo or screenshots of it working, known
      limitations (stock classes, no custom training yet, lighting
      sensitivity untested), and the next-steps roadmap (Part B below)

---

## Part B — Post-MVP roadmap (not this week)

This is where the real exploration happens, once the MVP has bought some
breathing room. Working mode here is different from Part A:

### Working mode for this part
- [ ] **Default output is pseudocode, not working code.** Write step-by-step
      pseudocode first — specific enough to build from (name real
      inputs/outputs, name the library/technique per step, call out tricky
      logic) — as a reference for what needs to be built, so the code can be
      written and learned hands-on rather than handed over finished.
- [ ] Only write full runnable code when explicitly requested — e.g. to
      verify a benchmark, or as a reference after getting stuck. Follow any
      requested code with a line-by-line or block-by-block walkthrough.
- [ ] Explain concepts before implementation: what problem it solves, why
      this approach vs. alternatives, what the key parameters/decisions are.
- [ ] When something fails or underperforms, explain why in plain terms
      before fixing it — a teaching moment, not a silent patch.
- [ ] If you (Claude) have a better idea than what's listed below at any
      point, add it to the comparison rather than only working the checklist
      as written. Explain specifically why it's likely better, what weakness
      it addresses, and what tradeoff it introduces — backed by a quick test,
      not just a claim. Flag it clearly as a suggestion beyond the plan.

### Phase 1 — Capture strategy
- [ ] Fixed-interval snapshot at a few different intervals (compare to MVP baseline)
- [ ] Motion-triggered snapshot via raw frame differencing
- [ ] Motion-triggered snapshot via background subtraction (OpenCV MOG2/KNN)
- [ ] Hybrid: motion trigger + fixed-interval fallback
- [ ] Explicitly test the known lighting-sensitivity risk with naive frame
      differencing, and confirm whether background subtraction actually fixes it

**Compare on:** compute cost, false-trigger rate under lighting changes,
missed-event rate, storage footprint.

### Phase 2 — Data collection & annotation strategy
- [ ] Estimate how much labeled data is realistically needed per item class
- [ ] Try an annotation tool/workflow (Roboflow, CVAT, LabelImg) and note time cost
- [ ] Test augmentation (rotation, lighting jitter, occlusion, background swap)
      to stretch a small real dataset
- [ ] Flag visually similar items that may need extra distinguishing data

### Phase 3 — Detection model
- [ ] Confirm stock YOLO's failure/limitation on real items (document the MVP gap)
- [ ] Fine-tune a YOLO variant on real labeled data from Phase 2
- [ ] Try at least one alternative architecture for comparison
- [ ] Benchmark inference speed on actual target hardware, not just dev machine

**Compare on:** mAP, latency, model size, occlusion robustness.

### Phase 4 — Add/remove event logic
- [ ] Confidence thresholding/hysteresis to avoid single-flicker false events
- [ ] If continuous video re-enters consideration: compare a lightweight
      tracker (ByteTrack, SORT) against pure snapshot diffing
- [ ] Handle multiple simultaneous changes between two snapshots gracefully

### Phase 5 — Robustness stress tests
- [ ] Lighting changes (gradual, sudden, shadows)
- [ ] Partial occlusion during capture
- [ ] Camera angle/zoom variation
- [ ] Similar-item confusion
- [ ] Long-running drift/stability

### Phase 6 — Recommendation
- [ ] Chosen capture strategy, detection approach, and event logic + why
- [ ] Known limitations and what's needed for higher reliability
- [ ] Rough compute/hardware requirements for deployment
- [ ] How results compare to initial expectations, and what changed along the way
