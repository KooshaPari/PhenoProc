# ADR-001: Rule-Based Validation API

**Date**: 2026-04-05  
**Status**: Accepted  
**Deciders**: Phenotype Engineering Team

## Context

The validation library needs to provide a flexible, extensible way to validate data without requiring struct tags or code generation.

## Decision Drivers

- **Flexibility**: Support runtime rule composition
- **Extensibility**: Easy to add custom rules
- **Testability**: Rules are testable units
- **Composability**: Combine rules for complex validation

## Options Considered

### Option A: Rule-Based (Selected)

```go
type Rule struct {
    Name     string
    Message  string
    Validate func(interface{}) bool
}

validator.AddRule("email", validation.Email)
```

**Pros**:
- Runtime rule composition
- Easy custom rules
- Testable units
- No struct modification needed

**Cons**:
- Field name strings (not type-safe)
- Runtime overhead

### Option B: Struct Tags

```go
type User struct {
    Email string `validate:"email"`
}
```

**Pros**:
- Declarative
- Familiar pattern
- IDE support

**Cons**:
- Requires struct access
- Tag parsing overhead
- Less flexible at runtime

### Option C: Code Generation

Generate validation code from schema.

**Pros**:
- Optimal performance
- Compile-time checking

**Cons**:
- Build step complexity
- Template maintenance

## Decision

**Use rule-based validation with predefined rules and custom rule support.**

## Consequences

### Positive
- Maximum flexibility
- Easy testing
- Clear error messages
- Composable rules

### Negative
- String-based field names
- Runtime reflection

## Implementation

See [validator.go](../../validator.go) for rule implementations.

---

*Rule-based validation is the primary pattern for Phenotype services.*
