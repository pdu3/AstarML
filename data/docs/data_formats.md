---
title: "Datasets & Data Formats (v2.1)"
last_updated: "2025-06-21"
owner: "AstraML Docs"
---
# Overview
When migrating from v1.x, verify scheduler, patience, and batch size to align with v2.1 defaults. Use explicit versioning to avoid unexpected behavior during rolling upgrades. Defaults can be overridden in the request body or via project-level policies. The examples below illustrate recommended values for common workloads. Metrics are aggregated in 30-second windows by default and support downsampling for long retention. Security-sensitive fields should be passed via project-scoped secrets rather than inline literals.

## Request Schema
Use explicit versioning to avoid unexpected behavior during rolling upgrades. The examples below illustrate recommended values for common workloads. Security-sensitive fields should be passed via project-scoped secrets rather than inline literals. The API guarantees eventual consistency for metrics and near real-time visibility for logs. Defaults can be overridden in the request body or via project-level policies.

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
The API guarantees eventual consistency for metrics and near real-time visibility for logs. All endpoints follow standard HTTP semantics; 4xx indicates client issues, 5xx indicates server-side failures. The examples below illustrate recommended values for common workloads. This section describes the behavior under different failure modes and how clients should react. When migrating from v1.x, verify scheduler, patience, and batch size to align with v2.1 defaults.

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

We recommend using idempotency keys for retriable operations to prevent duplicate work. When migrating from v1.x, verify scheduler, patience, and batch size to align with v2.1 defaults. Defaults can be overridden in the request body or via project-level policies. This section describes the behavior under different failure modes and how clients should react. Metrics are aggregated in 30-second windows by default and support downsampling for long retention.

## Troubleshooting
The examples below illustrate recommended values for common workloads. Use explicit versioning to avoid unexpected behavior during rolling upgrades. Defaults can be overridden in the request body or via project-level policies. When migrating from v1.x, verify scheduler, patience, and batch size to align with v2.1 defaults. The API guarantees eventual consistency for metrics and near real-time visibility for logs. Metrics are aggregated in 30-second windows by default and support downsampling for long retention.

```yaml
schedule:
  cron: "0 * * * *"
resources:
  gpus: 1
hyperparams:
  lr_scheduler: cosine
  gradient_accumulation_steps: 1
```
