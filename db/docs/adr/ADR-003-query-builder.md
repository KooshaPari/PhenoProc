# ADR-003: Query Builder for Dynamic Queries

**Date**: 2026-04-05  
**Status**: Accepted  
**Deciders**: Phenotype Engineering Team

## Context

Dynamic SQL query construction is error-prone with string concatenation. A type-safe query builder reduces SQL injection risks and improves maintainability.

## Decision Drivers

- **Safety**: Prevent SQL injection
- **Ergonomics**: Easy to read and write
- **Flexibility**: Support dynamic conditions
- **Backend agnostic**: Work with any SQL database

## Options Considered

### Option A: Fluent Query Builder (Selected)

```go
qb := db.NewQueryBuilder("users").
    Select("id", "name", "email").
    Where("status = ?", "active").
    Where("age >= ?", 18).
    OrderBy("created_at", true).
    Limit(100)

query, args := qb.Build()
```

**Pros**:
- Type-safe
- SQL injection safe
- Readable
- Composable

**Cons**:
- Limited to supported patterns
- Learning curve

### Option B: Raw SQL

```go
query := "SELECT * FROM users WHERE status = '" + status + "'"
```

**Pros**:
- Maximum flexibility
- No learning curve

**Cons**:
- SQL injection risk
- Hard to test
- Not composable

### Option C: ORM Query Builder

```go
db.Where("status = ?", "active").Find(&users)
```

**Pros**:
- Rich features
- Automatic type mapping

**Cons**:
- ORM lock-in
- Magic behavior
- Performance overhead

## Decision

**Implement fluent query builder for dynamic SQL construction.**

## Consequences

### Positive
- SQL injection protection
- Readable query construction
- Testable code
- No ORM dependency

### Negative
- Limited feature set
- Manual result mapping

## Implementation

See [query.go](../../query.go) for query builder implementation.

---

*Query builder is used for dynamic queries; raw SQL acceptable for static queries.*
