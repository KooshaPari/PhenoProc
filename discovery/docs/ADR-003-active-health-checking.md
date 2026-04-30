# ADR-003: Active Health Checking

## Status
**Accepted**

## Context

The service registry needs to detect and remove unhealthy service instances to prevent routing traffic to failed services. We must choose between active health checking (proactive probing) and passive health checking (detecting failures from actual traffic).

### Requirements

1. **Timeliness:** Detect failures quickly to minimize failed requests
2. **Accuracy:** Minimize false positives (healthy marked unhealthy)
3. **Efficiency:** Minimize overhead on services being checked
4. **Flexibility:** Support different health check types

### Options Considered

| Approach | Pros | Cons |
|----------|------|------|
| **Active (HTTP/TCP probes)** | Proactive detection, works without traffic | Additional load, potential false positives |
| **Passive (Circuit breaker)** | No additional load, real traffic based | Slower detection, requires traffic |
| **Both Combined** | Best of both | More complexity |
| **Agent-based** | Rich health info | Requires agent deployment |

## Decision

**We will implement active health checking** with HTTP probes as the primary mechanism, with design considerations for adding passive checks later.

### Rationale

1. **Proactive:** Detects failures before they affect users
2. **Standard:** HTTP health endpoints are standard practice
3. **Configurable:** Different intervals and thresholds per service
4. **Extendable:** Can add TCP, gRPC checks later

### Consequences

**Positive:**
- Fast failure detection
- Standard HTTP health checks
- Configurable per service
- Works without production traffic

**Negative:**
- Generates additional load
- Requires health endpoint implementation
- Potential false positives from network issues
- Must balance frequency vs. overhead

## Implementation

### Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Health Checking System                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    HealthChecker                         │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │  │
│  │  │   HTTP      │  │    TCP      │  │    gRPC     │         │  │
│  │  │   Probes    │  │   Probes    │  │   Probes    │         │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │  │
│  │         │                │                │               │  │
│  │         └────────────────┼────────────────┘               │  │
│  │                          │                                │  │
│  │                   ┌──────▼──────┐                         │  │
│  │                   │  Results    │                         │  │
│  │                   │  Processor  │                         │  │
│  │                   └──────┬──────┘                         │  │
│  │                          │                                │  │
│  │                   ┌──────▼──────┐                         │  │
│  │                   │  Registry   │                         │  │
│  │                   │  Updates    │                         │  │
│  │                   └─────────────┘                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Core Implementation

```go
// HealthChecker periodically checks service health
type HealthChecker struct {
    registry *Registry
    client   *http.Client
    interval time.Duration
    timeout  time.Duration
    logger   *slog.Logger
}

// HealthCheckConfig defines health check parameters
type HealthCheckConfig struct {
    Type     string        // http, tcp, grpc
    Path     string        // for HTTP checks
    Interval time.Duration
    Timeout  time.Duration
    HealthyThreshold   int // Consecutive successes to mark healthy
    UnhealthyThreshold int // Consecutive failures to mark unhealthy
}

// NewHealthChecker creates a new health checker
func NewHealthChecker(registry *Registry, interval, timeout time.Duration) *HealthChecker {
    return &HealthChecker{
        registry: registry,
        client:   &http.Client{Timeout: timeout},
        interval: interval,
        timeout:  timeout,
        logger:   slog.Default(),
    }
}

// Start begins the health check loop
func (hc *HealthChecker) Start(ctx context.Context) {
    ticker := time.NewTicker(hc.interval)
    defer ticker.Stop()
    
    for {
        select {
        case <-ctx.Done():
            hc.logger.Info("health checker stopping")
            return
        case <-ticker.C:
            hc.checkAllServices()
        }
    }
}

func (hc *HealthChecker) checkAllServices() {
    services := hc.registry.ListServices()
    
    var wg sync.WaitGroup
    for _, instances := range services {
        for _, svc := range instances {
            wg.Add(1)
            go func(service *Service) {
                defer wg.Done()
                hc.checkService(service)
            }(svc)
        }
    }
    
    wg.Wait()
}

func (hc *HealthChecker) checkService(svc *Service) {
    ctx, cancel := context.WithTimeout(context.Background(), hc.timeout)
    defer cancel()
    
    healthURL := fmt.Sprintf("http://%s:%d/health", svc.Address, svc.Port)
    
    req, err := http.NewRequestWithContext(ctx, "GET", healthURL, nil)
    if err != nil {
        hc.logger.Error("failed to create health check request",
            "service", svc.Name,
            "id", svc.ID,
            "error", err)
        return
    }
    
    start := time.Now()
    resp, err := hc.client.Do(req)
    duration := time.Since(start)
    
    if err != nil {
        hc.logger.Warn("health check failed",
            "service", svc.Name,
            "id", svc.ID,
            "error", err,
            "duration", duration)
        
        if err := hc.registry.SetHealthy(svc.Name, svc.ID, false); err != nil {
            hc.logger.Error("failed to mark service unhealthy",
                "service", svc.Name,
                "id", svc.ID,
                "error", err)
        }
        return
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        hc.logger.Warn("health check returned non-OK status",
            "service", svc.Name,
            "id", svc.ID,
            "status", resp.StatusCode,
            "duration", duration)
        
        if err := hc.registry.SetHealthy(svc.Name, svc.ID, false); err != nil {
            hc.logger.Error("failed to mark service unhealthy",
                "service", svc.Name,
                "id", svc.ID,
                "error", err)
        }
        return
    }
    
    hc.logger.Debug("health check passed",
        "service", svc.Name,
        "id", svc.ID,
        "duration", duration)
    
    // Update heartbeat
    if err := hc.registry.Heartbeat(svc.Name, svc.ID); err != nil {
        hc.logger.Error("failed to update heartbeat",
            "service", svc.Name,
            "id", svc.ID,
            "error", err)
    }
    
    // Mark healthy if not already
    if !svc.Healthy {
        if err := hc.registry.SetHealthy(svc.Name, svc.ID, true); err != nil {
            hc.logger.Error("failed to mark service healthy",
                "service", svc.Name,
                "id", svc.ID,
                "error", err)
        }
    }
}
```

