import { DBSchema, IDBPDatabase, openDB } from "idb";

interface QueueDB extends DBSchema {
  events: {
    key: string; // client_event_id
    value: Record<string, unknown>;
  };
  snapshots: {
    key: string; // client_snapshot_id
    value: Record<string, unknown>;
  };
}

const DB_NAME = "word-forensics-queue";
const DB_VERSION = 1;

let dbPromise: Promise<IDBPDatabase<QueueDB>> | null = null;

function getDb() {
  if (!dbPromise) {
    dbPromise = openDB<QueueDB>(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains("events")) db.createObjectStore("events");
        if (!db.objectStoreNames.contains("snapshots")) db.createObjectStore("snapshots");
      },
    });
  }
  return dbPromise;
}

/**
 * LocalQueueManager: buffers events/snapshots in IndexedDB so the add-in
 * keeps working offline. Records are removed only once the server has
 * acknowledged them (see SyncService), and every record carries a
 * client-generated ID so re-sending after a crash never creates duplicates.
 */
export const LocalQueueManager = {
  async addEvent(event: Record<string, unknown> & { client_event_id: string }) {
    const db = await getDb();
    await db.put("events", event, event.client_event_id);
  },

  async addSnapshot(snapshot: Record<string, unknown> & { client_snapshot_id: string }) {
    const db = await getDb();
    await db.put("snapshots", snapshot, snapshot.client_snapshot_id);
  },

  async getUnsynchronized() {
    const db = await getDb();
    const events = await db.getAll("events");
    const snapshots = await db.getAll("snapshots");
    return { events, snapshots };
  },

  async markSynchronized(eventIds: string[], snapshotIds: string[]) {
    const db = await getDb();
    const tx1 = db.transaction("events", "readwrite");
    await Promise.all(eventIds.map((id) => tx1.store.delete(id)));
    await tx1.done;

    const tx2 = db.transaction("snapshots", "readwrite");
    await Promise.all(snapshotIds.map((id) => tx2.store.delete(id)));
    await tx2.done;
  },

  async queueSize() {
    const db = await getDb();
    const e = await db.count("events");
    const s = await db.count("snapshots");
    return e + s;
  },
};

export function generateClientId(prefix: string) {
  return `${prefix}_${crypto.randomUUID()}`;
}
