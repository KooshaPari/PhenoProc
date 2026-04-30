# Ports Library - State of the Art

> Hexagonal Architecture Ports for Go - Clean Architecture Boundaries

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-04-05

---

## Part I: Architecture Patterns Landscape (2024-2026)

### 1.1 Architectural Pattern Evolution

The software architecture landscape has evolved from monolithic designs to sophisticated modular patterns that emphasize separation of concerns and testability.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Architecture Pattern Evolution                           │
│                                                                             │
│  1990s     2000s     2010s     2015s     2020s     2024+                    │
│    │         │         │         │         │         │                     │
│    ▼         ▼         ▼         ▼         ▼         ▼                     │
│  ┌────┐   ┌────┐   ┌────┐   ┌────┐   ┌────┐   ┌────┐                       │
│  │3-  │ → │MVC │ → │SOA │ → │Micro│ → │Clean│ → │Hexa-│                       │
│  │Tier│   │    │   │    │   │svc  │   │Arch │   │gonal│                       │
│  └────┘   └────┘   └────┘   └────┘   └────┘   └────┘                       │
│                                                                             │
│  Database  View/     Service  Services  Entities  Ports &                   │
│  Driven    Controller Oriented per app   & Use    Adapters                  │
│            Separation  Arch    Bounded   Cases                               │
│                      (SOAP)    Context  (Uncle Bob)                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Hexagonal Architecture (Ports & Adapters)

Hexagonal Architecture, also known as Ports and Adapters, was introduced by Alistair Cockburn in 2005. It has become the gold standard for clean, testable, and maintainable applications.

#### Core Concepts

| Concept | Definition | Benefit |
|---------|------------|---------|
| **Domain** | Business logic, entities, value objects | Independent of framework |
| **Ports** | Interfaces defining what the domain needs | Contract definition |
| **Adapters** | Concrete implementations of ports | Technology isolation |
| **Dependency Rule** | Dependencies point inward | Testability |

#### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Hexagonal Architecture                               │
│                                                                             │
│                              ┌──────────┐                                   │
│                              │          │                                   │
│                              │  Domain  │                                   │
│                              │          │                                   │
│                              │ • Entities│                                   │
│                              │ • Use     │                                   │
│                              │   Cases   │                                   │
│                              │ • Services│                                   │
│                              │          │                                   │
│                              └────┬─────┘                                   │
│                                   │                                         │
│         ══════════════════════════│═══════════════════════════               │
│                                   │                                         │
│              Input Ports            │            Output Ports                │
│         (Driving Adapters)         │         (Driven Adapters)               │
│                                   │                                         │
│     ┌──────────┐    ┌──────────┐ │  ┌──────────┐    ┌──────────┐             │
│     │   HTTP   │    │   CLI    │◄┼──┤ Repository│    │  External│             │
│     │ Handler  │    │  Handler │ │  │  Port    ├────┤  Service │             │
│     └──────────┘    └──────────┘ │  └──────────┘    └──────────┘             │
│                                   │                                         │
│     ┌──────────┐    ┌──────────┐ │  ┌──────────┐    ┌──────────┐             │
│     │   gRPC   │    │  Message │◄┼──┤  Event   │    │  File    │             │
│     │ Handler  │    │  Queue   │ │  │  Store   ├────┤  System  │             │
│     └──────────┘    └──────────┘ │  └──────────┘    └──────────┘             │
│                                   │                                         │
│         Primary Adapters           │         Secondary Adapters             │
│                                                                             │
│  Dependency Direction: Inward (Domain has no external dependencies)          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Pattern Comparison

| Pattern | Testability | Flexibility | Complexity | Learning Curve | Best For |
|---------|-------------|-------------|------------|----------------|----------|
| **Layered** | Low | Low | Simple | Easy | CRUD apps |
| **MVC** | Medium | Medium | Simple | Easy | Web apps |
| **Microservices** | Medium | High | Complex | Hard | Distributed |
| **Clean Architecture** | High | High | Medium | Medium | Enterprise |
| **Hexagonal** | Very High | Very High | Medium | Medium | Domain-driven |
| **Event Sourcing** | High | High | Complex | Hard | Audit trails |
| **CQRS** | High | High | Complex | Hard | Read-heavy |

