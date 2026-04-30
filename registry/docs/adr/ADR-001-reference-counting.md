# ADR-001: Reference Counting for Registry

**Date**: 2026-04-05  
**Status**: Accepted  
**Deciders**: Phenotype Engineering Team

## Context

The registry needs to support multiple owners for the same resource, ensuring cleanup only occurs when all owners have unregistered.

## Decision Drivers

- **Resource sharing**: Multiple components may use same resource
- **Automatic cleanup**: No manual reference management
- **Thread safety**: Concurrent access patterns
- **Simplicity**: Easy to understand and debug

## Options Considered

### Option A: Reference Counting (Selected)

```go
type entry[V any] struct {
    value V
    count int  // Reference count
}
```

**Pros**:
- Automatic resource lifecycle
- Well-understood pattern
- Deterministic cleanup

**Cons**:
- Cyclic reference risk
- Debugging complexity

### Option B: Single Owner

Each entry has exactly one owner.

**Pros**:
- Simple
- No counting needed

**Cons**:
- Requires wrapper/aggregator for shared resources
- More complex for shared use cases

### Option C: Garbage Collection

Let Go GC handle cleanup.

**Pros**:
- No manual tracking
- Automatic

**Cons**:
- Non-deterministic
- No explicit lifecycle hooks

## Decision

**Implement reference counting with explicit owner tracking.**

## Consequences

### Positive
- Predictable resource cleanup
- Support for shared resources
- Hook integration for metrics/logging

### Negative
- Must avoid reference cycles
- Careful error handling needed

## Implementation

See [registry.go](../../registry.go) for implementation details.

---

*Reference counting is used for all shared registry resources.*
