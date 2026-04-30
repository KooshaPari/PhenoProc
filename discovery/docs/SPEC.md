# SPEC: Discovery System

## 1. Overview

The Phenotype Discovery system provides service registration, discovery, and load balancing for the Phenotype ecosystem. It enables services to locate and communicate with each other in dynamic, distributed environments.

### 1.1 Purpose

This specification defines the architecture, interfaces, and behavior of the Discovery system, including:

- Service registration and deregistration
- Service discovery and lookup
- Health checking and monitoring
- Load balancing strategies

### 1.2 Scope

**In Scope:**
- In-memory service registry
- HTTP health checking
- Round-robin load balancing
- Service metadata management

**Out of Scope:**
- Distributed consensus (handled by external systems)
- Persistent storage (state rebuilt on restart)
- Complex service mesh features
- Multi-datacenter replication

### 1.3 Target Audience

- Backend Engineers
- Platform Engineers
- DevOps Engineers
- System Architects

### 1.4 Document Conventions

- **MUST:** Required for compliance
- **SHOULD:** Recommended but not required
- **MAY:** Optional
- **SHALL:** Synonym for MUST

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Phenotype Discovery                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        API Layer                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│  │  │  Register   │  │  Discover   │  │  Health     │  │  List      │  │   │
│  │  │  Handler    │  │  Handler    │  │  Handler    │  │  Handler   │  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘  │   │
│  └─────────┼────────────────┼────────────────┼───────────────┼────────┘   │
│            │                │                │               │            │
│  ┌─────────┼────────────────┼────────────────┼───────────────┼────────┐       │
│  │         ▼                ▼                ▼               ▼        │       │
│  │  ┌─────────────────────────────────────────────────────────────┐ │       │
│  │  │                    Core Engine                             │ │       │
│  │  ├─────────────────────────────────────────────────────────────┤ │       │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │ │       │
│  │  │  │  Registry   │  │    Load     │  │     Health              │ │ │       │
│  │  │  │  (In-Mem)   │  │  Balancer   │  │    Checker            │ │ │       │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────────┘ │ │       │
│  │  └─────────────────────────────────────────────────────────────┘ │       │
│  └────────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Storage Layer                                   │   │
│  │  ┌───────────────────────────────────────────────────────────────┐ │   │
│  │  │                  In-Memory Store                               │ │   │
│  │  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │ │   │
│  │  │  │  Service Map    │  │  Health Status  │  │  Load Balancer  │  │ │   │
│  │  │  │  (sync.Map)     │  │  (Atomic Bool)  │  │  (Counters)     │  │ │   │
│  │  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  │ │   │
│  │  └───────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Client Integration                                │   │
│  │         ┌──────────────────────────────────────────────┐            │   │
│  │         │              Service Clients                    │            │   │
│  │         │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │            │   │
│  │         │  │ Service A│  │ Service B│  │ Service C│      │            │   │
│  │         │  └──────────┘  └──────────┘  └──────────┘      │            │   │
│  │         └──────────────────────────────────────────────┘            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Diagram

```
                         ┌─────────────────┐
                         │    Client       │
                         │   Application   │
                         └────────┬────────┘
                                  │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
          ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
          │   Register   │  │   Discover   │  │   Health     │
          │   Service    │  │   Service    │  │   Check      │
          └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                 │                 │                 │
                 └─────────────────┼─────────────────┘
                                   │
                         ┌─────────▼─────────┐
                         │    Registry       │
                         │   (Interface)      │
                         └─────────┬─────────┘
                                   │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
          ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
          │  In-Memory   │  │    etcd      │  │   Consul     │
          │   Registry   │  │   (Future)   │  │   (Future)   │
          └──────────────┘  └──────────────┘  └──────────────┘
```

### 2.3 Data Flow

#### 2.3.1 Service Registration Flow

