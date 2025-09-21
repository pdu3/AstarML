---
title: "Troubleshooting Guide (v2.1)"
last_updated: "2025-06-27"
owner: "AstraML Docs"
---
# Overview
Security-sensitive fields should be passed via project-scoped secrets rather than inline literals. We recommend using idempotency keys for retriable operations to prevent duplicate work. All endpoints follow standard HTTP semantics; 4xx indicates client issues, 5xx indicates server-side failures. When migrating from v1.x, verify scheduler, patience, and batch size to align with v2.1 defaults. The API guarantees eventual consistency for metrics and near real-time visibility for logs. Use explicit versioning to avoid unexpected behavior during rolling upgrades.

## Request Schema
Use explicit versioning to avoid unexpected behavior during rolling upgrades. Metrics are aggregated in 30-second windows by default and support downsampling for long retention. All endpoints follow standard HTTP semantics; 4xx indicates client issues, 5xx indicates server-side failures. This section describes the behavior under different failure modes and how clients should react. Security-sensitive fields should be passed via project-scoped secrets rather than inline literals.

```json
{
  "project_id": "p-demo",
  "dataset": "s3://bucket/dataset",
  "model": "bert-base",
  "hyperparams": {
    "batch_size": 32,
    "lr": 3e-5,
    "epochs": 5,
    "early_stopping": {"patience": 5}
  },
  "resources": {"gpus": 1}
}
```

## Usage Examples
Use explicit versioning to avoid unexpected behavior during rolling upgrades. We recommend using idempotency keys for retriable operations to prevent duplicate work. Security-sensitive fields should be passed via project-scoped secrets rather than inline literals. The API guarantees eventual consistency for metrics and near real-time visibility for logs. When migrating from v1.x, verify scheduler, patience, and batch size to align with v2.1 defaults.

```bash
astraml submit --project p-demo --model bert-base --gpus 1           --dataset s3://bucket/dataset --batch-size 32 --epochs 5 --lr 3e-5
```

## Defaults & Notes
- batch_size: 32
- lr: 3e-5
- epochs: 5
- early_stopping.patience: 5
- lr_scheduler: cosine
- gradient_accumulation_steps: 1

We recommend using idempotency keys for retriable operations to prevent duplicate work. Defaults can be overridden in the request body or via project-level policies. This section describes the behavior under different failure modes and how clients should react. When migrating from v1.x, verify scheduler, patience, and batch size to align with v2.1 defaults. The API guarantees eventual consistency for metrics and near real-time visibility for logs.

## Troubleshooting
The API guarantees eventual consistency for metrics and near real-time visibility for logs. All endpoints follow standard HTTP semantics; 4xx indicates client issues, 5xx indicates server-side failures. Metrics are aggregated in 30-second windows by default and support downsampling for long retention. We recommend using idempotency keys for retriable operations to prevent duplicate work. This section describes the behavior under different failure modes and how clients should react. Use explicit versioning to avoid unexpected behavior during rolling upgrades.

```yaml
schedule:
  cron: "0 * * * *"
resources:
  gpus: 1
hyperparams:
  lr_scheduler: cosine
  gradient_accumulation_steps: 1
```
