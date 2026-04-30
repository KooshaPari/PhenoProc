# ADR-002: Generic Key-Value Registry

**Date**: 2026-04-05  
**Status**: Accepted  
**Deciders**: Phenotype Engineering Team

## Context

The registry must support different key and value types for various use cases (string keys, int values, struct values, etc.).

## Decision Drivers

- **Flexibility**: Work with any comparable key type
- **Type safety**: Values typed to use case
- **Performance**: Avoid boxing/unboxing
- **Simplicity**: Single implementation

## Options Considered

### Option A: Generic Registry[K, V] (Selected)

```go
type Registry[K comparable, V any] struct {
    entries map[K]*entry[V]
}
```

**Pros**:
- Type-safe keys and values
- No interface{} overhead
- Compile-time checking

**Cons**:
- Go 1.18+ required
- Type parameters add verbosity

### Option B: String-Only Keys

```go
type Registry[V any] struct {
    entries map[string]*entry[V]
}
```

**Pros**:
- Simpler API
- Keys are naturally serializable

**Cons**:
- Less flexible
- Key collision risk

### Option C: interface{} Values

```go
type Registry struct {
    entries map[string]interface{}
}
```

**Pros**:
- Simplest API
- Works with any value

**Cons**:
- Type assertions required
- Runtime overhead
- No compile-time safety

## Decision

**Use generic Registry[K comparable, V any] design.**

## Consequences

### Positive
- Full type safety
- Optimal performance
- Flexible key types

### Negative
- Requires Go 1.18+
- Some complex type signatures

---

*Generic registry is used throughout Phenotype services.*
