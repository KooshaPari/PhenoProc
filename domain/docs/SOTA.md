# State of the Art: Domain-Driven Design and Business Logic Architecture

## Executive Summary

This document provides a comprehensive analysis of the state-of-the-art in Domain-Driven Design (DDD), business logic architecture, and entity modeling patterns. The analysis covers tactical and strategic DDD patterns, event sourcing, CQRS, and modern implementation approaches in Go and other languages.

**Document Version:** 1.0  
**Last Updated:** 2026-04-05  
**Scope:** Domain modeling, DDD patterns, business logic architecture  
**Target Audience:** Software architects, domain modelers, backend engineers

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Domain-Driven Design Fundamentals](#2-domain-driven-design-fundamentals)
3. [Tactical Design Patterns](#3-tactical-design-patterns)
4. [Strategic Design Patterns](#4-strategic-design-patterns)
5. [Event Sourcing](#5-event-sourcing)
6. [CQRS Pattern](#6-cqrs-pattern)
7. [Implementation in Go](#7-implementation-in-go)
8. [Testing Domain Logic](#8-testing-domain-logic)
9. [Comparative Analysis](#9-comparative-analysis)
10. [Recommendations](#10-recommendations)

---

## 1. Introduction

### 1.1 Background

Domain-Driven Design, introduced by Eric Evans in 2003, has become the dominant approach for modeling complex business domains. Key evolution phases:

- **2003:** Eric Evans' "Domain-Driven Design" book
- **2013:** Vaughn Vernon's "Implementing DDD" with practical patterns
- **2015:** Event sourcing and CQRS mainstream adoption
- **2020:** DDD in microservices and distributed systems
- **2024:** AI-assisted domain modeling, automated pattern detection

### 1.2 Scope and Objectives

This research document aims to:

1. Catalog DDD tactical and strategic patterns
2. Analyze implementation approaches in modern languages
3. Evaluate event sourcing and CQRS trade-offs
4. Compare testing strategies for domain logic
5. Inform the design of Phenotype Domain

---

## 2. Domain-Driven Design Fundamentals

### 2.1 Core Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│                     DDD Architecture                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      Domain Layer                         │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │  │
│  │  │   Entity    │  │ Value Object│  │  Aggregate  │        │  │
│  │  │  (Identity) │  │  (Equality) │  │  (Boundary) │        │  │
│  │  └─────────────┘  └─────────────┘  └──────┬──────┘        │  │
│  │                                           │               │  │
│  │  ┌────────────────────────────────────────▼───────────┐ │  │
│  │  │              Domain Events                            │ │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │  │
│  │  │  │   Event     │  │   Event     │  │   Event     │  │ │  │
│  │  │  │  Created    │  │  Updated    │  │  Deleted    │  │ │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │              Domain Services                          │  │  │
│  │  │  (Operations that don't belong to entities/VOs)     │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Application Layer                         │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │  │
│  │  │  Use Case   │  │  Use Case   │  │  Use Case   │       │  │
│  │  │  Handler    │  │  Handler    │  │  Handler    │       │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Infrastructure Layer                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │  │
│  │  │ Repository  │  │   Event     │  │  External   │       │  │
│  │  │  (DB)       │  │   Store     │  │  Services   │       │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└───────────────────────────────────────────────────────────────────┘
```

### 2.2 Ubiquitous Language

The foundation of DDD is a shared language between domain experts and developers:

| Anti-Pattern | Ubiquitous Language |
|--------------|---------------------|
| `User.create()` | `Customer.register()` |
| `Order.process()` | `Order.place()` |
| `updateStatus()` | `Order.confirm()` |
| `getData()` | `Invoice.calculateTotal()` |
| `ItemManager` | `ShoppingCart` |

---

## 3. Tactical Design Patterns

### 3.1 Entities

Entities are objects defined by their identity, not attributes:

```go
// Entity interface defines the contract
type Entity interface {
    ID() EntityID
    Equals(Entity) bool
}

// EntityID represents a unique identifier
type EntityID = uuid.UUID

// BaseEntity provides common entity functionality
type BaseEntity struct {
    id        EntityID
    createdAt time.Time
    updatedAt time.Time
}

func NewBaseEntity(id EntityID) *BaseEntity {
    now := time.Now()
    return &BaseEntity{
        id:        id,
        createdAt: now,
        updatedAt: now,
    }
}

func (e *BaseEntity) ID() EntityID {
    return e.id
}

func (e *BaseEntity) Equals(other Entity) bool {
    if other == nil {
        return false
    }
    return e.id == other.ID()
}

// DomainError represents domain-level errors
type DomainError struct {
    Code    string
    Message string
    Err     error
}

func (e *DomainError) Error() string {
    if e.Err != nil {
        return fmt.Sprintf("%s: %s - %v", e.Code, e.Message, e.Err)
    }
    return fmt.Sprintf("%s: %s", e.Code, e.Message)
}
```

### 3.2 Value Objects

Value objects are immutable and compared by value:

```go
// ValueObject interface
type ValueObject interface {
    Equals(ValueObject) bool
    String() string
}

// Email value object with validation
type Email struct {
    address string
}

func NewEmail(address string) (*Email, error) {
    // RFC 5322 compliant regex
    emailRegex := regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
    if !emailRegex.MatchString(address) {
        return nil, &DomainError{
            Code:    "INVALID_EMAIL",
            Message: "email format is invalid",
        }
    }
    return &Email{address: strings.ToLower(address)}, nil
}

func (e *Email) Equals(other ValueObject) bool {
    if other == nil {
        return false
    }
    o, ok := other.(*Email)
    if !ok {
        return false
    }
    return e.address == o.address
}

func (e *Email) String() string {
    return e.address
}

func (e *Email) Address() string {
    return e.address
}

// Money value object with currency
type Money struct {
    amount   int64 // Stored in cents to avoid float issues
    currency string
}

func NewMoney(amount int64, currency string) *Money {
    return &Money{
        amount:   amount,
        currency: strings.ToUpper(currency),
    }
}

func (m *Money) Add(other *Money) (*Money, error) {
    if m.currency != other.currency {
        return nil, &DomainError{
            Code:    "CURRENCY_MISMATCH",
            Message: fmt.Sprintf("cannot add %s to %s", m.currency, other.currency),
        }
    }
    return NewMoney(m.amount+other.amount, m.currency), nil
}

func (m *Money) Equals(other ValueObject) bool {
    o, ok := other.(*Money)
    if !ok {
        return false
    }
    return m.amount == o.amount && m.currency == o.currency
}

func (m *Money) String() string {
    return fmt.Sprintf("%s %.2f", m.currency, float64(m.amount)/100)
}
```

### 3.3 Aggregates

Aggregates are consistency boundaries containing entities and value objects:

```go
// AggregateRoot interface
type AggregateRoot interface {
    Entity
    Version() uint64
    PullEvents() []DomainEvent
    AddEvent(event DomainEvent)
}

// BaseAggregate provides common aggregate functionality
type BaseAggregate struct {
    BaseEntity
    version       uint64
    pendingEvents []DomainEvent
}

func NewBaseAggregate(id EntityID) *BaseAggregate {
    return &BaseAggregate{
        BaseEntity:    *NewBaseEntity(id),
        version:       1,
        pendingEvents: make([]DomainEvent, 0),
    }
}

func (a *BaseAggregate) Version() uint64 {
    return a.version
}

// PullEvents returns and clears pending domain events
func (a *BaseAggregate) PullEvents() []DomainEvent {
    events := a.pendingEvents
    a.pendingEvents = make([]DomainEvent, 0)
    return events
}

// AddEvent adds a domain event to the aggregate
func (a *BaseAggregate) AddEvent(event DomainEvent) {
    a.pendingEvents = append(a.pendingEvents, event)
    a.version++
    a.Touch()
}
```

### 3.4 Domain Events

Domain events capture state changes:

```go
// DomainEvent interface
type DomainEvent interface {
    EventType() string
    OccurredAt() Time
    AggregateID() EntityID
}

// Time wrapper for domain events
type Time struct {
    value int64 // Unix timestamp
}

func NewTime() Time {
    return Time{value: time.Now().Unix()}
}

func FromTime(t time.Time) Time {
    return Time{value: t.Unix()}
}

func (t Time) Unix() int64 {
    return t.value
}

// BaseDomainEvent provides common functionality
type BaseDomainEvent struct {
    eventType   string
    occurredAt  Time
    aggregateID EntityID
    metadata    map[string]string
}

func NewBaseDomainEvent(eventType string, aggregateID EntityID) *BaseDomainEvent {
    return &BaseDomainEvent{
        eventType:   eventType,
        occurredAt:  NewTime(),
        aggregateID: aggregateID,
        metadata:    make(map[string]string),
    }
}

// OrderCreatedEvent example
type OrderCreatedEvent struct {
    *BaseDomainEvent
    CustomerID EntityID
    Items      []OrderItem
    Total      *Money
}

func NewOrderCreatedEvent(orderID, customerID EntityID, items []OrderItem, total *Money) *OrderCreatedEvent {
    return &OrderCreatedEvent{
        BaseDomainEvent: NewBaseDomainEvent("OrderCreated", orderID),
        CustomerID:      customerID,
        Items:           items,
        Total:           total,
    }
}
```

---

## 4. Strategic Design Patterns

### 4.1 Bounded Contexts

```
┌─────────────────────────────────────────────────────────────────┐
│                     Bounded Contexts                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐         ┌─────────────────┐               │
│  │  Sales Context  │         │ Inventory       │               │
│  │                 │         │ Context         │               │
│  │  - Order        │         │                 │               │
│  │  - Customer     │         │  - Product      │               │
│  │  - Pricing      │         │  - Stock        │               │
│  │  - Discount     │         │  - Warehouse    │               │
│  │                 │         │                 │               │
│  │  Ubiquitous     │         │  Ubiquitous     │               │
│  │  Language:      │         │  Language:      │               │
│  │  "Order",       │         │  "Item",        │               │
│  │  "Customer"     │         │  "Stock"        │               │
│  └────────┬────────┘         └────────┬────────┘               │
│           │                           │                        │
│           │   Integration             │                        │
│           │   (Events/REST)           │                        │
│           └───────────┬───────────────┘                        │
│                       │                                        │
│              ┌────────▼────────┐                               │
│              │   Shared      │                               │
│              │   Kernel      │                               │
│              │   (IDs,       │                               │
│              │   Common VO)   │                               │
│              └───────────────┘                               │
│                                                                  │
└───────────────────────────────────────────────────────────────────┘
```

### 4.2 Context Mapping

Patterns for relating bounded contexts:

| Pattern | Relationship | Use Case |
|---------|------------|----------|
| **Partnership** | Mutual dependency | Tightly coupled teams |
| **Shared Kernel** | Common subset | Shared domain concepts |
| **Customer-Supplier** | Upstream-downstream | API provider-consumer |
| **Conformist** | Follow upstream | Limited influence on upstream |
| **Anti-Corruption Layer** | Translation layer | Legacy integration |
| **Open Host** | Published language | Platform/API provider |
| **Published Language** | Documented protocol | B2B integration |

---

## 5. Event Sourcing

### 5.1 Event Sourcing Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Event Sourcing                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                   Command Handler                          │  │
│  │  ┌──────────┐         ┌──────────┐         ┌──────────┐  │  │
│  │  │ Command  │────────>│ Aggregate│────────>│  Events  │  │  │
│  │  │ (Create)│         │ (Logic)  │         │ (Output) │  │  │
│  │  └──────────┘         └────┬─────┘         └────┬─────┘  │  │
│  │                            │                     │         │  │
│  └─────────────────────────────┼─────────────────────┼─────────┘  │
│                               │                     │            │
│  ┌────────────────────────────▼─────────────────────▼─────────┐  │
│  │                    Event Store                               │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Event Stream (Immutable, Append-Only)              │  │  │
│  │  │                                                     │  │  │
│  │  │  1. OrderCreated { id: 1, items: [...] }           │  │  │
│  │  │  2. OrderItemAdded { orderId: 1, item: {...} }     │  │  │
│  │  │  3. OrderConfirmed { orderId: 1, at: ... }         │  │  │
│  │  │  4. OrderShipped { orderId: 1, tracking: ... }     │  │  │
│  │  │  ...                                                │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                               │                                  │
│           ┌───────────────────┼───────────────────┐              │
│           │                   │                   │              │
│  ┌────────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐    │
│  │  Projection     │  │  Snapshot   │  │  Event Bus        │    │
│  │  (Read Model)   │  │  Store      │  │  (Pub/Sub)        │    │
│  │                 │  │             │  │                   │    │
│  │  ┌───────────┐  │  │  Version    │  │  ┌───────────┐   │    │
│  │  │  Order    │  │  │  5: {...}   │  │  │  Handler  │   │    │
│  │  │  View     │  │  │  Version    │  │  │  A        │   │    │
│  │  │           │  │  │  10: {...}  │  │  └───────────┘   │    │
│  │  └───────────┘  │  └─────────────┘  │  ┌───────────┐   │    │
│  │                 │                   │  │  Handler  │   │    │
│  └─────────────────┘                   │  │  B        │   │    │
│                                       │  └───────────┘   │    │
│                                       └────────────────────┘    │
│                                                                  │
└───────────────────────────────────────────────────────────────────┘
```

---

## 6. CQRS Pattern

### 6.1 CQRS Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CQRS Architecture                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      Command Side                            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │ Command  │  │Command   │  │ Aggregate│  │  Event   │  │  │
│  │  │ Bus      │──>│ Handler│──>│  (Write) │──>│  Store   │  │  │
│  │  │          │  │          │  │          │  │          │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └────┬─────┘  │  │
│  │                                                 │        │  │
│  └──────────────────────────────────────────────────┼────────┘  │
│                                                     │             │
│  ┌──────────────────────────────────────────────────┼────────┐  │
│  │                    Event Projection                  │        │  │
│  │                                                     ▼        │  │
│  │  ┌────────────────────────────────────────────────────────┐│  │
│  │  │              Read Model (Query Side)                    ││  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  ││  │
│  │  │  │  Query   │  │  Query   │  │  Read    │  │  Cache │  ││  │
│  │  │  │  Bus     │──>│ Handler│──>│  Model   │──>│ (Redis)│  ││  │
│  │  │  │          │  │          │  │          │  │        │  ││  │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └────────┘  ││  │
│  │  └────────────────────────────────────────────────────────┘│  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                  │
└───────────────────────────────────────────────────────────────────┘
```

---

## 7. Implementation in Go

### 7.1 Go DDD Patterns

Go's type system and interfaces work well for DDD:

```go
// Package domain contains pure business logic
package domain

// Aggregate: Order
type Order struct {
    *BaseAggregate
    customerID EntityID
    items      []OrderItem
    status     OrderStatus
    total      *Money
}

type OrderStatus int

const (
    OrderStatusPending OrderStatus = iota
    OrderStatusConfirmed
    OrderStatusShipped
    OrderStatusCancelled
)

// Factory method for creating orders
func NewOrder(id, customerID EntityID) *Order {
    order := &Order{
        BaseAggregate: NewBaseAggregate(id),
        customerID:    customerID,
        items:         make([]OrderItem, 0),
        status:        OrderStatusPending,
        total:         NewMoney(0, "USD"),
    }
    
    // Record creation event
    order.AddEvent(NewOrderCreatedEvent(id, customerID, nil, order.total))
    
    return order
}

// Domain method with invariants
func (o *Order) AddItem(productID EntityID, quantity int, unitPrice *Money) error {
    if o.status != OrderStatusPending {
        return &DomainError{
            Code:    "ORDER_ALREADY_CONFIRMED",
            Message: "cannot add items to confirmed order",
        }
    }
    
    if quantity <= 0 {
        return &DomainError{
            Code:    "INVALID_QUANTITY",
            Message: "quantity must be positive",
        }
    }
    
    item := OrderItem{
        ProductID: productID,
        Quantity:  quantity,
        UnitPrice: unitPrice,
    }
    
    o.items = append(o.items, item)
    
    // Recalculate total
    lineTotal, _ := unitPrice.Multiply(int64(quantity))
    o.total, _ = o.total.Add(lineTotal)
    
    // Record event
    o.AddEvent(NewOrderItemAddedEvent(o.ID(), productID, quantity, lineTotal))
    
    return nil
}

func (o *Order) Confirm() error {
    if o.status != OrderStatusPending {
        return &DomainError{
            Code:    "INVALID_STATUS_TRANSITION",
            Message: fmt.Sprintf("cannot confirm order in status %v", o.status),
        }
    }
    
    if len(o.items) == 0 {
        return &DomainError{
            Code:    "EMPTY_ORDER",
            Message: "cannot confirm order with no items",
        }
    }
    
    o.status = OrderStatusConfirmed
    o.AddEvent(NewOrderConfirmedEvent(o.ID()))
    
    return nil
}
```

---

## 10. Recommendations

### 10.1 For Phenotype Domain

Based on this analysis:

1. **Pure Domain Layer:** No external dependencies in domain package
2. **Entity Pattern:** Use BaseEntity for identity management
3. **Value Objects:** Implement for Email, Money, Address
4. **Aggregates:** Define clear boundaries with BaseAggregate
5. **Domain Events:** Record state changes as events
6. **Immutability:** Value objects must be immutable
7. **Validation:** Fail fast with domain errors

### 10.2 Technology Selection

| Component | Pattern | Implementation |
|-----------|---------|----------------|
| Identity | UUID | google/uuid |
| Immutability | Copy-on-write | Go struct copies |
| Validation | Fail fast | DomainError |
| Events | In-memory | Slice of events |
| Equality | Value comparison | Equals() method |

---

*End of Document*
