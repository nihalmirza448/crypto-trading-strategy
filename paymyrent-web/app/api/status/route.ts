import { readSnapshot } from "@/lib/blob";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const snapshot = await readSnapshot();
  if (!snapshot) {
    return NextResponse.json(
      { error: "No snapshot yet. Run publish_snapshot or POST /api/ingest." },
      { status: 404 },
    );
  }
  return NextResponse.json(snapshot, {
    headers: {
      "Cache-Control": "public, max-age=10, stale-while-revalidate=30",
    },
  });
}
