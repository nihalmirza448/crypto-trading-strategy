// Snapshot persistence for the forward-test dashboard.
//
// Production: stored in Vercel Blob (set BLOB_READ_WRITE_TOKEN). The external
// publisher POSTs to /api/ingest hourly, which calls writeSnapshot(); the
// dashboard reads it via /api/status -> readSnapshot().
//
// Local dev (no Blob token): falls back to the JSON file written by
// `forward_test.publish_snapshot` at results/forward_test/dashboard_snapshot.json.

import { list, put } from "@vercel/blob";
import type { ForwardSnapshot } from "@/lib/types";

const SNAPSHOT_PATH = "forward/dashboard_snapshot.json";

function blobToken(): string | undefined {
  return process.env.BLOB_READ_WRITE_TOKEN || undefined;
}

async function readLocalSnapshot(): Promise<ForwardSnapshot | null> {
  try {
    const { readFile } = await import("node:fs/promises");
    const path = await import("node:path");
    const candidates = [
      path.join(process.cwd(), "..", "results", "forward_test", "dashboard_snapshot.json"),
      path.join(process.cwd(), "results", "forward_test", "dashboard_snapshot.json"),
    ];
    for (const file of candidates) {
      try {
        const raw = await readFile(file, "utf8");
        return JSON.parse(raw) as ForwardSnapshot;
      } catch {
        // try next candidate
      }
    }
  } catch {
    // fs unavailable
  }
  return null;
}

async function writeLocalSnapshot(snapshot: ForwardSnapshot): Promise<void> {
  const { mkdir, writeFile } = await import("node:fs/promises");
  const path = await import("node:path");
  const dir = path.join(process.cwd(), "..", "results", "forward_test");
  await mkdir(dir, { recursive: true });
  await writeFile(
    path.join(dir, "dashboard_snapshot.json"),
    JSON.stringify(snapshot, null, 2),
    "utf8",
  );
}

export async function readSnapshot(): Promise<ForwardSnapshot | null> {
  const token = blobToken();
  if (!token) {
    return readLocalSnapshot();
  }

  try {
    const { blobs } = await list({ token, prefix: SNAPSHOT_PATH, limit: 100 });
    if (!blobs.length) return null;
    // Newest upload wins (overwrites keep the same pathname).
    const latest = blobs.reduce((a, b) =>
      new Date(b.uploadedAt).getTime() > new Date(a.uploadedAt).getTime() ? b : a,
    );
    const res = await fetch(`${latest.url}?ts=${Date.now()}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as ForwardSnapshot;
  } catch {
    return null;
  }
}

export async function writeSnapshot(snapshot: ForwardSnapshot): Promise<void> {
  const token = blobToken();
  if (!token) {
    await writeLocalSnapshot(snapshot);
    return;
  }

  await put(SNAPSHOT_PATH, JSON.stringify(snapshot), {
    access: "public",
    token,
    contentType: "application/json",
    addRandomSuffix: false,
    cacheControlMaxAge: 0,
  });
}
