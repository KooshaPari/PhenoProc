# ADR-003: Domain Events for State Changes

## Status
**Accepted**

## Context

When domain state changes, other parts of the system often need to react. We need a mechanism to notify interested parties about significant state changes without creating tight coupling.

### Requirements

1. **Loose Coupling:** Domain model should not know about subscribers
2. **Immutable History:** Changes should be recorded as facts
3. **Audit Trail:** Track what happened and when
4. **Event Sourcing Ready:** Support potential future event sourcing migration
5. **Synchronous/Asynchronous:** Support both immediate and deferred handling

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Domain Events** | Loose coupling, audit trail, replayable | Eventual consistency |
| **Direct Calls** | Immediate consistency | Tight coupling |
| **Observer Pattern** | Decoupled | Hard to track dependencies |
| **Database Triggers** | Automatic | Database-specific, hard to test |

## Decision

**We will use Domain Events** recorded by aggregates and published after successful persistence.

### Rationale

1. **Ubiquitous Language:** Events named in domain language (OrderPlaced, not OrderUpdated)
2. **Loose Coupling:** Aggregates don't know about handlers
3. **Audit Trail:** Complete history of state changes
4. **Event Sourcing Path:** Can evolve to event sourcing later

### Consequences

**Positive:**
- Loose coupling between aggregates and handlers
- Complete audit trail
- Enables event-driven architecture
- Can replay events for recovery

**Negative:**
- Eventual consistency
- Event schema evolution complexity
- Need infrastructure for publishing

## Implementation

### Domain Event Interface

```go
// DomainEvent is the interface that all domain events implement
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

func (t Time) ToTime() time.Time {
    return time.Unix(t.value, 0)
}
```

### Base Domain Event

```go
// BaseDomainEvent provides common domain event functionality
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

func (e *BaseDomainEvent) EventType() string {
    return e.eventType
}

func (e *BaseDomainEvent) OccurredAt() Time {
    return e.occurredAt
}

func (e *BaseDomainEvent) AggregateID() EntityID {
    return e.aggregateID
}

func (e *BaseDomainEvent) WithMetadata(key, value string) *BaseDomainEvent {
    e.metadata[key] = value
    return e
}

func (e *BaseDomainEvent) GetMetadata(key string) string {
    return e.metadata[key]
}
```

### Aggregate with Event Recording

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

### Concrete Event Examples

```go
// OrderCreatedEvent represents a new order
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

// OrderConfirmedEvent represents order confirmation
type OrderConfirmedEvent struct {
    *BaseDomainEvent
    ConfirmedAt Time
}

func NewOrderConfirmedEvent(orderID EntityID) *OrderConfirmedEvent {
    return &OrderConfirmedEvent{
        BaseDomainEvent: NewBaseDomainEvent("OrderConfirmed", orderID),
        ConfirmedAt:     NewTime(),
    }
}

// OrderItemAddedEvent represents adding an item to an order
type OrderItemAddedEvent struct {
    *BaseDomainEvent
    ProductID  EntityID
    Quantity   int
    LineTotal  *Money
}

func NewOrderItemAddedEvent(orderID, productID EntityID, quantity int, lineTotal *Money) *OrderItemAddedEvent {
    return &OrderItemAddedEvent{
        BaseDomainEvent: NewBaseDomainEvent("OrderItemAdded", orderID),
        ProductID:       productID,
        Quantity:        quantity,
        LineTotal:       lineTotal,
    }
}
```

### Aggregate Using Events

```go
// Order aggregate example
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

func NewOrder(id, customerID EntityID) *Order {
    order := &Order{
        BaseAggregate: NewBaseAggregate(id),
        customerID:    customerID,
        items:         make([]OrderItem, 0),
        status:        OrderStatusPending,
        total:         NewMoney(0, 100, "USD"), // $0.00
    }
    
    // Record creation event
    order.AddEvent(NewOrderCreatedEvent(id, customerID, nil, order.total))
    
    return order
}

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

## Event Publishing

```go
// EventPublisher publishes domain events
type EventPublisher interface {
    Publish(event DomainEvent) error
}

// InMemoryEventPublisher for testing
type InMemoryEventPublisher struct {
    handlers map[string][]EventHandler
}

type EventHandler func(event DomainEvent) error

func (p *InMemoryEventPublisher) Subscribe(eventType string, handler EventHandler) {
    if p.handlers[eventType] == nil {
        p.handlers[eventType] = make([]EventHandler, 0)
    }
    p.handlers[eventType] = append(p.handlers[eventType], handler)
}

func (p *InMemoryEventPublisher) Publish(event DomainEvent) error {
    handlers := p.handlers[event.EventType()]
    for _, handler := range handlers {
        if err := handler(event); err != nil {
            return err
        }
    }
    return nil
}
```

## Related Decisions

- ADR-001: UUID as Entity Identifier
- ADR-002: Value Objects for Domain Primitives

---

*Last Updated: 2026-04-05*
