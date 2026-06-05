# paymyrent.ai

Public showcase dashboard for the Confluence Core trading agent (paper forward test).

## Local dev

```bash
cd paymyrent-web
npm install
npm run dev
```

Generate a local snapshot from the **repo root** (path has spaces — use quotes):

```bash
cd "/Users/nihal/cursor-projects/crypto trading strategy"

# Option A — project venv (Python 3.11)
"./.venv311/bin/python" -m forward_test.publish_snapshot

# Option B — alternate venv
"./.venv/bin/python" -m forward_test.publish_snapshot

# Option C — system Python (if venv missing)
python3 -m forward_test.publish_snapshot
```

Writes `results/forward_test/dashboard_snapshot.json`. Vercel POST only runs if `FORWARD_DASHBOARD_INGEST_URL` and `FORWARD_INGEST_SECRET` are set in `.env`.

With only `dashboard_snapshot.json`, dev mode reads it from `../results/forward_test/` when Blob token is unset.

## Deploy (Vercel)

1. `vercel link` in `paymyrent-web/`
2. Create Vercel Blob store → `BLOB_READ_WRITE_TOKEN`
3. Set `FORWARD_INGEST_SECRET` (same value on GCP VM)
4. `vercel deploy --prod`
5. Add domain **paymyrent.ai** in Vercel → DNS at registrar

## GCP publish

On the forward-test VM:

```bash
FORWARD_DASHBOARD_INGEST_URL=https://paymyrent.ai/api/ingest
FORWARD_INGEST_SECRET=<secret>
.venv311/bin/python -m forward_test.publish_snapshot
```

Enable the publish timer per `deploy/gcp/` (60s).

## API

- `GET /api/status` — latest snapshot JSON
- `POST /api/ingest` — `Authorization: Bearer <FORWARD_INGEST_SECRET>`
