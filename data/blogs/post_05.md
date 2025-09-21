---
author: "Karl Chen"
published_date: "2025-05-26"
title: "Concurrency Oddities on Legacy Tenants"
---
# Concurrency Oddities on Legacy Tenants
## Context
This post reflects field experience rather than policy. Numbers are indicative and may not match every workload. We call out divergences from v2.1 docs where applicable.

## Findings
- Observation on workload shape and throughput/latency trade-offs.
- Cases where the documented defaults underperform (and why).
- Surprising behavior on legacy tenants and migration caveats.

## Examples

```bash
astraml submit --project demo --model roberta-base --gpus 1 \      --dataset s3://bucket/blog-ds-5 --batch-size 64 \      --epochs 5 --lr 3e-5 --lr-scheduler step
```


## Recommendations
Start with documented defaults, then profile. Increase batch_size only when memory headroom is measured. Prefer cosine for long runs; step may fit short, sharp schedules. Consider 60-day artifact retention in regulated environments, despite 30-day default.

Tokenization overhead can dominate at small batch sizes; pipeline parallelism helps minimally. Autoscaling sensitivity to queue depth interacts with retry storms; tune cooldowns accordingly. Metrics at 10s granularity improve RCA but can raise storage and I/O costs by double digits.
