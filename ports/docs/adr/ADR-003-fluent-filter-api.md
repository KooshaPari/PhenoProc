# ADR-003: Fluent Filter API Design

**Date**: 2026-04-05  
**Status**: Accepted  
**Deciders**: Phenotype Engineering Team

## Context

The QueryRepository port needs a flexible way to specify query filters that can be adapted to different database backends (SQL, MongoDB, Elasticsearch).

## Decision Drivers

- **Expressiveness**: Support complex queries
- **Type safety**: Valid operators at compile time
- **Backend agnostic**: Works with any database
- **Ergonomics**: Easy to read and write

## Options Considered

### Option A: Fluent Builder (Selected)

```go
filter := ports.NewFilter().
    WithCondition("status", ports.OpEq, "active").
    WithCondition("age", ports.OpGte, 18).
    WithLimit(100).
    WithOffset(0)
```

**Pros**:
- Readable chain
- IDE autocomplete
- Type-safe operators
- Immutable operations

**Cons**:
- Verbose for simple queries
- Builder overhead

### Option B: Raw Query String

```go
filter := ports.RawFilter("status = 'active' AND age >= 18")
```

**Pros**:
- Maximum flexibility
- Familiar syntax

**Cons**:
- Injection risk
- Backend-specific
- No type safety

### Option C: Map-based

```go
filter := ports.MapFilter{
    "status": "active",
    "age": map[string]interface{}{">=": 18},
}
```

**Pros**:
- Simple data structure
- JSON serializable

**Cons**:
- Runtime errors
- Operator discovery difficult

## Decision

**Implement fluent builder pattern for filter construction.**

## Consequences

### Positive
- Type-safe query building
- Backend-agnostic representation
- Testable and mockable

### Negative
- More code to implement adapters
- Learning curve for API

## Implementation

See [port.go](../../port.go) for the Filter type implementation.

---

*Fluent API pattern is used throughout Phenotype query interfaces.*
