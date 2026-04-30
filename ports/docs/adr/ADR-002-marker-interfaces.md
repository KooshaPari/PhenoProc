# ADR-002: Marker Interface for Port Types

**Date**: 2026-04-05  
**Status**: Accepted  
**Deciders**: Phenotype Engineering Team

## Context

To enforce architectural boundaries in hexagonal architecture, we need a way to distinguish input ports (driving) from output ports (driven) at the type level.

## Decision Drivers

- **Compile-time enforcement**: Prevent incorrect port usage
- **Documentation**: Self-documenting code
- **Tooling**: Enable linting/architecture checks

## Options Considered

### Option A: Marker Interfaces (Selected)

```go
type InputPort interface {
    isInputPort()
}

type OutputPort interface {
    isOutputPort()
}
```

**Pros**:
- Compile-time type checking
- Zero runtime overhead
- Clear intent
- Extensible

**Cons**:
- Unexported method is unusual pattern

### Option B: Struct Tags

```go
type MyPort struct {
    // port: input
}
```

**Pros**:
- Familiar syntax
- Human readable

**Cons**:
- Runtime reflection required
- No compile-time checking
- Tooling complexity

### Option C: Naming Convention

```go
type InputUserPort interface {}
type OutputUserPort interface {}
```

**Pros**:
- Simple
- No code changes needed

**Cons**:
- No enforcement
- Inconsistent naming risk

## Decision

**Use unexported marker methods for port type distinction.**

## Consequences

### Positive
- Strong compile-time guarantees
- Clean implementation
- Extensible to additional port types

### Negative
- Unfamiliar pattern for some developers
- Requires documentation

## References

- https://go.dev/doc/effective_go#interfaces

---

*Marker interfaces are used throughout the Phenotype ports library.*
