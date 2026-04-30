# circuit Specification

**Version:** 1.0.0  
**Status:** Stable  
**Date:** 2026-04-05  

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [State Machine](#state-machine)
4. [API Reference](#api-reference)
5. [Implementation](#implementation)
6. [Examples](#examples)
7. [Appendices](#appendices)

---

## Overview

The `circuit` library implements the Circuit Breaker pattern for fault tolerance in distributed systems.

### Purpose

- Prevent cascade failures
- Fail fast when dependencies are unhealthy
- Automatic recovery detection

---

## Architecture

### State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Circuit Breaker States                               │
│                                                                             │
│                             ┌──────────────┐                                 │
│                             │              │                                 │
│              ┌───────────────▶│   CLOSED     │◀─────────────────────────┐    │
│              │   success < threshold      │   (Normal operation)     │    │
│              │                │              │                          │    │
│              │                └──────┬───────┘                          │    │
│              │                       │                                  │    │
│              │          failures >= FailureThreshold                   │    │
│              │                       │                                  │    │
│              │                       ▼                                  │    │
│              │              ┌──────────────┐     timeout expires       │    │
│              │              │              │───────────────────────────┘    │
│              │              │     OPEN     │                                │
│              │   success >= │   (Failing)  │                                │
│              │   SuccessThreshold│              │                                │
│              └───────────────│              │                                │
│                             └──────┬───────┘                                │
│                                    │                                        │
│                                    │ timeout expires                        │
│                                    ▼                                        │
│                             ┌──────────────┐                                │
│                             │              │                                │
│                             │   HALF-OPEN  │                                │
│                             │  (Testing)   │                                │
│                             └──────────────┘                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## API Reference

### Breaker

```go
type Config struct {
    FailureThreshold int           // Open after N failures (default: 5)
    SuccessThreshold int           // Close after N successes (default: 2)
    Timeout          time.Duration // Open -> Half-Open timeout (default: 30s)
    RequestTimeout   time.Duration // Per-request timeout (default: 10s)
}

type Breaker struct {
    name   string
    config Config
    state  State
    // ... internal fields
}

func New(name string, cfg Config) *Breaker

func (cb *Breaker) Execute(ctx context.Context, fn func() error) error
func (cb *Breaker) State() State
func (cb *Breaker) Reset()
func (cb *Breaker) GetMetrics() Metrics
```

### MultiBreaker

```go
type MultiBreaker struct {
    breakers map[string]*Breaker
    mu       sync.RWMutex
}

func NewMultiBreaker() *MultiBreaker
func (mb *MultiBreaker) Get(name string, cfg Config) *Breaker
```

### Errors

```go
var (
    ErrCircuitOpen     = errors.New("circuit breaker is open")
    ErrCircuitHalfOpen = errors.New("circuit breaker is half-open")
)
```

---

## Implementation

### State Transitions

```go
func (cb *Breaker) Execute(ctx context.Context, fn func() error) error {
    cb.mu.Lock()
    
    switch cb.state {
    case StateOpen:
        if time.Since(cb.lastFailTime) > cb.config.Timeout {
            cb.state = StateHalfOpen
            cb.success = 0
        } else {
            cb.mu.Unlock()
            return ErrCircuitOpen
        }
        
    case StateHalfOpen:
        // Allow request through for testing
    }
    
    cb.mu.Unlock()
    
    // Execute with timeout
    runCtx, cancel := context.WithTimeout(ctx, cb.config.RequestTimeout)
    defer cancel()
    
    result := make(chan error, 1)
    go func() {
        result <- fn()
    }()
    
    select {
    case <-runCtx.Done():
        cb.recordFailure()
        return runCtx.Err()
    case err := <-result:
        if err != nil {
            cb.recordFailure()
            return err
        }
        cb.recordSuccess()
        return nil
    }
}
```

---

## Examples

### Basic Usage

```go
package main

import (
    "context"
    "errors"
    "fmt"
    "time"
    
    "github.com/coder/circuit"
)

func main() {
    cb := circuit.New("api-call", circuit.Config{
        FailureThreshold: 3,
        SuccessThreshold: 2,
        Timeout:          30 * time.Second,
    })
    
    for i := 0; i < 10; i++ {
        err := cb.Execute(context.Background(), func() error {
            return callExternalAPI()
        })
        
        if errors.Is(err, circuit.ErrCircuitOpen) {
            fmt.Println("Circuit open - failing fast")
            time.Sleep(1 * time.Second)
            continue
        }
        
        if err != nil {
            fmt.Printf("Request failed: %v\n", err)
        } else {
            fmt.Println("Request succeeded")
        }
    }
}

func callExternalAPI() error {
    // Simulate API call
    return nil
}
```

### HTTP Client Integration

```go
type ResilientClient struct {
    client  *http.Client
    breaker *circuit.Breaker
}

func (c *ResilientClient) Do(req *http.Request) (*http.Response, error) {
    var resp *http.Response
    var err error
    
    execErr := c.breaker.Execute(req.Context(), func() error {
        resp, err = c.client.Do(req)
        if err != nil {
            return err
        }
        if resp.StatusCode >= 500 {
            return fmt.Errorf("server error: %d", resp.StatusCode)
        }
        return nil
    })
    
    if execErr == circuit.ErrCircuitOpen {
        return nil, fmt.Errorf("service unavailable")
    }
    
    return resp, err
}
```

### Database Integration

```go
type ResilientDB struct {
    db      *sql.DB
    breaker *circuit.Breaker
}

func (r *ResilientDB) QueryContext(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
    var rows *sql.Rows
    var err error
    
    execErr := r.breaker.Execute(ctx, func() error {
        rows, err = r.db.QueryContext(ctx, query, args...)
        return err
    })
    
    if execErr == circuit.ErrCircuitOpen {
        return nil, fmt.Errorf("database unavailable")
    }
    
    return rows, err
}
```

---

## Appendices

### Appendix A: State Reference

| State | Description | Requests Allowed |
|-------|-------------|------------------|
| Closed | Normal operation | All |
| Open | Failure threshold reached | None (fast fail) |
| Half-Open | Testing recovery | Limited (test requests) |

### Appendix B: Configuration Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| FailureThreshold | 5 | Consecutive failures to open |
| SuccessThreshold | 2 | Consecutive successes to close |
| Timeout | 30s | Time in Open before Half-Open |
| RequestTimeout | 10s | Per-request timeout |

---

*Specification Version: 1.0.0*  
*Last Updated: 2026-04-05*
