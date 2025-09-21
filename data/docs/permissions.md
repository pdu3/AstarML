---
title: "Permissions & Roles (v2.1)"
last_updated: "2025-07-06"
owner: "AstraML Docs"
---
# Overview
Metrics are aggregated in 30-second windows by default and support downsampling for long retention. We recommend using idempotency keys for retriable operations to prevent duplicate work. When migrating from v1.x, verify scheduler, patience, and batch size to align with v2.1 defaults. All endpoints follow standard HTTP semantics; 4xx indicates client issues, 5xx indicates server-side failures. The API guarantees eventual consistency for metrics and near real-time visibility for logs. Security-sensitive fields should be passed via project-scoped secrets rather than inline literals.

## Request Schema
When migrating from v1.x, verify scheduler, patience, and batch size to align with v2.1 defaults. This section describes the behavior under different failure modes and how clients should react. Defaults can be overridden in the request body or via project-level policies. Metrics are aggregated in 30-second windows by default and support downsampling for long retention. We recommend using idempotency keys for retriable operations to prevent duplicate work.

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
Metrics are aggregated in 30-second windows by default and support downsampling for long retention. Use explicit versioning to avoid unexpected behavior during rolling upgrades. Security-sensitive fields should be passed via project-scoped secrets rather than inline literals. We recommend using idempotency keys for retriable operations to prevent duplicate work. When migrating from v1.x, verify scheduler, patience, and batch size to align with v2.1 defaults.

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

Security-sensitive fields should be passed via project-scoped secrets rather than inline literals. When migrating from v1.x, verify scheduler, patience, and batch size to align with v2.1 defaults. The examples below illustrate recommended values for common workloads. We recommend using idempotency keys for retriable operations to prevent duplicate work. Use explicit versioning to avoid unexpected behavior during rolling upgrades.

## Troubleshooting
The examples below illustrate recommended values for common workloads. Defaults can be overridden in the request body or via project-level policies. Security-sensitive fields should be passed via project-scoped secrets rather than inline literals. Metrics are aggregated in 30-second windows by default and support downsampling for long retention. All endpoints follow standard HTTP semantics; 4xx indicates client issues, 5xx indicates server-side failures. We recommend using idempotency keys for retriable operations to prevent duplicate work.

```yaml
schedule:
  cron: "0 * * * *"
resources:
  gpus: 1
hyperparams:
  lr_scheduler: cosine
  gradient_accumulation_steps: 1
```