### 1.4 Ports & Adapters Ecosystem

#### Popular Implementations

| Language | Library | Approach | Stars | Status |
|----------|---------|----------|-------|--------|
| **Go** | go-kit/kit | Service-based | 26K+ | Active |
| **Go** | go-clean-arch | Template | 2K+ | Active |
| **Java** | Spring Hexagonal | Annotation | 1K+ | Active |
| **PHP** | ApiPlatform | Framework | 8K+ | Active |
| **TypeScript** | NestJS | Module-based | 65K+ | Active |
| **Rust** | hexagonal-rs | Traits | 500+ | Experimental |

---

## Part II: Port Types & Patterns

### 2.1 Port Categories

#### Input Ports (Driving Ports)

Input ports define how the application can be driven by external actors.

| Port Type | Purpose | Examples |
|-----------|---------|----------|
| **Command Handler** | Handle commands | CreateOrder, UpdateUser |
| **Query Handler** | Handle queries | GetOrder, ListUsers |
| **Event Subscriber** | React to events | OnPaymentReceived |
| **Use Case** | Execute business logic | ProcessCheckout |

#### Output Ports (Driven Ports)

Output ports define what the application needs from external services.

| Port Type | Purpose | Examples |
|-----------|---------|----------|
| **Repository** | Data persistence | Save, FindByID |
| **Event Bus** | Event publishing | Publish, Subscribe |
| **External Service** | HTTP/gRPC calls | SendEmail, ProcessPayment |
| **File Storage** | File operations | Store, Retrieve |

### 2.2 Repository Pattern

The Repository pattern is the most common output port, abstracting data persistence.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Repository Pattern                                     │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        Domain Layer                                   │   │
│  │                                                                        │   │
│  │   ┌──────────────────────────────────────────────────────────────┐    │   │
│  │   │                    Repository Port (Interface)               │    │   │
│  │   │                                                              │    │   │
│  │   │  type Repository[T any] interface {                          │    │   │
│  │   │      Save(ctx context.Context, entity T) (T, error)         │    │   │
│  │   │      FindByID(ctx context.Context, id string) (T, error)  │    │   │
│  │   │      Delete(ctx context.Context, id string) error         │    │   │
│  │   │      FindAll(ctx context.Context) ([]T, error)              │    │   │
│  │   │  }                                                         │    │   │
│  │   └──────────────────────────────────────────────────────────────┘    │   │
│  │                              ▲                                         │   │
│  └──────────────────────────────┼─────────────────────────────────────────┘   │
│                                │                                              │
│                    ════════════╧════════════                                   │
│                                │                                              │
│  ┌──────────────────────────────┼─────────────────────────────────────────┐   │
│  │                    Infrastructure Layer                                  │   │
│  │                            │                                            │   │
│  │   ┌────────────────────────┴────────────────────────┐                   │   │
│  │   │              Repository Adapters               │                   │   │
│  │   │                                                │                   │   │
│  │   │  ┌──────────────┐  ┌──────────────┐  ┌──────────┴──────┐             │   │
│  │   │  │   Postgres   │  │    MySQL     │  │    MongoDB      │             │   │
│  │   │  │   Adapter    │  │   Adapter    │  │    Adapter      │             │   │
│  │   │  └──────────────┘  └──────────────┘  └─────────────────┘             │   │
│  │   │                                                │                   │   │
│  │   └────────────────────────────────────────────────┘                   │   │
│  │                                                                        │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 CQRS with Ports

Command Query Responsibility Segregation separates read and write operations.

| Aspect | Command Side | Query Side |
|--------|--------------|------------|
| **Purpose** | Modify state | Read state |
| **Port** | CommandHandler | QueryHandler |
| **Repository** | Repository[T] | QueryRepository[T] |
| **Consistency** | Strong | Eventual |
| **Optimization** | Transactions | Read replicas |