```
┌─────────┐    ┌───────────┐    ┌──────────┐    ┌─────────┐
│ Service │───>│  Validate │───>│  Store   │───>│ Confirm │
│ (Start) │    │   Input   │    │  in Map  │    │   OK    │
└─────────┘    └───────────┘    └──────────┘    └─────────┘
     │              │               │              │
     │              │               │              │
     ▼              ▼               ▼              ▼
   Startup      Check name      Atomic insert    Return
   Hook         uniqueness      with mutex       service
                               Update index     details
```

#### 2.3.2 Service Discovery Flow

```
┌─────────┐    ┌───────────┐    ┌──────────┐    ┌─────────┐
│ Client  │───>│   Query   │───>│  Filter  │───>│ Return  │
│ Request │    │  Registry │    │ Healthy  │    │ Service │
└─────────┘    └───────────┘    └──────────┘    └─────────┘
     │              │               │              │
     │              │               │              │
     ▼              ▼               ▼              ▼
   service=      RLock map      Healthy=true    Select
   api-gateway   Get all         LastSeen<30s    via LB
                 instances
```

#### 2.3.3 Health Check Flow

```
┌─────────┐    ┌───────────┐    ┌──────────┐    ┌─────────┐
│ Health  │───>│   HTTP    │───>│ Evaluate │───>│ Update  │
│ Checker │    │   Probe   │    │  Result  │    │ Status  │
└─────────┘    └───────────┘    └──────────┘    └─────────┘
     │              │               │              │
     │              │               │              │
     ▼              ▼               ▼              ▼
   Ticker fires   GET /health    Success:        Set
   every 10s      timeout 5s     mark healthy    Healthy
                                 Fail:           flag
                                 mark unhealthy  (atomic)
```

### 2.4 Module Structure

```
discovery/
├── docs/                   # Documentation
│   ├── SOTA.md            # State of the Art research
│   ├── ADR-*.md           # Architecture Decision Records
│   └── SPEC.md            # This specification
├── registry.go            # Core registry implementation
├── registry_test.go       # Registry tests
├── health.go              # Health checking
├── health_test.go         # Health tests
├── balancer.go            # Load balancing
├── balancer_test.go       # Balancer tests
├── types.go               # Type definitions
├── errors.go              # Error definitions
├── go.mod                 # Go module definition
└── README.md              # Project readme
```

---

## 3. Interfaces

### 3.1 Registry Interface

The Registry is the core abstraction for service management:

```go
// Registry defines the contract for service registration and discovery
type Registry interface {
    // Register adds a service to the registry
    // If the service already exists, it updates the registration
    Register(service *Service) error
    
    // Deregister removes a service from the registry
    Deregister(name, id string) error
    
    // Discover returns all healthy instances of a service
    // Returns nil if service not found
    Discover(name string) []*Service
    
    // GetService returns a specific service instance by ID
    GetService(name, id string) (*Service, bool)
    
    // SetHealthy marks a service as healthy or unhealthy
    SetHealthy(name, id string, healthy bool) error
    
    // Heartbeat updates the last seen timestamp for a service
    // Used by services to indicate they are alive
    Heartbeat(name, id string) error
    
    // ListServices returns all registered services with their instances
    ListServices() map[string][]*Service
    
    // Watch returns a channel that receives service change events
    // Future enhancement for real-time updates
    Watch(name string) (<-chan ServiceEvent, error)
}

// Service represents a registered service instance
type Service struct {
    // ID is a unique identifier for this instance
    ID string
    
    // Name is the service type/name
    Name string
    
    // Address is the host/IP address
    Address string
    
    // Port is the service port
    Port int
    
    // Metadata contains arbitrary key-value pairs
    Metadata map[string]string
    
    // Healthy indicates if the service is healthy
    Healthy bool
    
    // LastSeen is the timestamp of last heartbeat
    LastSeen time.Time
    
    // RegisteredAt is when the service was first registered
    RegisteredAt time.Time
    
    // HealthCheckPath is the path for HTTP health checks
    // Default: "/health"
    HealthCheckPath string
}

// ServiceEvent represents a registry change event
type ServiceEvent struct {
    Type      EventType
    Service   *Service
    Timestamp time.Time
}

type EventType string

const (
    EventRegistered   EventType = "registered"
    EventDeregistered EventType = "deregistered"
    EventHealthChange EventType = "health_changed"
)

// RegistryError provides structured error information
type RegistryError struct {
    Code    ErrorCode
    Message string
    Cause   error
}

type ErrorCode string

const (
    ErrCodeNotFound     ErrorCode = "not_found"
    ErrCodeInvalidInput ErrorCode = "invalid_input"
    ErrCodeInternal     ErrorCode = "internal_error"
    ErrCodeTimeout      ErrorCode = "timeout"
)
```

