# ADR-002: Validation Result Structure

**Date**: 2026-04-05  
**Status**: Accepted  
**Deciders**: Phenotype Engineering Team

## Context

Validation errors need to be returned in a format that supports multiple field errors and is easy to convert to HTTP responses.

## Decision Drivers

- **Multiple errors**: Report all validation failures
- **Field mapping**: Associate errors with fields
- **HTTP friendly**: Easy to convert to 400 response
- **Human readable**: Clear error messages

## Options Considered

### Option A: Map[string][]string (Selected)

```go
errors, valid := validator.Validate(data)
// errors: map[string][]string{"email": {"is required", "must be valid email"}}
```

**Pros**:
- Multiple errors per field
- Easy JSON serialization
- Direct HTTP response mapping

**Cons**:
- Loss of error type information
- String-based only

### Option B: Error Interface

```go
if err := validator.Validate(data); err != nil {
    // Custom error type with fields
}
```

**Pros**:
- Standard error interface
- Can implement Unwrap

**Cons**:
- Single error (unless wrapped)
- Complex error inspection

### Option C: ValidationError Struct

```go
type ValidationError struct {
    Field   string
    Code    string
    Message string
}
```

**Pros**:
- Structured data
- Error codes for i18n

**Cons**:
- Custom type everywhere
- Slices of errors

## Decision

**Use map[string][]string for field errors with boolean valid flag.**

## Consequences

### Positive
- Simple and clear
- HTTP API friendly
- Multiple errors per field

### Negative
- Limited error metadata
- String-based only

## Implementation

```go
func (v *Validator) Validate(data interface{}) (map[string][]string, bool) {
    errors := make(map[string][]string)
    // ... validation logic
    return errors, len(errors) == 0
}
```

---

*Validation result format is used across all Phenotype APIs.*
