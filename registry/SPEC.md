# Registry Library Specification

> Generic Service Registry with Owner Tracking - Dependency Management

**Version**: 1.0  
**Status**: Production  
**Last Updated**: 2026-04-05

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [API Reference](#3-api-reference)
4. [Configuration](#4-configuration)
5. [Usage Patterns](#5-usage-patterns)
6. [Performance](#6-performance)
7. [Appendices](#7-appendices)

---

## 1. Overview

### 1.1 Purpose

The registry library provides a generic, thread-safe key-value store with owner tracking and reference counting. It enables:

- **Resource sharing**: Multiple owners for same resource
- **Automatic cleanup**: Reference counting ensures proper disposal
- **Lifecycle hooks**: Observe registration/unregistration events
- **Type safety**: Generic keys and values

### 1.2 Goals

| Goal | Priority | Status |
|------|----------|--------|
| Generic Registry[K,V] | P0 | ✅ Implemented |
| Reference counting | P0 | ✅ Implemented |
| Owner tracking | P0 | ✅ Implemented |
| Lifecycle hooks | P1 | ✅ Implemented |
| Thread safety | P0 | ✅ Implemented |

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Registry** | Key-value store with reference counting |
| **Owner** | Entity that registers resources |
| **Entry** | Stored value with reference count |
| **Hook** | Callback for lifecycle events |
| **Reference Count** | Number of owners for an entry |

---

## 2. Architecture

### 2.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Registry Architecture                                │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    Registry[K comparable, V any]                     │   │
│  │                                                                        │   │
│  │   ┌──────────────────────────────────────────────────────────────┐    │   │
│  │   │                      Internal State                              │    │   │
│  │   │                                                                │    │   │
│  │   │   entries:   map[K]*entry[V]      // Key → Entry mapping      │    │   │
│  │   │   ownerKeys: map[string][]K        // Owner → Keys mapping    │    │   │
│  │   │   hook:      Hook[K,V]            // Optional lifecycle hook │    │   │
│  │   │   mu:        sync.RWMutex         // Thread safety           │    │   │
│  │   │                                                                │    │   │
│  │   └──────────────────────────────────────────────────────────────┘    │   │
│  │                                                                        │   │
│  │   Operations:                                                           │   │
│  │   • Register(ownerID, key, value)                                      │   │
│  │   • Unregister(ownerID)                                                │   │
│  │   • Get(key) (value, bool)                                             │   │
│  │   • List() map[K]V                                                     │   │
│  │   • Count(key) int                                                     │   │
│  │                                                                        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Entry Lifecycle:                                                           │
│                                                                             │
│  Register("owner1", "key1", val) → entries["key1"] = {val, count: 1}        │
│  Register("owner2", "key1", val) → entries["key1"] = {val, count: 2}        │
│  Unregister("owner1")           → entries["key1"] = {val, count: 1}        │
│  Unregister("owner2")           → delete(entries, "key1")                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Reference Counting

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Reference Counting Flow                                 │
│                                                                             │
│  Scenario 1: Single Owner                                                   │
│                                                                             │
│  r.Register("owner1", "service1", svc1)                                     │
│  ┌───────────┐                                                              │
│  │ service1  │ count: 1                                                     │
│  └───────────┘                                                              │
│                                                                             │
│  r.Unregister("owner1")                                                     │
│  [deleted]                                                                  │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  Scenario 2: Multiple Owners                                                │
│                                                                             │
│  r.Register("owner1", "service1", svc1)                                     │
│  ┌───────────┐                                                              │
│  │ service1  │ count: 1 ◄─── owner1                                        │
│  └───────────┘                                                              │
│                                                                             │
│  r.Register("owner2", "service1", svc1)                                     │
│  ┌───────────┐                                                              │
│  │ service1  │ count: 2 ◄─── owner1, owner2                                │
│  └───────────┘                                                              │
│                                                                             │
│  r.Unregister("owner1")                                                     │
│  ┌───────────┐                                                              │
│  │ service1  │ count: 1 ◄─── owner2                                        │
│  └───────────┘                                                              │
│                                                                             │
│  r.Unregister("owner2")                                                     │
│  [deleted]                                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. API Reference

### 3.1 Core Types

```go
// Registry is a generic, thread-safe key-value store with owner tracking
type Registry[K comparable, V any] struct {
    mu        sync.RWMutex
    entries   map[K]*entry[V]
    ownerKeys map[string][]K
    hook      Hook[K, V]
}

// entry tracks a value and its reference count
type entry[V any] struct {
    value V
    count int
}

// Hook is called when registry entries change
type Hook[K comparable, V any] interface {
    OnRegister(ownerID string, key K, value V)
    OnUnregister(ownerID string)
}
```

### 3.2 Constructor

```go
// New creates a new empty Registry
func New[K comparable, V any]() *Registry[K, V]
```

### 3.3 Methods

```go
// Register adds or increments a key under the given owner
func (r *Registry[K, V]) Register(ownerID string, key K, value V)

// Unregister removes all keys owned by ownerID
func (r *Registry[K, V]) Unregister(ownerID string)

// Get retrieves a value by key
func (r *Registry[K, V]) Get(key K) (V, bool)

// List returns a snapshot of all entries
func (r *Registry[K, V]) List() map[K]V

// Count returns the reference count for a key
func (r *Registry[K, V]) Count(key K) int

// SetHook sets an optional hook for observing changes
func (r *Registry[K, V]) SetHook(hook Hook[K, V])
```

---

## 4. Configuration

No external configuration required. All configuration is done programmatically.

---

## 5. Usage Patterns

### 5.1 Basic Usage

```go
package main

import (
    "context"
    "github.com/KooshaPari/phenotype-go-kit/registry"
)

func main() {
    // Create a registry for services
    r := registry.New[string, Service]()
    
    // Register services with owner
    r.Register("module1", "auth-service", authSvc)
    r.Register("module1", "user-service", userSvc)
    r.Register("module2", "auth-service", authSvc) // Shared
    
    // Retrieve a service
    if svc, ok := r.Get("auth-service"); ok {
        svc.Authenticate(...)
    }
    
    // Unregister all services from an owner
    r.Unregister("module1")
    // auth-service still exists (count: 1 from module2)
    
    r.Unregister("module2")
    // auth-service deleted (count: 0)
}
```

### 5.2 With Hooks

```go
// Metrics hook tracks registry usage
type MetricsHook struct {
    registered   prometheus.Counter
    unregistered prometheus.Counter
}

func (h *MetricsHook) OnRegister(ownerID string, key string, value Service) {
    h.registered.Inc()
    log.Printf("Service registered: owner=%s key=%s", ownerID, key)
}

func (h *MetricsHook) OnUnregister(ownerID string) {
    h.unregistered.Inc()
    log.Printf("Owner unregistered: owner=%s", ownerID)
}

// Usage
r := registry.New[string, Service]()
r.SetHook(&MetricsHook{...})
```

### 5.3 Multiplexer for Multiple Hooks

```go
type Multiplexer[K comparable, V any] struct {
    hooks []registry.Hook[K, V]
}

func (m *Multiplexer[K, V]) OnRegister(ownerID string, key K, value V) {
    for _, h := range m.hooks {
        h.OnRegister(ownerID, key, value)
    }
}

func (m *Multiplexer[K, V]) OnUnregister(ownerID string) {
    for _, h := range m.hooks {
        h.OnUnregister(ownerID)
    }
}

// Usage with multiple hooks
r := registry.New[string, Service]()
r.SetHook(&Multiplexer[string, Service]{
    hooks: []registry.Hook[string, Service]{
        &MetricsHook{},
        &LoggingHook{},
        &ValidationHook{},
    },
})
```

---

## 6. Performance

### 6.1 Performance Characteristics

| Operation | Time Complexity | Space Complexity | Lock Type |
|-----------|-----------------|------------------|-----------|
| Register | O(1) | O(1) | Write |
| Unregister | O(n) n=keys per owner | O(1) | Write |
| Get | O(1) | O(1) | Read |
| List | O(n) n=total entries | O(n) | Read |
| Count | O(1) | O(1) | Read |

### 6.2 Scalability Limits

| Resource | Soft Limit | Hard Limit | Mitigation |
|----------|------------|------------|------------|
| Registry entries | 100K | 1M | Sharding |
| Owners | 10K | 100K | Partitioning |
| Keys per owner | 1K | 10K | Aggregation |

---

## 7. Appendices

### 7.1 API Reference

See [registry.go](../registry.go) for complete API documentation.

### 7.2 Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-05 | Initial release |

---

*This specification defines the registry library v1.0 for Phenotype Go Kit.*