### 3.2 Load Balancer Interface

```go
// LoadBalancer provides service instance selection
type LoadBalancer interface {
    // Next returns the next service instance for the given service name
    // Returns error if no healthy instances available
    Next(serviceName string) (*Service, error)
    
    // Name returns the load balancer algorithm name
    Name() string
}

// RoundRobinLB implements round-robin load balancing
type RoundRobinLB struct {
    registry *Registry
    counters sync.Map // serviceName -> *atomic.Uint64
}

// NewRoundRobinLB creates a round-robin load balancer
func NewRoundRobinLB(registry Registry) *RoundRobinLB

// Next implements the LoadBalancer interface
func (lb *RoundRobinLB) Next(serviceName string) (*Service, error)

// LeastConnectionsLB implements least-connections load balancing
type LeastConnectionsLB struct {
    registry  Registry
    counters  map[string]*int32 // serviceID -> connection count
    mu        sync.RWMutex
}

// NewLeastConnectionsLB creates a least-connections load balancer
func NewLeastConnectionsLB(registry Registry) *LeastConnectionsLB

// Next implements the LoadBalancer interface
func (lb *LeastConnectionsLB) Next(serviceName string) (*Service, error)

// Release decrements the connection count for a service
func (lb *LeastConnectionsLB) Release(serviceID string)
```

### 3.3 Health Checker Interface

```go
// HealthChecker performs health checks on registered services
type HealthChecker interface {
    // Start begins the health check loop
    // Runs until context is cancelled
    Start(ctx context.Context)
    
    // Check performs a one-time health check on a service
    Check(service *Service) HealthStatus
    
    // Stop stops the health checker
    Stop()
}

// HealthStatus represents the health status of a service
type HealthStatus int

const (
    HealthStatusUnknown HealthStatus = iota
    HealthStatusHealthy
    HealthStatusUnhealthy
    HealthStatusDegraded
)

// HealthCheckConfig defines health check parameters
type HealthCheckConfig struct {
    // Type is the health check type: http, tcp, grpc
    Type string
    
    // Path is the HTTP path for health checks
    Path string
    
    // Interval is the time between health checks
    Interval time.Duration
    
    // Timeout is the maximum time for a health check
    Timeout time.Duration
    
    // HealthyThreshold is consecutive successes to mark healthy
    HealthyThreshold int
    
    // UnhealthyThreshold is consecutive failures to mark unhealthy
    UnhealthyThreshold int
}

// HTTPHealthChecker performs HTTP health checks
type HTTPHealthChecker struct {
    registry Registry
    client   *http.Client
    config   HealthCheckConfig
    logger   *slog.Logger
}

// NewHTTPHealthChecker creates an HTTP health checker
func NewHTTPHealthChecker(registry Registry, config HealthCheckConfig) *HTTPHealthChecker
```

---

## 4. Data Models

### 4.1 Service Model

