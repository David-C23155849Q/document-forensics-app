/// <reference types="office-js" />

import { generateClientId, LocalQueueManager } from "./localQueueManager";

/**
 * DocumentMonitor polls the Word document via Office.js at the configured
 * interval. It only uses APIs Word actually exposes:
 *   - context.document.body.getText() (full document text)
 *   - context.document.body.paragraphs (paragraph count)
 * It does NOT and cannot observe OS-level clipboard, keystrokes, or other
 * applications - see docs/office-js-limitations.md. A "large insertion" is
 * always a DERIVED classification from comparing two text snapshots, never
 * a claim about how the text got there.
 */

export interface MonitorConfig {
  snapshotIntervalMs: number; // lightweight heartbeat cadence
  fullSnapshotIntervalMs: number; // full-content checkpoint cadence
  largeInsertionWordThreshold: number;
  idleThresholdMs: number;
}

export const DEFAULT_CONFIG: MonitorConfig = {
  snapshotIntervalMs: 1000,
  fullSnapshotIntervalMs: 2000,
  largeInsertionWordThreshold: 100,
  idleThresholdMs: 120000,
};

function wordCount(text: string) {
  return text.trim().length ? text.trim().split(/\s+/).length : 0;
}

export class DocumentMonitor {
  private timer: number | null = null;
  private sequenceNumber = 0;
  private lastText = "";
  private lastFullSnapshotAt = 0;
  private lastActivityAt = Date.now();
  private isIdle = false;

  constructor(
    private submissionId: number,
    private sessionId: number,
    private config: MonitorConfig,
    private onStateUpdate: (state: { wordCount: number; charCount: number; queueSize: number }) => void
  ) {}

  start() {
    this.timer = window.setInterval(() => this.tick(), this.config.snapshotIntervalMs);
  }

  stop() {
    if (this.timer) window.clearInterval(this.timer);
    this.timer = null;
  }

  private async readDocumentText(): Promise<string> {
    // In a non-Office test environment (e.g. this dashboard preview),
    // Office.js will be unavailable; fall back gracefully rather than
    // crashing, per the "handle Word API failures" requirement.
    if (typeof Office === "undefined" || typeof Word === "undefined") {
      return this.lastText; // no-op outside Word
    }
    return Word.run(async (context) => {
      const body = context.document.body;
      body.load("text");
      await context.sync();
      return body.text;
    });
  }

  private async tick() {
    let text: string;
    try {
      text = await this.readDocumentText();
    } catch (err) {
      // Word API failure - do not fabricate a state, just skip this tick.
      console.warn("DocumentMonitor: Word API read failed, skipping tick", err);
      return;
    }

    this.sequenceNumber += 1;
    const now = Date.now();
    const changed = text !== this.lastText;
    const currentWordCount = wordCount(text);
    const previousWordCount = wordCount(this.lastText);

    if (changed) {
      this.lastActivityAt = now;
      if (this.isIdle) {
        this.isIdle = false;
        await this.queueEvent("idle_ended", { previousWordCount, currentWordCount });
      }
    } else {
      const idleFor = now - this.lastActivityAt;
      if (!this.isIdle && idleFor >= this.config.idleThresholdMs) {
        this.isIdle = true;
        await this.queueEvent("idle_started", {
          previousWordCount,
          currentWordCount,
          metadata: { gap_seconds: idleFor / 1000 },
        });
      }
    }

    const dueForFullSnapshot = now - this.lastFullSnapshotAt >= this.config.fullSnapshotIntervalMs;
    const isFull = changed && dueForFullSnapshot;

    await LocalQueueManager.addSnapshot({
      client_snapshot_id: generateClientId("snap"),
      session_id: this.sessionId,
      submission_id: this.submissionId,
      timestamp: new Date(now).toISOString(),
      sequence_number: this.sequenceNumber,
      word_count: currentWordCount,
      character_count: text.length,
      content_changed: changed,
      change_type: changed ? this.classifyChange(previousWordCount, currentWordCount) : "",
      content: text, // im just gonna try some shit
      force_full: true,
    });
    if (isFull) this.lastFullSnapshotAt = now;

    if (changed) {
      const delta = currentWordCount - previousWordCount;
      if (delta > 0) {
        await this.queueEvent(
          delta >= this.config.largeInsertionWordThreshold ? "large_insertion" : "insertion",
          { previousWordCount, currentWordCount, wordsAffected: delta }
        );
      } else if (delta < 0) {
        await this.queueEvent("deletion", { previousWordCount, currentWordCount, wordsAffected: -delta });
      }
    }

    this.lastText = text;

    const queueSize = await LocalQueueManager.queueSize();
    this.onStateUpdate({ wordCount: currentWordCount, charCount: text.length, queueSize });
  }

  private classifyChange(prevWords: number, newWords: number) {
    const delta = newWords - prevWords;
    if (delta > 0) return delta >= this.config.largeInsertionWordThreshold ? "large_insertion" : "insertion";
    if (delta < 0) return "deletion";
    return "edit";
  }

  private async queueEvent(
    eventType: string,
    data: { previousWordCount: number; currentWordCount: number; wordsAffected?: number; metadata?: Record<string, unknown> }
  ) {
    await LocalQueueManager.addEvent({
      client_event_id: generateClientId("evt"),
      session_id: this.sessionId,
      submission_id: this.submissionId,
      event_type: eventType,
      timestamp: new Date().toISOString(),
      previous_word_count: data.previousWordCount,
      new_word_count: data.currentWordCount,
      words_affected: data.wordsAffected || 0,
      detection_method: "office_js_document_state_diff",
      classification_confidence: eventType === "large_insertion" ? "HIGH" : "MEDIUM",
      metadata: data.metadata || null,
    });
  }
}
