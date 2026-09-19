import { generateClientId, LocalQueueManager } from "./localQueueManager";
import { syncBatch } from "./api";

export type NetworkStatus = "connected" | "synchronizing" | "offline" | "sync_failed" | "sync_complete";

export class SyncService {
  private timer: number | null = null;

  constructor(
    private submissionId: number,
    private intervalMs: number,
    private onStatusChange: (status: NetworkStatus) => void
  ) {}

  start() {
    this.timer = window.setInterval(() => this.flush(), this.intervalMs);
    // Flush immediately on connectivity restoration.
    window.addEventListener("online", () => this.flush());
  }

  stop() {
    if (this.timer) window.clearInterval(this.timer);
  }

  async flush() {
    if (!navigator.onLine) {
      this.onStatusChange("offline");
      return;
    }
    const { events, snapshots } = await LocalQueueManager.getUnsynchronized();
    if (events.length === 0 && snapshots.length === 0) {
      this.onStatusChange("connected");
      return;
    }

    this.onStatusChange("synchronizing");
    try {
      const result = await syncBatch({
        submission_id: this.submissionId,
        events: events as any[],
        snapshots: snapshots as any[],
        client_timestamp: new Date().toISOString(),
        client_id: generateClientId("client"),
      });

      const syncedEventIds = events
        .map((e: any) => e.client_event_id)
        .filter((id: string) => !result.errors?.some((err: any) => err.event === id));
      const syncedSnapshotIds = snapshots
        .map((s: any) => s.client_snapshot_id)
        .filter((id: string) => !result.errors?.some((err: any) => err.snapshot === id));

      await LocalQueueManager.markSynchronized(syncedEventIds, syncedSnapshotIds);
      this.onStatusChange("sync_complete");
    } catch (err) {
      console.warn("SyncService: flush failed, will retry", err);
      this.onStatusChange("sync_failed");
    }
  }
}