```go
// ServiceModel is the internal representation
type ServiceModel struct {
    ID               string            `json:"id"`
    Name             string            `json:"name"`
    Address          string            `json:"address"`
    Port             int               `json:"port"`
    Metadata         map[string]string `json:"metadata,omitempty"`
    Healthy          bool              `json:"healthy"`
    LastSeen         time.Time         `json:"last_seen"`
    RegisteredAt     time.Time         `json:"registered_at"`
    HealthCheckPath  string            `json:"health_check_path,omitempty"`
    
    // Internal fields (not serialized)
    mu               sync.RWMutex      `json:"-"`
    consecutiveSuccesses int           `json:"-"`
    consecutiveFailures  int           `json:"-"`
}

// Internal storage structure
type RegistryStore struct {
    // services is the main storage: name -> id -> service
    services map[string]map[string]*ServiceModel
    
    // mu protects the services map
    mu sync.RWMutex
    
    // healthyIndex is a derived index for fast healthy lookups
    // name -> set of healthy service IDs
    healthyIndex map[string]map[string]struct{}
}
```

### 4.2 Health Check Model

```go
// HealthCheckResult captures the result of a health check
type HealthCheckResult struct {
    ServiceID string
    Status    HealthStatus
    Timestamp time.Time
    Duration  time.Duration
    Error     error
    HTTPCode  int // For HTTP checks
}

// HealthCheckHistory maintains check history for a service
type HealthCheckHistory struct {
    ServiceID        string
    Results          []HealthCheckResult // Ring buffer
    CurrentIndex     int
    Capacity         int
    
    // Threshold tracking
    ConsecutiveSuccesses int
    ConsecutiveFailures  int
}

// Record adds a new result to history
func (h *HealthCheckHistory) Record(result HealthCheckResult) {
    h.Results[h.CurrentIndex] = result
    h.CurrentIndex = (h.CurrentIndex + 1) % h.Capacity
    
    if result.Status == HealthStatusHealthy {
        h.ConsecutiveSuccesses++
        h.ConsecutiveFailures = 0
    } else {
        h.ConsecutiveFailures++
        h.ConsecutiveSuccesses = 0
    }
}

// ShouldMarkHealthy returns true if service should transition to healthy
func (h *HealthCheckHistory) ShouldMarkHealthy(threshold int) bool {
    return h.ConsecutiveSuccesses >= threshold
}

// ShouldMarkUnhealthy returns true if service should transition to unhealthy
func (h *HealthCheckHistory) ShouldMarkUnhealthy(threshold int) bool {
    return h.ConsecutiveFailures >= threshold
}
```

### 4.3 Registry State Model

```go
// RegistryState captures the complete registry state for snapshots
type RegistryState struct {
    Version   int64                  `json:"version"`
    Timestamp time.Time              `json:"timestamp"`
    Services  map[string]ServiceList `json:"services"`
}

type ServiceList struct {
    Name      string         `json:"name"`
    Instances []ServiceModel `json:"instances"`
}

// ExportState exports the current registry state
func (r *Registry) ExportState() RegistryState {
    r.mu.RLock()
    defer r.mu.RUnlock()
    
    state := RegistryState{
        Version:   atomic.AddInt64(&r.version, 0),
        Timestamp: time.Now(),
        Services:  make(map[string]ServiceList),
    }
    
    for name, instances := range r.services {
        list := ServiceList{Name: name}
        for _, svc := range instances {
            list.Instances = append(list.Instances, *svc)
        }
        state.Services[name] = list
    }
    
    return state
}
```

---

## 5. Behavior

### 5.1 Service Lifecycle

#### 5.1.1 State Machine

```
                    ┌─────────┐
                    │  INIT   │
                    └────┬────┘
                         │ Register()
                         ▼
              ┌───────────────────┐
              │     PENDING       │
              │  (first check)    │
              └────────┬──────────┘
                       │
              ┌────────┴──────────┐
              │                   │
              ▼                   ▼
     ┌─────────────────┐  ┌──────────────┐
     │    HEALTHY      │  │   UNHEALTHY  │
     │   (serving)     │  │   (waiting)  │
     └────────┬────────┘  └──────┬───────┘
              │                  │
              │ Health Check     │ Health Check
              │                  │
     ┌────────┴────────┐        │
     │                   │        │
     ▼                   ▼        ▼
┌─────────────┐  ┌─────────────┐  ┌──────────────┐
│  DEGRADED   │  │   FAILED    │  │   REMOVED    │
│ (warnings)  │  │ (too many   │  │ (manual or   │
│             │  │  failures)  │  │  expired)    │
└─────────────┘  └─────────────┘  └──────────────┘
```

