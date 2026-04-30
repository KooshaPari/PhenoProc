# ADR-001: In-Memory Service Registry

## Status
**Accepted**

## Context

The Phenotype Discovery system needs a service registry to track available services and their health status. We must choose between various registry implementations with different trade-offs in consistency, availability, and complexity.

### Requirements

1. **Low Latency:** Service lookup should complete in milliseconds
2. **High Availability:** Registry must be highly available
3. **Simplicity:** Implementation should be straightforward to maintain
4. **Health Awareness:** Must track service health status
5. **Load Balancing:** Support for selecting healthy instances

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **In-Memory Registry** | Fast, simple, no external deps | Data lost on restart, single-node |
| **etcd Integration** | Persistent, distributed | Complex, requires cluster |
| **Consul Client** | Rich features, health checks | External dependency |
| **Redis Backend** | Fast, persistent option | External dependency, eventual consistency |
| **Kubernetes Endpoints** | Native K8s integration | K8s-only, limited customization |

## Decision

**We will implement an in-memory service registry** with periodic health checking. This provides the lowest latency and simplest implementation for the expected scale.

### Rationale

1. **Latency:** In-memory lookups complete in microseconds vs. milliseconds for network calls
2. **Simplicity:** No external dependencies or complex distributed systems concerns
3. **Scale:** Phenotype services operate at a scale where in-memory is sufficient
4. **Recovery:** Services re-register on restart, allowing quick recovery

### Consequences

**Positive:**
- Extremely fast lookups (< 1ms)
- No network dependencies for discovery
- Simple implementation and testing
- Easy to extend with custom load balancing

**Negative:**
- State lost on process restart
- Single-node limitation
- No persistence across restarts
- Requires service re-registration

## Implementation

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Service Registry                            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    Registry Core                         │ │
│  │  ┌─────────────┐    ┌─────────────┐                   │ │
│  │  │  services   │    │   mutex     │                   │ │
│  │  │   map       │    │  (RWMutex)  │                   │ │
│  │  │ name->id->  │    │             │                   │ │
│  │  │   service   │    │             │                   │ │
│  │  └─────────────┘    └─────────────┘                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           │                                    │
│                    ┌──────▼──────┐                           │
│                    │ Health      │                           │
│                    │ Checker     │                           │
│                    └─────────────┘                           │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Load Balancers                              │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │ │
│  │  │  Round   │  │  Least   │  │  Hash    │              │ │
│  │  │  Robin   │  │  Conn    │  │  Ring    │              │ │
│  │  └──────────┘  └──────────┘  └──────────┘              │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Core Implementation

```go
// Service represents a registered service instance
type Service struct {
    ID       string
    Name     string
    Address  string
    Port     int
    Metadata map[string]string
    Healthy  bool
    LastSeen time.Time
}

// Registry manages service registration and discovery
type Registry struct {
    services map[string]map[string]*Service // name -> id -> service
    mu       sync.RWMutex
    logger   *slog.Logger
}

// New creates a new service registry
func New() *Registry {
    return &Registry{
        services: make(map[string]map[string]*Service),
        logger:   slog.Default(),
    }
}

// Register adds a service to the registry
func (r *Registry) Register(service *Service) error {
    r.mu.Lock()
    defer r.mu.Unlock()
    
    if r.services[service.Name] == nil {
        r.services[service.Name] = make(map[string]*Service)
    }
    
    service.LastSeen = time.Now()
    r.services[service.Name][service.ID] = service
    
    r.logger.Info("service registered",
        "name", service.Name,
        "id", service.ID,
        "address", service.Address)
    return nil
}

// Deregister removes a service from the registry
func (r *Registry) Deregister(name, id string) error {
    r.mu.Lock()
    defer r.mu.Unlock()
    
    if r.services[name] == nil {
        return fmt.Errorf("service not found: %s", name)
    }
    
    delete(r.services[name], id)
    r.logger.Info("service deregistered", "name", name, "id", id)
    return nil
}

// Discover returns all healthy instances of a service
func (r *Registry) Discover(name string) []*Service {
    r.mu.RLock()
    defer r.mu.RUnlock()
    
    services, ok := r.services[name]
    if !ok {
        return nil
    }
    
    result := make([]*Service, 0)
    for _, s := range services {
        if s.Healthy {
            result = append(result, s)
        }
    }
    
    return result
}
```

## Health Checking

```go
// HealthChecker periodically checks service health
type HealthChecker struct {
    registry *Registry
    client   *http.Client
    interval time.Duration
    timeout  time.Duration
}

// NewHealthChecker creates a new health checker
func NewHealthChecker(registry *Registry, interval, timeout time.Duration) *HealthChecker {
    return &HealthChecker{
        registry: registry,
        client:   &http.Client{Timeout: timeout},
        interval: interval,
        timeout:  timeout,
    }
}

// Start begins the health check loop
func (hc *HealthChecker) Start(ctx context.Context) {
    ticker := time.NewTicker(hc.interval)
    defer ticker.Stop()
    
    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            hc.checkServices()
        }
    }
}

func (hc *HealthChecker) checkServices() {
    services := hc.registry.ListServices()
    
    for _, instances := range services {
        for _, svc := range instances {
            healthURL := fmt.Sprintf("http://%s:%d/health", svc.Address, svc.Port)
            
            ctx, cancel := context.WithTimeout(context.Background(), hc.timeout)
            defer cancel()
            
            req, _ := http.NewRequestWithContext(ctx, "GET", healthURL, nil)
            resp, err := hc.client.Do(req)
            
            if err != nil || resp.StatusCode != http.StatusOK {
                hc.registry.SetHealthy(svc.Name, svc.ID, false)
                continue
            }
            resp.Body.Close()
            
            hc.registry.SetHealthy(svc.Name, svc.ID, true)
        }
    }
}
```

## Migration Path

If persistence or distributed operation becomes necessary:

```go
// Registry interface allows different implementations
type Registry interface {
    Register(service *Service) error
    Deregister(name, id string) error
    Discover(name string) []*Service
    GetService(name, id string) (*Service, bool)
    SetHealthy(name, id string, healthy bool) error
    Heartbeat(name, id string) error
    ListServices() map[string][]*Service
}

// InMemoryRegistry is the current implementation
var _ Registry = (*Registry)(nil)

// Future: etcd-backed implementation
type EtcdRegistry struct {
    client *clientv3.Client
}

var _ Registry = (*EtcdRegistry)(nil)
```

## Related Decisions

- ADR-002: Round-Robin Load Balancing
- ADR-003: Active Health Checking

---

*Last Updated: 2026-04-05*