### TCP Health Check

```go
// TCPHealthChecker performs TCP connection checks
type TCPHealthChecker struct {
    registry *Registry
    timeout  time.Duration
}

func (tc *TCPHealthChecker) Check(svc *Service) bool {
    address := fmt.Sprintf("%s:%d", svc.Address, svc.Port)
    
    conn, err := net.DialTimeout("tcp", address, tc.timeout)
    if err != nil {
        return false
    }
    defer conn.Close()
    
    return true
}
```

### gRPC Health Check

```go
// GRPCHealthChecker uses gRPC health protocol
// https://github.com/grpc/grpc/blob/master/doc/health-checking.md
type GRPCHealthChecker struct {
    registry *Registry
    timeout  time.Duration
}

func (gc *GRPCHealthChecker) Check(svc *Service) bool {
    address := fmt.Sprintf("%s:%d", svc.Address, svc.Port)
    
    ctx, cancel := context.WithTimeout(context.Background(), gc.timeout)
    defer cancel()
    
    conn, err := grpc.DialContext(ctx, address, grpc.WithInsecure())
    if err != nil {
        return false
    }
    defer conn.Close()
    
    healthClient := grpc_health_v1.NewHealthClient(conn)
    resp, err := healthClient.Check(ctx, &grpc_health_v1.HealthCheckRequest{
        Service: svc.Name,
    })
    
    if err != nil {
        return false
    }
    
    return resp.Status == grpc_health_v1.HealthCheckResponse_SERVING
}
```

## Configuration

### Default Health Check Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| Interval | 10s | Time between health checks |
| Timeout | 5s | Maximum time for health check |
| Healthy Threshold | 2 | Consecutive successes to mark healthy |
| Unhealthy Threshold | 3 | Consecutive failures to mark unhealthy |

### Service-Specific Configuration

```go
// Service health check configuration
var defaultHealthCheckConfig = HealthCheckConfig{
    Type:               "http",
    Path:               "/health",
    Interval:           10 * time.Second,
    Timeout:            5 * time.Second,
    HealthyThreshold:   2,
    UnhealthyThreshold: 3,
}

// Per-service overrides
var serviceHealthConfigs = map[string]HealthCheckConfig{
    "database": {
        Type:               "tcp",
        Interval:           5 * time.Second,
        Timeout:            2 * time.Second,
        UnhealthyThreshold: 5, // More tolerant for DB
    },
    "api-gateway": {
        Type:               "http",
        Path:               "/health/ready",
        Interval:           5 * time.Second,
        UnhealthyThreshold: 2, // Less tolerant for gateway
    },
}
```

## Future: Passive Health Checking

Design for adding circuit breaker pattern:

```go
// CircuitBreaker provides passive health checking
type CircuitBreaker struct {
    failureThreshold int
    successThreshold int
    timeout          time.Duration
    
    consecutiveFailures  int
    consecutiveSuccesses int
    lastFailureTime    time.Time
    state              CircuitState
}

type CircuitState int

const (
    StateClosed CircuitState = iota    // Normal operation
    StateOpen                          // Failing, reject requests
    StateHalfOpen                      // Testing if recovered
)

func (cb *CircuitBreaker) RecordResult(success bool) {
    cb.mutex.Lock()
    defer cb.mutex.Unlock()
    
    switch cb.state {
    case StateClosed:
        if success {
            cb.consecutiveFailures = 0
        } else {
            cb.consecutiveFailures++
            if cb.consecutiveFailures >= cb.failureThreshold {
                cb.state = StateOpen
                cb.lastFailureTime = time.Now()
            }
        }
        
    case StateOpen:
        if time.Since(cb.lastFailureTime) > cb.timeout {
            cb.state = StateHalfOpen
            cb.consecutiveSuccesses = 0
        }
        
    case StateHalfOpen:
        if success {
            cb.consecutiveSuccesses++
            if cb.consecutiveSuccesses >= cb.successThreshold {
                cb.state = StateClosed
                cb.consecutiveFailures = 0
            }
        } else {
            cb.state = StateOpen
            cb.lastFailureTime = time.Now()
        }
    }
}

func (cb *CircuitBreaker) Allow() bool {
    cb.mutex.RLock()
    defer cb.mutex.RUnlock()
    
    return cb.state == StateClosed || cb.state == StateHalfOpen
}
```

## Related Decisions

- ADR-001: In-Memory Service Registry
- ADR-002: Round-Robin Load Balancing

---

*Last Updated: 2026-04-05*
