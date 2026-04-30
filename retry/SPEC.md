# Retry Library Specification

> Exponential Backoff Retry Logic for Go - Resilience Patterns

**Version**: 1.0  
**Status**: Production  
**Last Updated**: 2026-04-05

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Configuration](#3-configuration)
4. [Usage Patterns](#4-usage-patterns)
5. [Performance](#5-performance)
6. [Appendices](#6-appendices)

---

## 1. Overview

### 1.1 Purpose

The retry library provides configurable retry logic with exponential backoff for Go applications. It enables:

- **Automatic retries**: Transparent failure recovery
- **Exponential backoff**: Prevents thundering herd
- **Jitter**: Distributes retry timing
- **Context awareness**: Respects cancellation
- **Permanent errors**: Distinguish non-retryable failures

### 1.2 Goals

| Goal | Priority | Status |
|------|----------|--------|
| Exponential backoff | P0 | ✅ Implemented |
| Jitter support | P0 | ✅ Implemented |
| Context cancellation | P0 | ✅ Implemented |
| Permanent errors | P1 | ✅ Implemented |
| Result-returning functions | P1 | ✅ Implemented |

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Attempt** | Single execution of the function |
| **Backoff** | Delay between attempts |
| **Jitter** | Random variation in backoff |
| **Permanent error** | Error that should not trigger retry |
| **Retryable error** | Error that may succeed on retry |

---

## 2. Architecture

### 2.1 Retry Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Retry Flow Diagram                                   │
│                                                                             │
│  ┌──────────────┐                                                           │
│  │   Start      │                                                           │
│  └──────┬───────┘                                                           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────┐     ┌──────────┐                                         │
│  │ Attempt = 1  │────▶│ Execute  │                                         │
│  └──────────────┘     └────┬─────┘                                         │
│                            │                                               │
│                    ┌─────────┴─────────┐                                     │
│                    │                   │                                     │
│                    ▼                   ▼                                     │
│              ┌──────────┐       ┌──────────┐                               │
│              │ Success  │       │  Error   │                               │
│              └────┬─────┘       └────┬─────┘                               │
│                   │                   │                                     │
│                   ▼                   ▼                                     │
│              ┌──────────┐       ┌──────────┐                               │
│              │  Return  │       │Permanent?│                               │
│              │  nil     │       └────┬─────┘                               │
│              └──────────┘              │                                     │
│                             ┌────────┴────────┐                            │
│                             │                 │                            │
│                             ▼                 ▼                            │
│                       ┌──────────┐      ┌──────────┐                       │
│                       │  Return  │      │ Max      │                       │
│                       │  Error   │      │ Attempts?│                       │
│                       └──────────┘      └────┬─────┘                       │
│                                    ┌─────────┴─────────┐                   │
│                                    │                   │                   │
│                                    ▼                   ▼                   │
│                              ┌──────────┐      ┌──────────┐               │
│                              │  Return  │      │  Delay   │               │
│                              │  Error   │      │  & Retry │               │
│                              └──────────┘      └────┬─────┘               │
│                                                      │                     │
│                                                      ▼                     │
│                                               ┌──────────┐               │
│                                               │ Attempt++ │               │
│                                               └──────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Backoff Calculation

```
delay = min(initialDelay * multiplier^(attempt-1), maxDelay)

With jitter (±25%):
delay = delay * (1 + random(-0.25, +0.25))

Example with defaults:
  Attempt 1: 100ms * 2^0 = 100ms
  Attempt 2: 100ms * 2^1 = 200ms
  Attempt 3: 100ms * 2^2 = 400ms
  Attempt 4: 100ms * 2^3 = 800ms
  Attempt 5: 100ms * 2^4 = 1600ms (clamped to 30s max)
```

---

## 3. Configuration

### 3.1 Config Structure

```go
type Config struct {
    MaxAttempts  int           // Maximum number of attempts (default: 3)
    InitialDelay time.Duration // First retry delay (default: 100ms)
    MaxDelay     time.Duration // Maximum delay cap (default: 30s)
    Multiplier   float64       // Exponential multiplier (default: 2.0)
    Jitter       bool          // Enable jitter (default: true)
}

// Default configuration
var DefaultConfig = Config{
    MaxAttempts:  3,
    InitialDelay: 100 * time.Millisecond,
    MaxDelay:     30 * time.Second,
    Multiplier:   2.0,
    Jitter:       true,
}
```

### 3.2 Configuration Presets

| Preset | Use Case | MaxAttempts | InitialDelay | MaxDelay |
|--------|----------|-------------|--------------|----------|
| **Default** | General use | 3 | 100ms | 30s |
| **Aggressive** | Fast recovery | 5 | 50ms | 5s |
| **Conservative** | Rate-limited APIs | 3 | 1s | 60s |
| **Database** | DB operations | 5 | 100ms | 30s |
| **Network** | Network calls | 5 | 200ms | 60s |

---

## 4. Usage Patterns

### 4.1 Basic Retry

```go
package main

import (
    "context"
    "github.com/KooshaPari/phenotype-go-kit/retry"
)

func main() {
    ctx := context.Background()
    
    // Simple retry with defaults
    err := retry.Do(ctx, retry.DefaultConfig, func(ctx context.Context) error {
        return callExternalAPI(ctx)
    })
    
    if err != nil {
        log.Fatalf("Failed after retries: %v", err)
    }
}
```

### 4.2 Custom Configuration

```go
// Custom retry configuration
cfg := retry.Config{
    MaxAttempts:  5,
    InitialDelay: 200 * time.Millisecond,
    MaxDelay:     1 * time.Minute,
    Multiplier:   2.0,
    Jitter:       true,
}

err := retry.Do(ctx, cfg, func(ctx context.Context) error {
    return databaseQuery(ctx)
})
```

### 4.3 Retrying with Result

```go
// Retry function that returns a value
result, err := retry.DoWithResult(ctx, cfg, func() (interface{}, error) {
    return fetchUser(ctx, userID)
})

if err != nil {
    return nil, err
}

user := result.(User)
```

### 4.4 Permanent Errors

```go
// Mark errors as non-retryable
err := retry.Do(ctx, cfg, func(ctx context.Context) error {
    resp, err := api.CreateUser(ctx, req)
    if err != nil {
        // Don't retry on 4xx errors
        if isClientError(err) {
            return &retry.PermanentError{Err: err}
        }
        return err // Will retry on 5xx
    }
    return nil
})
```

### 4.5 Context Cancellation

```go
// Respect timeout
deadline := time.Now().Add(30 * time.Second)
ctx, cancel := context.WithDeadline(context.Background(), deadline)
defer cancel()

err := retry.Do(ctx, cfg, func(ctx context.Context) error {
    return longRunningOperation(ctx)
})
```

### 4.6 WithRetry Wrapper

```go
// Create a reusable retry wrapper
withRetry := retry.WithRetry(cfg)

// Use for multiple operations
fetchUser := withRetry(func(ctx context.Context) error {
    return fetchUserFromAPI(ctx, id)
})

fetchOrder := withRetry(func(ctx context.Context) error {
    return fetchOrderFromAPI(ctx, id)
})

err := fetchUser(ctx)
```

---

## 5. Performance

### 5.1 Overhead

| Aspect | Impact |
|--------|--------|
| **Function call** | Negligible |
| **Jitter calculation** | ~100ns |
| **Timer creation** | ~1μs |
| **Context check** | ~10ns |

### 5.2 Timing Examples

| Config | Attempt 1 | Attempt 2 | Attempt 3 | Total (success) |
|--------|-----------|-----------|-----------|-----------------|
| Default | 100ms | 200ms | 400ms | ~700ms |
| Aggressive | 50ms | 100ms | 200ms | ~350ms |
| Conservative | 1s | 2s | 4s | ~7s |

---

## 6. Appendices

### 6.1 API Reference

See [backoff.go](../backoff.go) for complete API documentation.

### 6.2 Error Types

```go
// PermanentError wraps an error that should not be retried
type PermanentError struct {
    Err error
}

func (e *PermanentError) Error() string
func (e *PermanentError) Unwrap() error

// IsPermanent checks if an error is permanent
func IsPermanent(err error) bool
```

### 6.3 Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-05 | Initial release |

---

*This specification defines the retry library v1.0 for Phenotype Go Kit.*
