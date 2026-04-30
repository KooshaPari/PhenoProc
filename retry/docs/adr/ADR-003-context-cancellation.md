# ADR-003: Context-Aware Cancellation

**Date**: 2026-04-05  
**Status**: Accepted  
**Deciders**: Phenotype Engineering Team

## Context

Retry loops must respect context cancellation to support request timeouts and graceful shutdown.

## Decision Drivers

- **Responsiveness**: Stop retrying when caller gives up
- **Resource cleanup**: Release resources on cancellation
- **Graceful degradation**: Respect system state
- **Testability**: Timeouts in tests

## Options Considered

### Option A: Check Context Before Each Attempt (Selected)

```go
for attempt := 1; attempt <= cfg.MaxAttempts; attempt++ {
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
    }
    
    if err := fn(ctx); err != nil {
        // ... retry logic
    }
}
```

**Pros**:
- Respects cancellation immediately
- Standard Go pattern
- Works with deadlines/timeouts

**Cons**:
- Small overhead per iteration

### Option B: Pass Context to Retry Function Only

Let the function handle context, check only final error.

**Pros**:
- Simpler retry code
- Function has full control

**Cons**:
- Can't cancel during backoff
- May continue after timeout

### Option C: Background Retries

Ignore context for retries, use background.

**Pros**:
- Guaranteed completion

**Cons**:
- Violates caller expectations
- Resource leaks on shutdown

## Decision

**Check context before each retry attempt and during backoff waits.**

## Implementation

```go
// Check before attempt
select {
case <-ctx.Done():
    return ctx.Err()
default:
}

// Check during backoff
select {
case <-ctx.Done():
    return ctx.Err()
case <-time.After(delay):
}
```

## Consequences

### Positive
- Proper cancellation support
- No wasted retry attempts
- Clean shutdown behavior

### Negative
- Need to pass context everywhere
- Slightly more complex code

---

*Context-aware retries are required for all Phenotype services.*
