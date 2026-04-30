# Registry Library - State of the Art

> Generic Service Registry with Owner Tracking - Dependency Management

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-04-05

---

## Part I: Service Registry Landscape (2024-2026)

### 1.1 Registry Evolution

Service registries have evolved from simple DNS-based discovery to sophisticated distributed systems with health checking, load balancing, and service mesh integration.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Service Registry Evolution                             │
│                                                                             │
│  Static Files → DNS SRV → ZooKeeper → Consul → etcd → Kubernetes → Mesh   │
│                                                                             │
│  2000        2005       2008       2014      2014      2015       2018+       │
│    │           │          │          │         │         │          │      │
│    ▼           ▼          ▼          ▼         ▼         ▼          ▼      │
│  ┌────┐     ┌────┐    ┌────┐    ┌────┐   ┌────┐   ┌────┐    ┌────┐      │
│  │/etc│     │SRV │    │ ZK │    │Cons│   │etcd│   │K8s │    │Ist │      │
│  │host│     │rec │    │    │    │ul  │   │    │   │SD  │    │io │      │
│  └────┘     └────┘    └────┘    └────┘   └────┘   └────┘    └────┘      │
│                                                                             │
│  Manual     Service   Coordination Discovery  K/V     Container  Sidecar   │
│  config     location  service    + health   store   native     proxy     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Registry Types Comparison

| Registry | Consensus | Protocol | Health Check | Multi-DC | Best For |
|----------|-----------|----------|--------------|----------|----------|
| **Consul** | Raft | HTTP/gRPC | Native | Yes | VM-based |
| **etcd** | Raft | gRPC | Via proxy | Yes | Kubernetes |
| **ZooKeeper** | ZAB | Custom TCP | Via Curator | Complex | Hadoop |
| **Eureka** | Self-preservation | HTTP | Native | Via zones | Netflix |
| **Nacos** | Raft | HTTP/gRPC | Native | Yes | Alibaba |
| **K8s DNS** | N/A | DNS | Liveness probe | Via federation | K8s native |

### 1.3 Registry Capabilities Matrix

| Capability | Basic | Advanced | Enterprise |
|------------|-------|----------|------------|
| **Registration** | Manual | Self | Auto-discovery |
| **Discovery** | DNS | Client-side LB | Server-side LB |
| **Health Checks** | Passive | Active | Deep |
| **Routing** | Random | Weighted | Custom rules |
| **Security** | None | mTLS | Zero trust |
| **Observability** | Logs | Metrics | Full tracing |

---

## Part II: Registry Patterns

### 2.1 Registration Patterns

| Pattern | Pros | Cons | Use Case |
|---------|------|------|----------|
| **Self-registration** | Simple, no orchestrator needed | Lifecycle coupling, restart issues | Simple services |
| **Third-party** | Decoupled, flexible | Additional complexity, SPOF | Kubernetes, Cloud |
| **Registrator** | Automatic, container-native | Sidecar overhead, complexity | Docker, Nomad |

### 2.2 Discovery Patterns

| Pattern | Implementation | Latency | Complexity |
|---------|----------------|---------|------------|
| **Client-side** | Ribbon, gRPC-LB | Low | High (client logic) |
| **Server-side** | Traefik, Envoy | Medium | Medium (proxy layer) |
| **DNS-based** | Consul DNS, CoreDNS | Medium | Low (standard DNS) |
| **Service Mesh** | Istio, Linkerd | Low | Very High |

### 2.3 Consistency Models

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Registry Consistency Spectrum                            │
│                                                                             │
│  Strong ────────────────────────────────────────────────────► Eventual    │
│                                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Paxos     │  │   Raft     │  │   Gossip   │  │  CRDTs     │            │
│  │  (ZK)      │  │  (etcd)    │  │  (Serf)    │  │  (Riak)    │            │
│  │            │  │            │  │            │  │            │            │
│  │  Writes    │  │  Majority  │  │  Propagate │  │  Merge     │            │
│  │  require   │  │  read      │  │  changes   │  │  conflicts │            │
│  │  consensus │  │            │  │            │  │            │            │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘            │
│                                                                             │
│  Use: Financial   Use: K8s/etcd    Use: Large      Use: Edge              │
│  transactions     clusters         clusters        devices                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part III: Registry Implementation Patterns

### 3.1 Generic Registry Design

```go
// Generic Registry with Owner Tracking
type Registry[K comparable, V any] struct {
    mu        sync.RWMutex
    entries   map[K]*entry[V]
    ownerKeys map[string][]K
    hook      Hook[K, V]
}

type entry[V any] struct {
    value V
    count int  // Reference count
}

// Operations
func (r *Registry[K, V]) Register(ownerID string, key K, value V)
func (r *Registry[K, V]) Unregister(ownerID string)
func (r *Registry[K, V]) Get(key K) (V, bool)
func (r *Registry[K, V]) List() map[K]V
```

### 3.2 Reference Counting

Reference counting enables multiple owners to share resources while ensuring cleanup when all owners release.

| Scenario | Count | Action |
|----------|-------|--------|
| First registration | 0 → 1 | Create entry |
| Second registration | 1 → 2 | Increment count |
| First unregistration | 2 → 1 | Decrement count |
| Last unregistration | 1 → 0 | Delete entry |

### 3.3 Lifecycle Hooks

```go
type Hook[K comparable, V any] interface {
    OnRegister(ownerID string, key K, value V)
    OnUnregister(ownerID string)
}
```

| Hook Use Case | Example |
|---------------|---------|
| **Metrics** | Track registered services |
| **Logging** | Audit registration events |
| **Cleanup** | Release associated resources |
| **Validation** | Verify registration allowed |

---

## Part IV: Performance & Scalability

### 4.1 Performance Characteristics

| Operation | Time Complexity | Space Complexity | Lock Type |
|-----------|-----------------|------------------|-----------|
| Register | O(1) | O(1) | Write |
| Unregister | O(n) where n = keys per owner | O(1) | Write |
| Get | O(1) | O(1) | Read |
| List | O(n) where n = total entries | O(n) | Read |

### 4.2 Scalability Limits

| Resource | Soft Limit | Hard Limit | Mitigation |
|----------|------------|------------|------------|
| Registry entries | 100K | 1M | Sharding |
| Owners | 10K | 100K | Partitioning |
| Operations/sec | 10K | 100K | Caching |

---

## Part V: References

| Resource | URL | Description |
|----------|-----|-------------|
| Consul | https://www.consul.io | HashiCorp service mesh |
| etcd | https://etcd.io | Kubernetes backing store |
| ZooKeeper | https://zookeeper.apache.org | Apache coordination |
| Eureka | https://github.com/Netflix/eureka | Netflix registry |

---

*This document reflects SOTA in service registry patterns as of April 2026.*
