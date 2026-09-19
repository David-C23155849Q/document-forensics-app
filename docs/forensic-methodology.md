# Forensic Methodology

This document explains, in plain language, what the Word Forensics System
records and how it interprets that data. It is intended to be shared with
lecturers (and made available to students) for transparency.

## What is recorded

The Word Add-in uses Microsoft's Office.js Word JavaScript API. It can
only see things Office.js legitimately exposes about the *current
document*:

- The full text of the document body, polled at a configurable interval
  (default: 1 second).
- Word/character/paragraph counts derived from that text.
- Timestamps of when the add-in observed a change.

It **cannot** see:

- Keystrokes.
- Clipboard contents.
- Other applications, browser tabs, or files outside this Word document.
- Anything on the operating system outside the Office.js sandbox.

## The three evidence layers

1. **Observed** — raw values read directly from Word (text, counts,
   timestamps).
2. **Derived** — things our system calculates by comparing two observed
   states (insertion size, writing velocity, an "idle" period).
3. **ML** — statistical indicators calculated from the derived data
   (anomaly scores, "unusual pattern" flags).

These layers are never blended in the UI. A "large insertion" is always a
Layer 2 label; it is never presented as an observed paste action unless
Word's API explicitly reports one (which, in the current Office.js
surface, it generally does not for arbitrary insertions).

## What "large insertion" means — and doesn't mean

When the system detects that the document gained N words between two
snapshots, and N exceeds the configured threshold, it records a
`large_insertion` event. This is **only** a statement about how much text
changed and how quickly. It is explicitly **not** a claim that:

- the text was pasted from an external source,
- the text was AI-generated,
- the student did anything against policy.

Many legitimate explanations exist: moving text within the document,
inserting pre-written material the student authored elsewhere, or a
single large edit. The system reports the measurement; the lecturer
applies judgment.

## What ML anomaly scores mean

The ML module (Isolation Forest over a submission's own insertion-size
history) flags insertions or patterns that are statistically unusual
*relative to that submission's own baseline* — not relative to some
external "cheating" model, and not calibrated as a probability of
misconduct. A score of 0.8 means "this looks unusual for this student's
own writing pattern," not "80% chance of cheating."

## Limitations

- Office.js polling has practical latency; a "one-second" interval is a
  target, not a hard real-time guarantee.
- Full-document reconstruction depends on periodic full snapshots plus
  diffs; extremely rapid changes between two full snapshots are
  summarized, not captured word-by-word.
- The system only ever describes activity within this Word document
  during a monitored session.

## No automatic accusations

The system is designed so that it structurally cannot output a verdict
like "student cheated" or a misconduct probability. It surfaces evidence;
academic judgment remains with the lecturer, following the institution's
academic integrity process.