#### 5.1.2 State Transitions

| Current State | Event | Next State | Action |
|---------------|-------|------------|--------|
| INIT | Register() | PENDING | Add to registry, start health checks |
| PENDING | Health OK | HEALTHY | Mark healthy, available for discovery |
| PENDING | Health Fail | UNHEALTHY | Keep checking, not discoverable |
| HEALTHY | Health Fail | DEGRADED | Log warning, continue serving |
| HEALTHY | Health Fail x3 | FAILED | Mark unhealthy, remove from discovery |
| UNHEALTHY | Health OK x2 | HEALTHY | Mark healthy, add to discovery |
| Any | Deregister() | REMOVED | Remove from registry |
| Any | Expire (no heartbeat) | REMOVED | Remove from registry |

### 5.2 Concurrency Model

The registry uses a read-heavy locking strategy:

```go
// Read operations use RLock
func (r *Registry) Discover(name string) []*Service {
    r.mu.RLock()
    defer r.mu.RUnlock()
    
    // Fast path: read from healthy index
    services, ok := r.healthyIndex[name]
    if !ok {
        return nil
    }
    
    result := make([]*Service, 0, len(services))
    for id := range services {
        if svc, ok := r.services[name][id]; ok {
            result = append(result, svc)
        }
    }
    
    return result
}

// Write operations use Lock
func (r *Registry) Register(service *Service) error {
    r.mu.Lock()
    defer r.mu.Unlock()
    
    if r.services[service.Name] == nil {
        r.services[service.Name] = make(map[string]*Service)
    }
    
    service.LastSeen = time.Now()
    service.RegisteredAt = time.Now()
    
    // Update main storage
    r.services[service.Name][service.ID] = service
    
    // Update healthy index if healthy
    if service.Healthy {
        if r.healthyIndex[service.Name] == nil {
            r.healthyIndex[service.Name] = make(map[string]struct{})
        }
        r.healthyIndex[service.Name][service.ID] = struct{}{}
    }
    
    // Increment version for change tracking
    atomic.AddInt64(&r.version, 1)
    
    return nil
}
```

### 5.3 Health Check Behavior

```go
// Health check execution with thresholds
func (hc *HTTPHealthChecker) evaluateHealth(svc *Service, result HealthCheckResult) {
    history := hc.getOrCreateHistory(svc.ID)
    history.Record(result)
    
    currentStatus := svc.Healthy
    
    switch result.Status {
    case HealthStatusHealthy:
        if !currentStatus && history.ShouldMarkHealthy(hc.config.HealthyThreshold) {
            hc.registry.SetHealthy(svc.Name, svc.ID, true)
            hc.logger.Info("service marked healthy",
                "service", svc.Name,
                "id", svc.ID,
                "consecutive_successes", history.ConsecutiveSuccesses)
        }
        
    case HealthStatusUnhealthy:
        if currentStatus && history.ShouldMarkUnhealthy(hc.config.UnhealthyThreshold) {
            hc.registry.SetHealthy(svc.Name, svc.ID, false)
            hc.logger.Warn("service marked unhealthy",
                "service", svc.Name,
                "id", svc.ID,
                "consecutive_failures", history.ConsecutiveFailures,
                "error", result.Error)
        }
    }
}
```

---

## 6. Configuration

### 6.1 Default Configuration

