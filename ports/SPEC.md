# Ports Library Specification

> Hexagonal Architecture Ports for Go - Clean Architecture Boundaries

**Version**: 1.0  
**Status**: Production  
**Last Updated**: 2026-04-05

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Port Types](#3-port-types)
4. [Configuration](#4-configuration)
5. [Usage Patterns](#5-usage-patterns)
6. [Integration](#6-integration)
7. [Appendices](#7-appendices)

---

## 1. Overview

### 1.1 Purpose

The ports library provides interfaces and patterns for implementing hexagonal architecture (ports and adapters) in Go applications. It enables:

- **Clean separation**: Domain logic independent of infrastructure
- **Testability**: Easy mocking of external dependencies
- **Flexibility**: Swap implementations without domain changes
- **Type safety**: Generic repository patterns

### 1.2 Goals

| Goal | Priority | Status |
|------|----------|--------|
| Generic Repository[T] | P0 | ✅ Implemented |
| Marker interfaces | P0 | ✅ Implemented |
| Filter API | P1 | ✅ Implemented |
| Event bus port | P1 | ✅ Implemented |
| Query repository | P1 | ✅ Implemented |

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Port** | Interface defining what the domain needs |
| **Adapter** | Concrete implementation of a port |
| **Input Port** | Port for driving the application (incoming) |
| **Output Port** | Port for driven by the application (outgoing) |
| **Repository** | Port for data persistence |
| **Filter** | Query criteria specification |

---

## 2. Architecture

### 2.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Hexagonal Architecture                                 │
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
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Port Interfaces

```go
// InputPort marker interface
type InputPort interface {
    isInputPort()
}

// OutputPort marker interface
type OutputPort interface {
    isOutputPort()
}

// Repository generic port
type Repository[T any] interface {
    Save(ctx context.Context, entity T) (T, error)
    FindByID(ctx context.Context, id string) (T, error)
    Delete(ctx context.Context, id string) error
    FindAll(ctx context.Context) ([]T, error)
}

// QueryRepository for read operations
type QueryRepository[T any] interface {
    FindByFilter(ctx context.Context, filter Filter) ([]T, error)
    Count(ctx context.Context, filter Filter) (int64, error)
}
```

---

## 3. Port Types

### 3.1 Repository Port

```go
// Generic repository for any entity type
type UserRepository interface {
    Repository[User]
    FindByEmail(ctx context.Context, email string) (User, error)
}

// Implementation (in infrastructure layer)
type PostgresUserRepository struct {
    db *sql.DB
}

func (r *PostgresUserRepository) Save(ctx context.Context, user User) (User, error) {
    // Implementation
}
```

### 3.2 Filter API

```go
// Create a filter with fluent API
filter := NewFilter().
    WithCondition("status", OpEq, "active").
    WithCondition("age", OpGte, 18).
    WithLimit(100).
    WithOffset(0)

// Supported operators
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
```

### 3.3 Event Ports

```go
// EventBus for publishing events
type EventBus interface {
    Publish(ctx context.Context, topic string, event Event) error
    Subscribe(topic string, handler EventHandler)
}

type EventHandler interface {
    Handle(ctx context.Context, event Event) error
}

// EventStore for event sourcing
type EventStore interface {
    Append(ctx context.Context, aggregateID string, events []Event, expectedVersion uint64) error
    GetEvents(ctx context.Context, aggregateID string) ([]Event, error)
}
```

---

## 4. Configuration

No external configuration required. Ports are pure interfaces defined in code.

---

## 5. Usage Patterns

### 5.1 Repository Implementation

```go
// Domain layer - define port
type OrderRepository interface {
    Repository[Order]
    FindByCustomerID(ctx context.Context, customerID string) ([]Order, error)
}

// Infrastructure layer - implement adapter
type PostgresOrderRepository struct {
    db *sql.DB
}

func NewPostgresOrderRepository(db *sql.DB) *PostgresOrderRepository {
    return &PostgresOrderRepository{db: db}
}

func (r *PostgresOrderRepository) Save(ctx context.Context, order Order) (Order, error) {
    query := `INSERT INTO orders (id, customer_id, total) VALUES ($1, $2, $3)`
    _, err := r.db.ExecContext(ctx, query, order.ID, order.CustomerID, order.Total)
    return order, err
}
```

### 5.2 Use Case Implementation

```go
// Domain layer - use case
type CreateOrderUseCase struct {
    orderRepo   OrderRepository
    customerRepo CustomerRepository
    eventBus    EventBus
}

func (uc *CreateOrderUseCase) Execute(ctx context.Context, cmd CreateOrderCommand) (Order, error) {
    // Validate customer exists
    customer, err := uc.customerRepo.FindByID(ctx, cmd.CustomerID)
    if err != nil {
        return Order{}, err
    }
    
    // Create order
    order := Order{
        ID:         uuid.New().String(),
        CustomerID: customer.ID,
        Items:      cmd.Items,
        Total:      calculateTotal(cmd.Items),
    }
    
    // Save order
    saved, err := uc.orderRepo.Save(ctx, order)
    if err != nil {
        return Order{}, err
    }
    
    // Publish event
    uc.eventBus.Publish(ctx, "orders", OrderCreatedEvent{OrderID: saved.ID})
    
    return saved, nil
}
```

### 5.3 Testing with Mocks

```go
// Mock implementation
type MockOrderRepository struct {
    mock.Mock
}

func (m *MockOrderRepository) Save(ctx context.Context, order Order) (Order, error) {
    args := m.Called(ctx, order)
    return args.Get(0).(Order), args.Error(1)
}

// Test
func TestCreateOrderUseCase(t *testing.T) {
    mockRepo := new(MockOrderRepository)
    mockBus := new(MockEventBus)
    
    uc := CreateOrderUseCase{
        orderRepo: mockRepo,
        eventBus:  mockBus,
    }
    
    mockRepo.On("Save", mock.Anything, mock.Anything).Return(expectedOrder, nil)
    mockBus.On("Publish", mock.Anything, "orders", mock.Anything).Return(nil)
    
    result, err := uc.Execute(context.Background(), cmd)
    
    assert.NoError(t, err)
    assert.Equal(t, expectedOrder, result)
    mockRepo.AssertExpectations(t)
}
```

---

## 6. Integration

### 6.1 Dependency Injection

```go
// Wire up dependencies
func NewApplication(db *sql.DB, eventBus EventBus) *Application {
    // Create repositories
    userRepo := NewPostgresUserRepository(db)
    orderRepo := NewPostgresOrderRepository(db)
    
    // Create use cases
    createOrder := &CreateOrderUseCase{
        orderRepo:    orderRepo,
        customerRepo: userRepo,
        eventBus:     eventBus,
    }
    
    // Create HTTP handlers (input adapters)
    orderHandler := NewOrderHTTPHandler(createOrder)
    
    return &Application{
        OrderHandler: orderHandler,
    }
}
```

---

## 7. Appendices

### 7.1 API Reference

See [port.go](../port.go) for complete interface definitions.

### 7.2 Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-05 | Initial release |

---

*This specification defines the ports library v1.0 for Phenotype Go Kit.*
