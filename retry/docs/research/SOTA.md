# Retry Library - State of the Art

> Exponential Backoff Retry Logic for Go - Resilience Patterns

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-04-05

---

## Part I: Resilience Patterns Landscape (2024-2026)

### 1.1 Resilience Pattern Evolution

Distributed systems resilience has evolved from simple retries to sophisticated circuit breakers, bulkheads, and chaos engineering.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Resilience Pattern Evolution                           │
│                                                                             │
│  2000s          2010s           2015s          2020s          2024+         │
│     │             │               │              │              │          │
│     ▼             ▼               ▼              ▼              ▼          │
│  ┌────────┐   ┌────────┐     ┌────────┐    ┌────────┐    ┌────────┐        │
│  │ Retry  │   │ Circuit│     │ Bulkhead│   │ Timeout │   │ Chaos  │        │
│  │        │ → │ Breaker│  →  │        │ →  │ Budget │ →  │ Eng    │        │
│  └────────┘   └────────┘     └────────┘    └────────┘    └────────┘        │
│                                                                             │
│  Exponential   Fail fast       Resource      Adaptive       Antifragile     │
│  backoff       isolation       limits        limits        systems         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Retry Strategy Comparison

| Strategy | Backoff | Jitter | Use Case | Complexity |
|----------|---------|--------|----------|------------|
| **Fixed** | Constant | None | Simple retries | Low |
| **Linear** | Linear increase | Optional | Rate limiting | Low |
| **Exponential** | 2^n multiplier | Recommended | Network calls | Medium |
| **Decorrelated** | Random in range | Built-in | High contention | Medium |
| **Polynomial** | n^k growth | Optional | Bounded backoff | High |

### 1.3 Industry Standards

| Standard | Organization | Specification |
|----------|--------------|---------------|
| **AIA** | Microsoft | Adaptive retry with throttling |
| **AWS SDK** | Amazon | Exponential backoff + jitter |
| **gRPC** | CNCF | Built-in retry with hedging |
| **Resilience4j** | Netflix | Circuit breaker + retry |

---

## Part II: Backoff Algorithms

### 2.1 Exponential Backoff Formula

```
delay = min(
    initialDelay * multiplier^(attempt-1),
    maxDelay
)

With jitter:
delay = delay * (1 + random(-jitterFactor, +jitterFactor))
```

| Attempt | No Jitter | 25% Jitter Range |
|---------|-----------|------------------|
| 1 | 100ms | 75-125ms |
| 2 | 200ms | 150-250ms |
| 3 | 400ms | 300-500ms |
| 4 | 800ms | 600-1000ms |
| 5 | 1600ms | 1200-2000ms |

### 2.2 Jitter Strategies

| Type | Formula | Use Case |
|------|---------|----------|
| **Full** | random(0, delay) | Maximum dispersion |
| **Equal** | delay/2 + random(0, delay/2) | Balanced |
| **Decorrelated** | random(minDelay, delay * 3) | AWS recommended |
| **Decorrelated (New)** | random(minDelay, previous * 3) | Better dispersion |

---

## Part III: Go Implementation

### 3.1 Configuration

```go
type Config struct {
    MaxAttempts  int           // Maximum retry attempts
    InitialDelay time.Duration // First retry delay
    MaxDelay     time.Duration // Maximum delay cap
    Multiplier   float64       // Exponential multiplier (typically 2.0)
    Jitter       bool          // Enable jitter
}

// Sensible defaults
var DefaultConfig = Config{
    MaxAttempts:  3,
    InitialDelay: 100 * time.Millisecond,
    MaxDelay:     30 * time.Second,
    Multiplier:   2.0,
    Jitter:       true,
}
```

### 3.2 Permanent Errors

Some errors should not be retried:

```go
type PermanentError struct {
    Err error
}

// Usage
if err != nil {
    if errors.Is(err, context.DeadlineExceeded) {
        return &retry.PermanentError{Err: err}
    }
}
```

| Error Type | Retry? | Rationale |
|------------|--------|-----------|
| **Timeout** | Yes | Transient network issue |
| **Connection refused** | Yes | Service may be starting |
| **4xx client errors** | No | Request is invalid |
| **5xx server errors** | Yes | Server may recover |
| **Context cancelled** | No | Caller gave up |

---

## Part IV: References

| Resource | URL | Description |
|----------|-----|-------------|
| AWS Retry | https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/ | Best practices |
| gRPC Retry | https://github.com/grpc/proposal/blob/master/A6-client-retries.md | gRPC spec |
| Resilience4j | https://resilience4j.readme.io/ | Java patterns |
| Polly | https://github.com/App-vNext/Polly | .NET resilience |

---

*This document reflects SOTA in retry patterns as of April 2026.*
