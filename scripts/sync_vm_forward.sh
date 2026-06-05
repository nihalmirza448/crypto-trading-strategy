#!/bin/bash
# Pull latest forward-test data from the GCP VM into the local mirror and rebuild
# the dashboard snapshot. Run on a timer by com.nihal.crypto-forward-sync.plist.
set -uo pipefail

export PATH="/opt/homebrew/bin:/opt/homebrew/share/google-cloud-sdk/bin:/usr/bin:/bin:/usr/sbin:/sbin"

REPO="/Users/nihal/cursor-projects/crypto trading strategy"
VM="crypto-trading-vm"
ZONE="asia-south1-a"
REMOTE="/opt/crypto-trading-strategy/results/forward_test"

cd "$REPO" || exit 1

ts() { date "+%Y-%m-%dT%H:%M:%S"; }

gcloud compute ssh "$VM" --zone="$ZONE" \
  --command="cd $REMOTE && tar czf /tmp/ft_sync.tgz --exclude=suite.log --exclude=dashboard_snapshot.json ." \
  || { echo "$(ts) ssh/tar failed"; exit 1; }

gcloud compute scp "$VM:/tmp/ft_sync.tgz" /tmp/ft_sync.tgz --zone="$ZONE" \
  || { echo "$(ts) scp failed"; exit 1; }

tar xzf /tmp/ft_sync.tgz -C results/forward_test/ \
  || { echo "$(ts) extract failed"; exit 1; }

.venv/bin/python forward_test/write_local_snapshot.py \
  || { echo "$(ts) snapshot build failed"; exit 1; }

echo "$(ts) sync ok"
