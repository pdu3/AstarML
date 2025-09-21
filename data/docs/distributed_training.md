---
title: "Distributed Training (v2.1)"
last_updated: "2025-07-19"
owner: "Product Engineering"
---
# Overview
This document describes the Distributed Training module in AstraML v2.1. It outlines supported fields, defaults, migration notes from v1.x, and example usage. The intent is normative and versioned; readers should treat this as the authoritative specification.

## Request Schema

```json
{
  "project_id": "proj-691",
  "dataset": "s3://bucket/dataset-1",
  "model": "bert-base",
  "hyperparams": {
    "batch_size": 32,
    "lr": 3e-5,
    "epochs": 5,
    "early_stopping": {"patience": 5},
    "lr_scheduler": "cosine",
    "gradient_accumulation_steps": 1
  },
  "resources": {"gpus": 1}
}
```


## Usage Examples

```bash
# submit a standard job
astraml submit --project demo --model bert-base --gpus 1 \      --dataset s3://bucket/ds --batch-size 32 --epochs 5 --lr 3e-5

# fetch metrics
astraml metrics --job-id 12345 --window 30s
```


## Defaults & Notes
- batch_size: 32 (v2.1 default)
- lr: 3e-5
- epochs: 5
- early_stopping.patience: 5
- lr_scheduler: cosine
- concurrency: 2 (legacy tenants may observe 1)
- artifact_retention_days: 30
- storage_quota_tb: 5
Notes: These defaults may evolve; consult last_updated for changes.

Implementation details emphasize determinism and backward compatibility where feasible. Where behavior changed from v1.x, the change is documented with explicit rationale. Examples are intentionally minimal to reduce ambiguity and copy-paste errors. Security-sensitive fields should be supplied via secret references, not inline strings.

## Troubleshooting
If jobs queue for longer than expected, confirm available quota and see autoscaling cooldown. For 429s on inference endpoints, reduce burst RPM or apply token budgets. If registry automation fails, verify permissions and roll back to a known-good snapshot.

```yaml
schedule:
  cron: "0 * * * *"
resources: { gpus: 1 }
```
