# ADR-003: Registry Lifecycle Hooks

**Date**: 2026-04-05  
**Status**: Accepted  
**Deciders**: Phenotype Engineering Team

## Context

Applications need to react to registry changes for metrics, logging, and cleanup. A hook interface enables these use cases without coupling.

## Decision Drivers

- **Observability**: Track registry changes
- **Extensibility**: Custom behavior on changes
- **Decoupling**: Registry doesn't know about observers
- **Testing**: Easy to verify interactions

## Options Considered

### Option A: Hook Interface (Selected)

```go
type Hook[K comparable, V any] interface {
    OnRegister(ownerID string, key K, value V)
    OnUnregister(ownerID string)
}
```

**Pros**:
- Clean interface
- Type-safe
- Testable
- Optional (nil is OK)

**Cons**:
- Single hook (need multiplexing for multiple)

### Option B: Channel-based

```go
type Event struct {
    Type     EventType
    OwnerID  string
    Key      interface{}
    Value    interface{}
}

events chan Event
```

**Pros**:
- Multiple subscribers
- Go-idiomatic

**Cons**:
- Buffer management
- Goroutine complexity
- Blocking concerns

### Option C: Callback Functions

```go
type Registry struct {
    OnRegister   func(ownerID string, key, value interface{})
    OnUnregister func(ownerID string)
}
```

**Pros**:
- Simple
- Flexible

**Cons**:
- Less structured
- Harder to compose

## Decision

**Implement Hook interface with optional multiplexing support.**

## Consequences

### Positive
- Clean extension point
- Easy testing with mocks
- Metrics/logging integration simple

### Negative
- Need multiplexer for multiple observers
- Hook failures can affect registry operations

## Implementation

```go
// Multiplexer for multiple hooks
type Multiplexer[K comparable, V any] struct {
    hooks []Hook[K, V]
}

func (m *Multiplexer[K, V]) OnRegister(ownerID string, key K, value V) {
    for _, h := range m.hooks {
        h.OnRegister(ownerID, key, value)
    }
}
```

---

*Hooks are used for metrics and auditing throughout Phenotype.*
