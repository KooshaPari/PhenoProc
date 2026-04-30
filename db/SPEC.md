# Database Library Specification

> Database Utilities and Adapters for Go - Persistence Layer

**Version**: 1.0  
**Status**: Production  
**Last Updated**: 2026-04-05

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Connection Pool](#3-connection-pool)
4. [Query Builder](#4-query-builder)
5. [Adapters](#5-adapters)
6. [Indexes](#6-indexes)
7. [Appendices](#7-appendices)

---

## 1. Overview

### 1.1 Purpose

The database library provides connection pooling, query building, and hexagonal architecture adapters for Go applications. It enables:

- **Connection management**: Configurable connection pooling
- **Query building**: Type-safe SQL construction
- **Hexagonal adapters**: Database-agnostic domain layer
- **Index management**: Database index definitions
- **Health checks**: Connection monitoring

### 1.2 Goals

| Goal | Priority | Status |
|------|----------|--------|
| Connection pooling | P0 | ✅ Implemented |
| Query builder | P0 | ✅ Implemented |
| Hexagonal adapters | P0 | ✅ Implemented |
| Multi-database support | P1 | ✅ Implemented |
| Index definitions | P1 | ✅ Implemented |

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Adapter** | Database-specific implementation of QueryExecutor |
| **Pool** | Connection pool for database connections |
| **Query builder** | Fluent API for SQL construction |
| **Index** | Database index definition |

---

## 2. Architecture

### 2.1 Hexagonal Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Database Architecture                                  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    Domain Layer (No DB dependencies)                 │   │
│  │                                                                        │   │
│  │   ┌──────────────────────────────────────────────────────────────┐    │   │
│  │   │              QueryExecutor Port (Interface)                   │    │   │
│  │   │                                                              │    │   │
│  │   │  type QueryExecutor interface {                              │    │   │
│  │   │      Query(ctx context.Context, query string, args...any)    │    │   │
│  │   │      QueryRow(ctx context.Context, query string, args...any) │    │   │
│  │   │      Exec(ctx context.Context, query string, args...any)       │    │   │
│  │   │      BeginTx(ctx context.Context, opts TxOptions)              │    │   │
│  │   │      Ping(ctx context.Context) error                           │    │   │
│  │   │      Stats() PoolStats                                         │    │   │
│  │   │  }                                                         │    │   │
│  │   └──────────────────────────────────────────────────────────────┘    │   │
│  │                              ▲                                         │   │
│  └──────────────────────────────┼─────────────────────────────────────────┘   │
│                                 │                                              │
│                    ═════════════╧═════════════                                   │
│                                 │                                              │
│  ┌──────────────────────────────┼─────────────────────────────────────────┐   │
│  │                    Infrastructure Layer                                  │   │
│  │                            │                                            │   │
│  │   ┌────────────────────────┴────────────────────────┐                   │   │
│  │   │              Database Adapters                 │                   │   │
│  │   │                                                │                   │   │
│  │   │  ┌──────────────┐  ┌──────────────┐  ┌──────┴──────┐             │   │
│  │   │  │   Postgres   │  │    MySQL     │  │   SQLite    │             │   │
│  │   │  │   Adapter    │  │   Adapter    │  │   Adapter   │             │   │
│  │   │  └──────────────┘  └──────────────┘  └─────────────┘             │   │
│  │   │                                                │                   │   │
│  │   └────────────────────────────────────────────────┘                   │   │
│  │                                                                        │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Connection Pool

### 3.1 Pool Configuration

```go
type PoolConfig struct {
    MaxOpenConns    int           // Maximum open connections (default: 25)
    MaxIdleConns    int           // Maximum idle connections (default: 5)
    ConnMaxLifetime time.Duration // Connection max lifetime (default: 5m)
    ConnMaxIdleTime time.Duration // Connection max idle time (default: 1m)
    DialTimeout     time.Duration // Connection dial timeout (default: 5s)
    QueryTimeout    time.Duration // Query timeout (default: 30s)
}

var DefaultPoolConfig = PoolConfig{
    MaxOpenConns:    25,
    MaxIdleConns:    5,
    ConnMaxLifetime: 5 * time.Minute,
    ConnMaxIdleTime: 1 * time.Minute,
    DialTimeout:     5 * time.Second,
    QueryTimeout:    30 * time.Second,
}
```

### 3.2 Pool Management

```go
// Configure pool
db, _ := sql.Open("postgres", dsn)
err := db.ConfigurePool(db, db.DefaultPoolConfig)

// Get pool stats
stats := db.GetPoolStats(db)
fmt.Printf("Open: %d, Idle: %d, InUse: %d\n", 
    stats.OpenConnections, stats.IdleConnections, stats.InUseConnections)

// Health check
if err := db.HealthCheck(ctx, db); err != nil {
    log.Fatal("Database unhealthy:", err)
}
```

---

## 4. Query Builder

### 4.1 Fluent API

```go
// Build a SELECT query
qb := db.NewQueryBuilder("users").
    Select("id", "name", "email").
    Where("status = ?", "active").
    Where("age >= ?", 18).
    OrderBy("created_at", true).
    Limit(100).
    Offset(0)

query, args := qb.Build()
// SELECT id, name, email FROM users WHERE status = ? AND age >= ? 
// ORDER BY created_at DESC LIMIT 100 OFFSET 0
// args: ["active", 18]
```

### 4.2 Pagination

```go
// Offset-based pagination
qb := db.NewQueryBuilder("products").
    Select("*").
    Paginate(page, pageSize) // page 1, 20 per page

// Get count for pagination metadata
countQuery, countArgs := qb.Count()
```

---

## 5. Adapters

### 5.1 PostgreSQL Adapter

```go
import "github.com/KooshaPari/phenotype-go-kit/db/adapter"

// Create adapter
dsn := "postgres://user:pass@localhost/db?sslmode=disable"
config := outbound.PoolConfig{...}

pgAdapter, err := adapter.NewPostgresAdapter(dsn, config)
if err != nil {
    log.Fatal(err)
}
defer pgAdapter.Close()

// Use adapter
rows, err := pgAdapter.Query(ctx, "SELECT * FROM users WHERE active = true")
```

### 5.2 MySQL Adapter

```go
// Create adapter
dsn := "user:pass@tcp(localhost:3306)/db"
mysqlAdapter, err := adapter.NewMySQLAdapter(dsn, config)
```

### 5.3 SQLite Adapter

```go
// Create adapter
sqliteAdapter, err := adapter.NewSQLiteAdapter("file:app.db", config)
```

---

## 6. Indexes

### 6.1 Index Definitions

```go
// Define indexes
var Indexes = []db.IndexDefinition{
    {
        Name:    "idx_users_email",
        Table:   "users",
        Columns: []string{"email"},
        Unique:  true,
    },
    {
        Name:    "idx_users_status",
        Table:   "users",
        Columns: []string{"status"},
    },
    {
        Name:    "idx_orders_user_id",
        Table:   "orders",
        Columns: []string{"user_id"},
    },
}

// Generate SQL
for _, idx := range db.Indexes {
    sql := idx.GenerateCreateIndexSQL()
    db.Exec(sql)
}
```

---

## 7. Appendices

### 7.1 API Reference

See [pool.go](../pool.go), [query.go](../query.go), and [adapter/](../adapter/) for complete API documentation.

### 7.2 Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-05 | Initial release |

---

*This specification defines the database library v1.0 for Phenotype Go Kit.*
