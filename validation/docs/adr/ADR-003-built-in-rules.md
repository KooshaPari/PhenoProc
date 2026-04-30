# ADR-003: Built-in Validation Rules

**Date**: 2026-04-05  
**Status**: Accepted  
**Deciders**: Phenotype Engineering Team

## Context

The validation library should provide common validation rules out of the box while allowing custom rule creation.

## Decision Drivers

- **Coverage**: Common validation patterns included
- **Consistency**: Standard rules across services
- **Security**: OWASP-aligned validations
- **Performance**: Optimized rule implementations

## Options Considered

### Option A: Rich Built-in Set (Selected)

Provide common rules as package-level variables:

```go
var (
    Required = Rule{...}
    Email    = Rule{...}
)

func MinLength(n int) Rule
func MaxLength(n int) Rule
func Min(n int) Rule
func Max(n int) Rule
func Pattern(p string, msg string) Rule
func In(values ...string) Rule
```

**Pros**:
- Ready to use
- Consistent across services
- Optimized implementations

**Cons**:
- Library bloat risk
- Opinionated choices

### Option B: Minimal Core + Extensions

Only basic rules in core, extensions in separate packages.

**Pros**:
- Smaller core
- Flexible

**Cons**:
- Fragmentation
- Dependency management

### Option C: Plugin System

Dynamic rule loading.

**Pros**:
- Ultimate flexibility

**Cons**:
- Complexity
- Security risks

## Decision

**Provide comprehensive built-in rules with factory functions for parameterized rules.**

## Included Rules

| Rule | Purpose |
|------|---------|
| Required | Non-empty values |
| Email | Email format validation |
| MinLength(n) | String length minimum |
| MaxLength(n) | String length maximum |
| Min(n) | Numeric minimum |
| Max(n) | Numeric maximum |
| Pattern(re, msg) | Regex validation |
| In(values...) | Whitelist validation |

## Consequences

### Positive
- Common validations available immediately
- Consistent across services
- Security-reviewed patterns

### Negative
- Library size
- Maintenance burden

---

*Built-in rules are reviewed quarterly for security updates.*
