# ADR-001: Hexagonal Database Adapter Pattern

**Date**: 2026-04-05  
**Status**: Accepted  
**Deciders**: Phenotype Engineering Team

## Context

Database access should follow hexagonal architecture principles with ports defining the interface and adapters providing concrete implementations.

## Decision Drivers

- **Testability**: Swap real DB for mocks in tests
- **Flexibility**: Switch databases without domain changes
- **Clean architecture**: Domain doesn't depend on DB
- **Multi-database support**: PostgreSQL, MySQL, SQLite

## Options Considered

### Option A: Hexagonal Adapters (Selected)

```go
// Port (in domain/contracts)
type QueryExecutor interface {
    Query(ctx context.Context, query string, args ...any) (Rows, error)
    QueryRow(ctx context.Context, query string, args ...any) Row
    Exec(ctx context.Context, query string, args ...any) (Result, error)
    BeginTx(ctx context.Context, opts TxOptions) (Transaction, error)
}

// Adapter (in infrastructure)
type PostgresAdapter struct {
    db *sql.DB
}
```

**Pros**:
- Clean architecture
- Easy testing
- Database flexibility
- No ORM lock-in

**Cons**:
- More boilerplate
- Manual query writing

### Option B: ORM (GORM)

```go
db.Create(&user)
db.Where("name = ?", "john").First(&user)
```

**Pros**:
- Less boilerplate
- Automatic migrations
- Rich features

**Cons**:
- ORM complexity
- Performance overhead
- Hard to optimize

### Option C: Raw database/sql

Use standard library directly.

**Pros**:
- Standard library
- Maximum control

**Cons**:
- No abstraction
- Hard to test
- Leaks infrastructure

## Decision

**Implement hexagonal adapter pattern with QueryExecutor port and database-specific adapters.**

## Consequences

### Positive
- Clean separation of concerns
- Testable code
- Database flexibility
- Query optimization control

### Negative
- More code to write
- SQL knowledge required

## Implementation

See [adapter/](../adapter/) directory for implementations.

---

*Hexagonal pattern is required for all Phenotype database access.*
