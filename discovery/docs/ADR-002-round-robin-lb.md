# ADR-002: Round-Robin Load Balancing

## Status
**Accepted**

## Context

The service discovery system needs to distribute traffic across multiple healthy instances of a service. We must choose a load balancing algorithm that balances simplicity, fairness, and performance.

### Requirements

1. **Fairness:** All healthy instances should receive roughly equal traffic
2. **Simplicity:** Implementation should be straightforward
3. **Statelessness:** No per-connection state to manage
4. **Performance:** Selection should be O(1)

### Options Considered

| Algorithm | Pros | Cons |
|-----------|------|------|
| **Round Robin** | Simple, fair, no state | Ignores load/capacity |
| **Random** | Very simple | Uneven distribution |
| **Least Connections** | Considers load | Requires state tracking |
| **Consistent Hashing** | Sticky sessions | Imbalanced distribution |
| **Weighted Round Robin** | Handles capacity | Requires weights |
| **IP Hash** | Session affinity | Uneven distribution |

## Decision

**We will implement Round-Robin load balancing** as the default strategy, with Least Connections as an alternative for stateful services.

### Rationale

1. **Simplicity:** Round-robin is the simplest correct load balancing algorithm
2. **Fairness:** Distributes requests evenly across all instances
3. **Statelessness:** No per-request state management needed
4. **Performance:** Atomic counter increment is extremely fast

### Consequences

**Positive:**
- Extremely simple implementation
- Lock-free with atomic operations
- Perfectly fair request distribution
- No memory overhead per connection

**Negative:**
- Ignores actual service load
- Doesn't account for instance capacity differences
- Not optimal for long-running requests

## Implementation

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Load Balancer Interface                     │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              LoadBalancer Interface                    │  │
│  │         Next(serviceName string) (*Service, error)     │  │
│  └─────────────────────┬───────────────────────────────────┘  │
│                        │                                      │
│         ┌──────────────┼──────────────┐                    │
│         │              │              │                      │
│         ▼              ▼              ▼                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │  RoundRobin  │ │  LeastConn   │ │   Random     │         │
│  │     LB       │ │     LB       │ │     LB       │         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Round Robin Implementation

```go
// LoadBalancer provides service instance selection
type LoadBalancer interface {
    Next(serviceName string) (*Service, error)
}

// RoundRobinLB is a round-robin load balancer
type RoundRobinLB struct {
    registry *Registry
    counters map[string]int
    mu       sync.Mutex
}

// NewRoundRobinLB creates a round-robin load balancer
func NewRoundRobinLB(registry *Registry) *RoundRobinLB {
    return &RoundRobinLB{
        registry: registry,
        counters: make(map[string]int),
    }
}

// Next returns the next service instance
func (lb *RoundRobinLB) Next(serviceName string) (*Service, error) {
    services := lb.registry.Discover(serviceName)
    if len(services) == 0 {
        return nil, fmt.Errorf("no healthy instances for service: %s", serviceName)
    }
    
    lb.mu.Lock()
    count := lb.counters[serviceName]
    lb.counters[serviceName] = (count + 1) % len(services)
    lb.mu.Unlock()
    
    return services[count], nil
}
```

### Optimized Atomic Implementation

```go
// AtomicRoundRobinLB uses atomic operations for lock-free operation
type AtomicRoundRobinLB struct {
    registry *Registry
    counters sync.Map // serviceName -> *atomic.Uint64
}

// NewAtomicRoundRobinLB creates an atomic round-robin load balancer
func NewAtomicRoundRobinLB(registry *Registry) *AtomicRoundRobinLB {
    return &AtomicRoundRobinLB{
        registry: registry,
    }
}

// Next returns the next service instance (lock-free)
func (lb *AtomicRoundRobinLB) Next(serviceName string) (*Service, error) {
    services := lb.registry.Discover(serviceName)
    if len(services) == 0 {
        return nil, fmt.Errorf("no healthy instances for service: %s", serviceName)
    }
    
    // Get or create atomic counter
    counterValue, _ := lb.counters.LoadOrStore(serviceName, &atomic.Uint64{})
    counter := counterValue.(*atomic.Uint64)
    
    // Atomic increment and modulo
    count := counter.Add(1) - 1
    index := int(count % uint64(len(services)))
    
    return services[index], nil
}
```

### Least Connections Alternative

```go
// LeastConnectionsLB tracks active connections per instance
type LeastConnectionsLB struct {
    registry  *Registry
    counters  map[string]*int32 // serviceID -> connection count
}

// NewLeastConnectionsLB creates a least-connections load balancer
func NewLeastConnectionsLB(registry *Registry) *LeastConnectionsLB {
    return &LeastConnectionsLB{
        registry: registry,
        counters: make(map[string]*int32),
    }
}

// Next returns the instance with fewest connections
func (lb *LeastConnectionsLB) Next(serviceName string) (*Service, error) {
    services := lb.registry.Discover(serviceName)
    if len(services) == 0 {
        return nil, fmt.Errorf("no healthy instances for service: %s", serviceName)
    }
    
    var selected *Service
    var minConnections int32 = math.MaxInt32
    
    for _, svc := range services {
        connections := int32(0)
        if counter, ok := lb.counters[svc.ID]; ok {
            connections = atomic.LoadInt32(counter)
        }
        
        if connections < minConnections {
            minConnections = connections
            selected = svc
        }
    }
    
    // Increment connection count
    if selected != nil {
        counter, _ := lb.counters[selected.ID]
        if counter == nil {
            counter = new(int32)
            lb.counters[selected.ID] = counter
        }
        atomic.AddInt32(counter, 1)
    }
    
    return selected, nil
}

// Release decrements connection count
func (lb *LeastConnectionsLB) Release(serviceID string) {
    if counter, ok := lb.counters[serviceID]; ok {
        atomic.AddInt32(counter, -1)
    }
}
```

## Selection Guide

| Scenario | Recommended LB | Rationale |
|----------|---------------|-----------|
| Stateless services | Round Robin | Simple, fair, fast |
| Long-running requests | Least Connections | Prevents overload |
| Session affinity | Consistent Hash | Sticky sessions |
| Variable capacity | Weighted Round Robin | Capacity-aware |

## Related Decisions

- ADR-001: In-Memory Service Registry
- ADR-003: Active Health Checking

---

*Last Updated: 2026-04-05*