```go
// DefaultConfig provides sensible defaults
var DefaultConfig = Config{
    Registry: RegistryConfig{
        MaxServices:      10000,
        MaxInstances:     100000,
        HeartbeatTimeout: 30 * time.Second,
    },
    HealthCheck: HealthCheckConfig{
        Type:               "http",
        Path:               "/health",
        Interval:           10 * time.Second,
        Timeout:            5 * time.Second,
        HealthyThreshold:   2,
        UnhealthyThreshold: 3,
    },
    LoadBalancer: LoadBalancerConfig{
        Type:          "round_robin",
        RetryAttempts: 3,
    },
}

// Config holds all discovery configuration
type Config struct {
    Registry     RegistryConfig     `yaml:"registry"`
    HealthCheck  HealthCheckConfig  `yaml:"health_check"`
    LoadBalancer LoadBalancerConfig `yaml:"load_balancer"`
}
```

### 6.2 Configuration File

```yaml
# discovery.yaml
registry:
  max_services: 10000
  max_instances: 100000
  heartbeat_timeout: 30s

health_check:
  type: http
  path: /health
  interval: 10s
  timeout: 5s
  healthy_threshold: 2
  unhealthy_threshold: 3

load_balancer:
  type: round_robin
  retry_attempts: 3

# Per-service overrides
services:
  database:
    health_check:
      type: tcp
      interval: 5s
      timeout: 2s
      unhealthy_threshold: 5
  
  api-gateway:
    health_check:
      path: /health/ready
      interval: 5s
      unhealthy_threshold: 2
```

---

## 7. Operations

### 7.1 API Endpoints

If exposed via HTTP:

```
POST /v1/services/register
  Request:  Service registration
  Response: Registration confirmation

DELETE /v1/services/{name}/{id}
  Response: Deregistration confirmation

GET /v1/services/{name}
  Response: List of healthy instances

GET /v1/services/{name}/{id}
  Response: Specific service instance

POST /v1/services/{name}/{id}/heartbeat
  Response: Heartbeat acknowledgment

GET /v1/services
  Response: All registered services
```

### 7.2 CLI Commands

```bash
# Register a service
discovery register \
  --name api-service \
  --id instance-1 \
  --address 10.0.1.5 \
  --port 8080 \
  --health-path /health

# Discover services
discovery discover --name api-service

# List all services
discovery list

# Health check status
discovery health --name api-service

# Watch for changes
discovery watch --name api-service
```

### 7.3 Metrics

Prometheus metrics exported:

```go
var (
    registrySize = prometheus.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "discovery_registry_size",
            Help: "Number of registered services",
        },
        []string{"service_name"},
    )
    
    healthCheckDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "discovery_health_check_duration_seconds",
            Help:    "Health check duration",
            Buckets: prometheus.DefBuckets,
        },
        []string{"service_name", "status"},
    )
    
    loadBalancerSelections = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "discovery_lb_selections_total",
            Help: "Total load balancer selections",
        },
        []string{"service_name", "algorithm"},
    )
    
    serviceEvents = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "discovery_service_events_total",
            Help: "Total service events",
        },
        []string{"event_type", "service_name"},
    )
)
```

---

## 8. Security

### 8.1 Authentication

Future enhancement - currently internal use only:

```go
// Authenticator interface for registry access
type Authenticator interface {
    Authenticate(token string) (*Identity, error)
    Authorize(identity *Identity, action Action, resource Resource) bool
}
```

### 8.2 Network Security

```yaml
# NetworkPolicy for Kubernetes deployment
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: discovery-network-policy
spec:
  podSelector:
    matchLabels:
      app: discovery
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: phenotype-system
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: TCP
          port: 8080
```

---

## 9. Testing

### 9.1 Unit Tests

