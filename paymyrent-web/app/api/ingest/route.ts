import { writeSnapshot } from "@/lib/blob";
import type { ForwardSnapshot } from "@/lib/types";
import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const secret = process.env.FORWARD_INGEST_SECRET;
  if (!secret) {
    return NextResponse.json(
      { error: "FORWARD_INGEST_SECRET not configured" },
      { status: 500 },
    );
  }

  const auth = req.headers.get("authorization") || "";
  if (auth !== `Bearer ${secret}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let body: ForwardSnapshot;
  try {
    body = (await req.json()) as ForwardSnapshot;
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  if (!body.tracks || !Array.isArray(body.tracks)) {
    return NextResponse.json({ error: "Missing tracks array" }, { status: 400 });
  }

  await writeSnapshot(body);
  return NextResponse.json({
    ok: true,
    tracks: body.tracks.length,
    updated_at: body.updated_at,
  });
}
