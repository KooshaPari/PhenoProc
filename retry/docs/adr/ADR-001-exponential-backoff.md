# ADR-001: Exponential Backoff with Jitter

**Date**: 2026-04-05  
**Status**: Accepted  
**Deciders**: Phenotype Engineering Team

## Context

Retry logic needs to balance between quick recovery and avoiding thundering herd problems when services recover.

## Decision Drivers

- **Fast recovery**: Retry quickly for transient failures
- **Backoff**: Don't overwhelm recovering services
- **Dispersion**: Avoid synchronized retries
- **Simplicity**: Easy to configure and understand

## Options Considered

### Option A: Exponential + Jitter (Selected)

```
delay = min(initialDelay * 2^attempt, maxDelay)
delay = delay * (1 ± jitterFactor)
```

**Pros**:
- Widely adopted (AWS, Google)
- Good dispersion with jitter
- Predictable maximum delay

**Cons**:
- Can grow very quickly
- Not optimal for all patterns

### Option B: Linear Backoff

```
delay = initialDelay + (attempt * increment)
```

**Pros**:
- Simpler to reason about
- Consistent increase

**Cons**:
- Slow to reach long delays
- Less dispersion

### Option C: Decorrelated Jitter (AWS)

```
delay = random(minDelay, previousDelay * 3)
```

**Pros**:
- Better dispersion
- AWS proven pattern

**Cons**:
- More complex
- Less predictable

## Decision

**Implement exponential backoff with equal jitter (±25%).**

## Configuration

```go
type Config struct {
    MaxAttempts  int           // Default: 3
    InitialDelay time.Duration // Default: 100ms
    MaxDelay     time.Duration // Default: 30s
    Multiplier   float64       // Default: 2.0
    Jitter       bool          // Default: true
}
```

## Consequences

### Positive
- Industry standard approach
- Configurable for different use cases
- Good balance of speed and safety

### Negative
- May be too aggressive for some services
- Jitter adds randomness to debugging

## References

- https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/

---

*This retry strategy is used throughout Phenotype services.*