```go
func TestRegistry_Register(t *testing.T) {
    r := New()
    
    svc := &Service{
        ID:      "test-1",
        Name:    "test-service",
        Address: "10.0.0.1",
        Port:    8080,
    }
    
    err := r.Register(svc)
    require.NoError(t, err)
    
    // Verify registration
    found, ok := r.GetService("test-service", "test-1")
    require.True(t, ok)
    assert.Equal(t, svc.Address, found.Address)
}

func TestRegistry_Discover(t *testing.T) {
    r := New()
    
    // Register healthy services
    for i := 0; i < 3; i++ {
        r.Register(&Service{
            ID:      fmt.Sprintf("svc-%d", i),
            Name:    "api",
            Address: fmt.Sprintf("10.0.0.%d", i),
            Port:    8080,
            Healthy: true,
        })
    }
    
    // Register unhealthy service
    r.Register(&Service{
        ID:      "svc-unhealthy",
        Name:    "api",
        Address: "10.0.0.99",
        Port:    8080,
        Healthy: false,
    })
    
    // Discover should only return healthy
    services := r.Discover("api")
    assert.Len(t, services, 3)
}
```

### 9.2 Integration Tests

```go
func TestDiscovery_Integration(t *testing.T) {
    if os.Getenv("INTEGRATION") != "true" {
        t.Skip("Set INTEGRATION=true to run")
    }
    
    // Start test HTTP server
    server := httptest.NewServer(http.HandlerFunc(
        func(w http.ResponseWriter, r *http.Request) {
            if r.URL.Path == "/health" {
                w.WriteHeader(http.StatusOK)
                return
            }
            w.WriteHeader(http.StatusNotFound)
        }))
    defer server.Close()
    
    // Create registry and health checker
    registry := New()
    
    addr := strings.TrimPrefix(server.URL, "http://")
    parts := strings.Split(addr, ":")
    port, _ := strconv.Atoi(parts[1])
    
    svc := &Service{
        ID:      "test-1",
        Name:    "test-service",
        Address: parts[0],
        Port:    port,
        Healthy: false,
    }
    
    registry.Register(svc)
    
    // Start health checker
    hc := NewHTTPHealthChecker(registry, HealthCheckConfig{
        Interval:           1 * time.Second,
        Timeout:            2 * time.Second,
        HealthyThreshold:   1,
        UnhealthyThreshold: 2,
    })
    
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    
    go hc.Start(ctx)
    
    // Wait for health check to mark service healthy
    time.Sleep(3 * time.Second)
    
    // Verify service is healthy
    services := registry.Discover("test-service")
    assert.Len(t, services, 1)
    assert.True(t, services[0].Healthy)
}
```

### 9.3 Load Tests

```go
func BenchmarkRegistry_Discover(b *testing.B) {
    r := New()
    
    // Setup: register 1000 services
    for i := 0; i < 1000; i++ {
        r.Register(&Service{
            ID:      fmt.Sprintf("svc-%d", i),
            Name:    "benchmark-service",
            Address: fmt.Sprintf("10.0.0.%d", i%256),
            Port:    8080,
            Healthy: i%10 != 0, // 90% healthy
        })
    }
    
    b.ResetTimer()
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            _ = r.Discover("benchmark-service")
        }
    })
}
```

---

## 10. Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Service** | An application component that provides functionality |
| **Instance** | A specific running copy of a service |
| **Registry** | Storage for service locations and metadata |
| **Health Check** | Probe to determine if a service is functioning |
| **Load Balancer** | Component that distributes traffic across instances |
| **Round Robin** | Sequential selection of instances |
| **Heartbeat** | Periodic signal indicating a service is alive |

### Appendix B: Error Codes

| Code | Description |
|------|-------------|
| NOT_FOUND | Service or instance not found in registry |
| INVALID_INPUT | Invalid registration parameters |
| INTERNAL_ERROR | Unexpected internal error |
| TIMEOUT | Operation timed out |
| ALREADY_EXISTS | Service with ID already registered |

### Appendix C: References

1. [Consul Documentation](https://www.consul.io/docs/)
2. [etcd Documentation](https://etcd.io/docs/)
3. [Kubernetes Services](https://kubernetes.io/docs/concepts/services-networking/service/)
4. [AWS Cloud Map](https://docs.aws.amazon.com/cloud-map/)
5. [Raft Consensus](https://raft.github.io/)

---

*End of Specification*
