---
title: "Hyperparameter Tuning Service (v2.1)"
last_updated: "2025-06-22"
owner: "AstraML Docs"
---
# Overview
Defaults can be overridden in the request body or via project-level policies. All endpoints follow standard HTTP semantics; 4xx indicates client issues, 5xx indicates server-side failures. We recommend using idempotency keys for retriable operations to prevent duplicate work. Use explicit versioning to avoid unexpected behavior during rolling upgrades. This section describes the behavior under different failure modes and how clients should react. The examples below illustrate recommended values for common workloads.

## Request Schema
Metrics are aggregated in 30-second windows by default and support downsampling for long retention. The API guarantees eventual consistency for metrics and near real-time visibility for logs. The examples below illustrate recommended values for common workloads. When migrating from v1.x, verify scheduler, patience, and batch size to align with v2.1 defaults. This section describes the behavior under different failure modes and how clients should react.

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
This section describes the behavior under different failure modes and how clients should react. The API guarantees eventual consistency for metrics and near real-time visibility for logs. Use explicit versioning to avoid unexpected behavior during rolling upgrades. When migrating from v1.x, verify scheduler, patience, and batch size to align with v2.1 defaults. The examples below illustrate recommended values for common workloads.

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

Metrics are aggregated in 30-second windows by default and support downsampling for long retention. All endpoints follow standard HTTP semantics; 4xx indicates client issues, 5xx indicates server-side failures. This section describes the behavior under different failure modes and how clients should react. We recommend using idempotency keys for retriable operations to prevent duplicate work. Use explicit versioning to avoid unexpected behavior during rolling upgrades.

## Troubleshooting
When migrating from v1.x, verify scheduler, patience, and batch size to align with v2.1 defaults. Metrics are aggregated in 30-second windows by default and support downsampling for long retention. This section describes the behavior under different failure modes and how clients should react. Security-sensitive fields should be passed via project-scoped secrets rather than inline literals. All endpoints follow standard HTTP semantics; 4xx indicates client issues, 5xx indicates server-side failures. Use explicit versioning to avoid unexpected behavior during rolling upgrades.

```yaml
schedule:
  cron: "0 * * * *"
resources:
  gpus: 1
hyperparams:
  lr_scheduler: cosine
  gradient_accumulation_steps: 1
```
