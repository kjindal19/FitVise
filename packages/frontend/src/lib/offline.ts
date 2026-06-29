// Offline logging queue (PRD §3.1). Mutations made while offline are persisted
// to IndexedDB and flushed on reconnect. Conflict strategy: last-write-wins —
// the server simply accepts whatever arrives, ordered by client timestamp.

import { get, set } from "idb-keyval";
import { api } from "./api";

const QUEUE_KEY = "fitvise.offline.queue";

export interface QueuedRequest {
  id: string;
  path: string;
  method: string;
  body: unknown;
  queued_at: string;
}

async function readQueue(): Promise<QueuedRequest[]> {
  return (await get<QueuedRequest[]>(QUEUE_KEY)) ?? [];
}
async function writeQueue(q: QueuedRequest[]) {
  await set(QUEUE_KEY, q);
}

export async function queueSize(): Promise<number> {
  return (await readQueue()).length;
}

/** Try a mutation immediately; if offline, queue it and resolve optimistically. */
export async function mutate(path: string, method: string, body: unknown): Promise<boolean> {
  if (navigator.onLine) {
    try {
      await api(path, { method, json: body });
      return true; // synced
    } catch {
      /* fall through to queue on network failure */
    }
  }
  const q = await readQueue();
  q.push({
    id: crypto.randomUUID(),
    path,
    method,
    body,
    queued_at: new Date().toISOString(),
  });
  await writeQueue(q);
  return false; // queued
}

/** Flush queued mutations in order. Returns count successfully synced. */
export async function flushQueue(): Promise<number> {
  if (!navigator.onLine) return 0;
  let q = await readQueue();
  let synced = 0;
  const remaining: QueuedRequest[] = [];
  for (const item of q) {
    try {
      await api(item.path, { method: item.method, json: item.body });
      synced++;
    } catch {
      remaining.push(item); // keep for next attempt
    }
  }
  await writeQueue(remaining);
  return synced;
}

export function initOfflineSync(onFlush?: (n: number) => void) {
  const run = () => flushQueue().then((n) => n && onFlush?.(n));
  window.addEventListener("online", run);
  run();
}
