# ADR-001: Generic Repository Port Design

**Date**: 2026-04-05  
**Status**: Accepted  
**Deciders**: Phenotype Engineering Team

## Context

The ports library needs to define repository interfaces that work across different entity types while maintaining type safety. Go 1.18+ generics provide this capability.

## Decision Drivers

- **Type safety**: Avoid interface{} and type assertions
- **Flexibility**: Work with any entity type
- **Testability**: Easy to mock for testing
- **Performance**: Minimal overhead

## Options Considered

### Option A: Generic Repository[T] (Selected)

```go
type Repository[T any] interface {
    Save(ctx context.Context, entity T) (T, error)
    FindByID(ctx context.Context, id string) (T, error)
    Delete(ctx context.Context, id string) error
    FindAll(ctx context.Context) ([]T, error)
}
```

**Pros**:
- Type-safe at compile time
- No reflection overhead
- Clear interfaces
- Easy testing

**Cons**:
- Go 1.18+ required
- More verbose type parameters

### Option B: interface{} Repository

```go
type Repository interface {
    Save(ctx context.Context, entity interface{}) error
    FindByID(ctx context.Context, id string) (interface{}, error)
}
```

**Pros**:
- Works with older Go versions
- Simpler signatures

**Cons**:
- Runtime type assertions
- No compile-time safety
- Reflection overhead

### Option C: Code Generation

Generate type-specific repositories.

**Pros**:
- Optimal performance
- No generics complexity

**Cons**:
- Build step required
- Template maintenance
- Slower iteration

## Decision

**Adopt generic Repository[T] pattern.**

Go 1.18+ is now standard and generics provide the best developer experience.

## Consequences

### Positive
- Type-safe repository operations
- IDE autocomplete support
- Refactoring safety

### Negative
- Requires Go 1.18+
- Learning curve for generics syntax

## References

- https://go.dev/doc/tutorial/generics

---

*This ADR establishes the repository pattern for all Phenotype services.*
