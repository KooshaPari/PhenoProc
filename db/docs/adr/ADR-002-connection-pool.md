# ADR-002: Connection Pool Configuration

**Date**: 2026-04-05  
**Status**: Accepted  
**Deciders**: Phenotype Engineering Team

## Context

Database connection pool configuration directly impacts application performance, resource usage, and availability.

## Decision Drivers

- **Performance**: Minimize connection overhead
- **Resource limits**: Respect database capacity
- **Availability**: Handle connection failures gracefully
- **Scalability**: Support growing load

## Options Considered

### Option A: Opinionated Defaults (Selected)

```go
type PoolConfig struct {
    MaxOpenConns    int           // Default: 25
    MaxIdleConns    int           // Default: 5
    ConnMaxLifetime time.Duration // Default: 5 minutes
    ConnMaxIdleTime time.Duration // Default: 1 minute
}
```

**Pros**:
- Sensible defaults
- Based on production experience
- Tuning guidance provided

**Cons**:
- May not fit all workloads
- Requires tuning for scale

### Option B: Unlimited Connections

Use default Go sql.DB settings (unlimited).

**Pros**:
- Simple
- No configuration

**Cons**:
- Risk of connection exhaustion
- Database overload
- Unpredictable behavior

### Option C: Dynamic Auto-Tuning

Automatically adjust pool based on load.

**Pros**:
- Self-optimizing
- Adapts to workload

**Cons**:
- Complex implementation
- Unpredictable behavior
- Hard to debug

## Decision

**Provide opinionated defaults with clear tuning guidelines.**

## Consequences

### Positive
- Predictable resource usage
- Performance guidance
- Production-ready defaults

### Negative
- Requires tuning at scale
- May need adjustment per service

## Guidelines

| Workload | MaxOpenConns | MaxIdleConns | Lifetime |
|----------|--------------|--------------|----------|
| Light (<100 RPS) | 10 | 5 | 5m |
| Medium (100-1000 RPS) | 25 | 10 | 5m |
| Heavy (>1000 RPS) | 50 | 25 | 10m |

---

*Pool configuration is service-specific and reviewed in load testing.*