---

## Part III: Go Implementation Patterns

### 3.1 Generic Ports

Go 1.18+ generics enable type-safe repository ports.

```go
// Generic Repository Port
type Repository[T any] interface {
    Save(ctx context.Context, entity T) (T, error)
    FindByID(ctx context.Context, id string) (T, error)
    Delete(ctx context.Context, id string) error
    FindAll(ctx context.Context) ([]T, error)
}

// Generic Query Repository
type QueryRepository[T any] interface {
    FindByFilter(ctx context.Context, filter Filter) ([]T, error)
    Count(ctx context.Context, filter Filter) (int64, error)
}

// Usage
type UserRepository interface {
    Repository[User]
    FindByEmail(ctx context.Context, email string) (User, error)
}
```

### 3.2 Filter Pattern

The Filter pattern enables flexible query composition.

```go
// Filter with fluent API
type Filter struct {
    Conditions []Condition
    Limit      int
    Offset     int
}

type Condition struct {
    Field    string
    Operator Operator
    Value    any
}

type Operator string

const (
    OpEq         Operator = "eq"
    OpNe         Operator = "ne"
    OpGt         Operator = "gt"
    OpLt         Operator = "lt"
    OpGte        Operator = "gte"
    OpLte        Operator = "lte"
    OpContains   Operator = "contains"
    OpStartsWith Operator = "startsWith"
    OpIn         Operator = "in"
)

// Fluent API
filter := NewFilter().
    WithCondition("status", OpEq, "active").
    WithCondition("age", OpGte, 18).
    WithLimit(100).
    WithOffset(0)
```

### 3.3 Event-Driven Ports

Event ports enable loose coupling between domains.

```go
// Event Port
type EventBus interface {
    Publish(ctx context.Context, topic string, event Event) error
    Subscribe(topic string, handler EventHandler)
}

type EventHandler interface {
    Handle(ctx context.Context, event Event) error
}

// Event Store Port (for Event Sourcing)
type EventStore interface {
    Append(ctx context.Context, aggregateID string, events []Event, expectedVersion uint64) error
    GetEvents(ctx context.Context, aggregateID string) ([]Event, error)
}
```

---

## Part IV: Testing Strategies

### 4.1 Test Pyramid with Ports

| Test Type | Scope | Tools | Port Usage |
|-----------|-------|-------|------------|
| **Unit** | Domain logic | Go test | Mock ports |
| **Integration** | Adapters | Testcontainers | Real implementations |
| **Contract** | Port interfaces | Pact | Consumer/provider |
| **E2E** | Full flow | Cypress/Playwright | Production setup |

### 4.2 Mock Generation

```go
//go:generate mockery --name=Repository --case=underscore

type MockRepository[T any] struct {
    mock.Mock
}

func (m *MockRepository[T]) Save(ctx context.Context, entity T) (T, error) {
    args := m.Called(ctx, entity)
    return args.Get(0).(T), args.Error(1)
}
```

---

## Part V: References

### 5.1 Core Resources

| Resource | URL | Description |
|----------|-----|-------------|
| Hexagonal Architecture | https://alistair.cockburn.us/hexagonal-architecture/ | Original article |
| Clean Architecture | https://blog.cleancoder.com/ | Uncle Bob's blog |
| Domain-Driven Design | https://domainlanguage.com/ | Eric Evans |
| Go Clean Arch | https://github.com/bxcodec/go-clean-arch | Example project |

### 5.2 Glossary

| Term | Definition |
|------|------------|
| **Port** | Interface defining domain needs |
| **Adapter** | Concrete implementation of a port |
| **Domain** | Business logic core |
| **Use Case** | Application-specific business operation |
| **Entity** | Domain object with identity |
| **Value Object** | Immutable domain object without identity |

---

*This document reflects SOTA in clean architecture as of April 2026.*
