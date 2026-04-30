# Database Library - State of the Art

> Database Utilities and Adapters for Go - Persistence Layer

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-04-05

---

## Part I: Database Landscape (2024-2026)

### 1.1 Database Paradigm Evolution

Database technologies have evolved from monolithic RDBMS to polyglot persistence with specialized databases for different use cases.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Database Evolution                                     │
│                                                                             │
│  RDBMS ────► NoSQL ────► NewSQL ────► Cloud ────► Serverless ────► Edge   │
│                                                                             │
│  1970s       2009        2013        2015        2018         2022+         │
│    │          │           │           │           │            │            │
│    ▼          ▼           ▼           ▼           ▼            ▼            │
│  ┌────┐    ┌────┐      ┌────┐      ┌────┐      ┌────┐       ┌────┐       │
│  │Oral│    │Mong│      │Cock│      │Auro│      │Aurora│      │SQLi│       │
│  │cle │    │oDB │      │roach│      │ra  │      │Serve│       │te │       │
│  │    │    │    │      │DB  │      │    │      │rless│       │    │       │
│  └────┘    └────┘      └────┘      └────┘      └────┘       └────┘       │
│                                                                             │
│  ACID        Horizontal   Distributed  Managed    Auto-scale    Embedded   │
│  Transactions  scale      SQL          services   pay-per-use    devices    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Database Categories

| Category | Leaders | Use Case | Performance |
|----------|---------|----------|-------------|
| **Relational** | PostgreSQL, MySQL | ACID transactions | 10K TPS |
| **Document** | MongoDB, Couchbase | Flexible schema | 100K ops/s |
| **Key-Value** | Redis, DynamoDB | Caching, sessions | 1M ops/s |
| **Wide Column** | Cassandra, ScyllaDB | Time-series, logs | 1M writes/s |
| **Graph** | Neo4j, Dgraph | Relationships | 100K traversals/s |
| **Search** | Elasticsearch, Meilisearch | Full-text search | 10K searches/s |
| **Time-series** | InfluxDB, TimescaleDB | Metrics, IoT | 1M writes/s |

### 1.3 Go Database Libraries

| Library | Type | ORM | Performance | Maintenance |
|---------|------|-----|-------------|-------------|
| **database/sql** | Standard | No | Good | Standard |
| **sqlx** | Extension | No | Good | Active |
| **gorm** | ORM | Yes | Medium | Very active |
| **ent** | ORM | Yes | Good | Very active |
| **sqlc** | Codegen | Generated | Excellent | Active |
| **pgx** | PostgreSQL | No | Excellent | Very active |
| **go-pg** | PostgreSQL | Yes | Good | Maintenance |

---

## Part II: Connection Management

### 2.1 Connection Pooling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Connection Pool Architecture                             │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                    Application                                          │ │
│  │                                                                        │ │
│  │   ┌──────────────────────────────────────────────────────────────┐   │ │
│  │   │              Connection Pool                                   │   │ │
│  │   │                                                                │   │ │
│  │   │   ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                        │   │ │
│  │   │   │Conn│ │Conn│ │Conn│ │Conn│ │Conn│   MaxOpenConns: 25     │   │ │
│  │   │   │ 1  │ │ 2  │ │ 3  │ │ 4  │ │ 5  │   MaxIdleConns: 5      │   │ │
│  │   │   │ ✓  │ │ ✓  │ │ ✓  │ │ ✗  │ │ ✓  │   ConnMaxLifetime: 5m  │   │ │
│  │   │   └────┘ └────┘ └────┘ └────┘ └────┘   ConnMaxIdleTime: 1m   │   │ │
│  │   │                                                                │   │ │
│  │   │   ┌──────────────────────────────────────────────────────┐     │   │ │
│  │   │   │                    Queue                            │     │   │ │
│  │   │   │   Waiting: 3 requests                               │     │   │ │
│  │   │   └──────────────────────────────────────────────────────┘     │   │ │
│  │   │                                                                │   │ │
│  │   └──────────────────────────────────────────────────────────────┘   │ │
│  │                                                                        │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                              │                                              │
│                              ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                    Database Server (PostgreSQL/MySQL)                  │ │
│  │                                                                        │ │
│  │   Max connections: 100                                                 │ │
│  │   Active connections: 5                                                │ │
│  │                                                                        │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Pool Configuration

| Parameter | Default | Recommended | Impact |
|-----------|---------|-------------|--------|
| **MaxOpenConns** | Unlimited | CPU cores * 2 | Limits connection spikes |
| **MaxIdleConns** | 2 | MaxOpenConns | Reduces connection churn |
| **ConnMaxLifetime** | Unlimited | 1 hour | Prevents stale connections |
| **ConnMaxIdleTime** | Unlimited | 10 minutes | Cleanup idle connections |
| **ConnMaxIdleTime** | - | 1 minute | Free up resources |

### 2.3 Adapter Pattern

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Database Adapter Pattern                               │
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
│  │   │  }                                                           │    │   │
│  │   └──────────────────────────────────────────────────────────────┘    │   │
│  │                              ▲                                         │   │
│  └──────────────────────────────┼─────────────────────────────────────────┘   │
│                                 │                                              │
│                    ═════════════╧═════════════                                   │
│                                 │                                              │
│  ┌──────────────────────────────┼─────────────────────────────────────────┐   │
│  │                    Infrastructure Layer                                │   │
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

## Part III: Query Patterns

### 3.1 Query Builder

```go
type QueryBuilder struct {
    table       string
    columns     []string
    where       []string
    orderBy     []string
    limitVal    int
    offsetVal   int
    params      []interface{}
}

// Fluent API
qb := db.NewQueryBuilder("users").
    Select("id", "name", "email").
    Where("status = ?", "active").
    OrderBy("created_at", true).
    Limit(100).
    Offset(0)

query, args := qb.Build()
// SELECT id, name, email FROM users WHERE status = ? ORDER BY created_at DESC LIMIT 100 OFFSET 0
```

### 3.2 Pagination

| Pattern | Pros | Cons | Use Case |
|---------|------|------|----------|
| **Offset** | Simple | Slow on large offsets | Small datasets |
| **Cursor** | Fast, consistent | Complex | Large datasets |
| **Keyset** | Fast, no skips | Requires index | Infinite scroll |
| **Seek** | Very fast | No jumping | Time-series |

---

## Part IV: Indexing

### 4.1 Index Types

| Type | Use Case | Storage | Performance |
|------|----------|---------|-------------|
| **B-Tree** | General purpose | Medium | O(log n) |
| **Hash** | Equality only | Small | O(1) |
| **GIN** | Full-text, JSON | Large | Variable |
| **GiST** | Geospatial | Medium | Variable |
| **BRIN** | Block range | Very small | Sequential |

### 4.2 Index Best Practices

| DO | DON'T |
|----|-------|
| Index foreign keys | Index low-cardinality columns |
| Index query filters | Index frequently updated columns |
| Use partial indexes | Create redundant indexes |
| Monitor index usage | Index small tables (< 1000 rows) |

---

## Part V: References

| Resource | URL | Description |
|----------|-----|-------------|
| PostgreSQL | https://postgresql.org | Official docs |
| MySQL | https://mysql.com | Official docs |
| SQLite | https://sqlite.org | Official docs |
| sqlc | https://sqlc.dev | SQL compiler |
| pgx | https://github.com/jackc/pgx | PostgreSQL driver |

---

*This document reflects SOTA in database access patterns as of April 2026.*
