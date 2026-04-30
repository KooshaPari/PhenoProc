# ADR-002: Permanent Error Distinction

**Date**: 2026-04-05  
**Status**: Accepted  
**Deciders**: Phenotype Engineering Team

## Context

Not all errors should trigger retries. Some errors indicate permanent failures that will never succeed on retry (e.g., invalid credentials, bad request format).

## Decision Drivers

- **Efficiency**: Don't retry hopeless cases
- **Latency**: Fail fast on permanent errors
- **Resource conservation**: Save network/compute
- **Correctness**: Respect client errors

## Options Considered

### Option A: PermanentError Type (Selected)

```go
type PermanentError struct {
    Err error
}

func (e *PermanentError) Error() string { return e.Err.Error() }
func (e *PermanentError) Unwrap() error { return e.Err }

func IsPermanent(err error) bool {
    var pe *PermanentError
    return errors.As(err, &pe)
}
```

**Pros**:
- Explicit opt-out of retries
- Wrappable (preserves error chain)
- Type-safe

**Cons**:
- Requires error wrapping discipline

### Option B: Error Type Whitelist

```go
var retryableErrors = map[error]bool{
    io.ErrUnexpectedEOF: true,
    syscall.ECONNRESET: true,
}
```

**Pros**:
- Automatic for known errors
- No code changes in callers

**Cons**:
- Maintaining list is tedious
- Can't cover all cases

### Option C: Context Cancellation Only

Only stop retrying on context cancellation.

**Pros**:
- Very simple

**Cons**:
- Retries pointless errors
- Wastes resources

## Decision

**Use PermanentError wrapper for non-retryable errors.**

## Usage

```go
func doSomething() error {
    if err := validate(); err != nil {
        return &retry.PermanentError{Err: err}
    }
    // ... retryable work
}
```

## Consequences

### Positive
- Efficient retry behavior
- Clear error semantics
- Compatible with errors.Is/As

### Negative
- Developers must consciously mark errors
- Risk of missing retryable errors

---

*PermanentError is used throughout Phenotype for business errors.*
