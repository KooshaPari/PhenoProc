# Reference

## Core reference docs

- [Specification](../../SPEC.md)
- [ADR Index](../ADR.md)
- [Process architecture ADRs](../adr/ADR-001.md)
- [Research: Job Scheduling](../research/SOTA-Job-Scheduling.md)
- [Research: Process Management](../research/SOTA-Process-Management.md)

## Crate surface map

- `pheno-proc-core`: process lifecycle and pool management
- `pheno-proc-dedup`: command deduplication and caching
- `pheno-proc-queue`: priority queuing (details in `SPEC.md`)
- `pheno-proc-shm`: shared memory primitives
- `pheno-proc-uds`: Unix domain socket transport
