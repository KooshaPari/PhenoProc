# cors Specification

**Version:** 1.0.0  
**Status:** Stable  
**Date:** 2026-04-05  

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Reference](#api-reference)
4. [Security](#security)
5. [Examples](#examples)
6. [Appendices](#appendices)

---

## Overview

The `cors` library provides CORS (Cross-Origin Resource Sharing) middleware for Go HTTP servers.

### Purpose

- Handle cross-origin requests
- Support preflight OPTIONS requests
- Configurable origin validation
- Production-safe defaults

---

## Architecture

### Request Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CORS Request Flow                                    │
│                                                                             │
│  Browser Request                                                            │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  CORS Middleware                                                     │    │
│  │                                                                      │    │
│  │  ┌─────────────┐                                                    │    │
│  │  │ Is OPTIONS? │                                                    │    │
│  │  └──────┬──────┘                                                    │    │
│  │      Yes│No                                                         │    │
│  │         │                                                           │    │
│  │    ┌────┴────┐                                                      │    │
│  │    ▼         ▼                                                      │    │
│  │ ┌──────┐  ┌─────────┐                                               │    │
│  │ │Handle│  │Set CORS │                                               │    │
│  │ │Pre-  │  │Headers  │                                               │    │
│  │ │flight│  │         │                                               │    │
│  │ │204   │  │Continue │                                               │    │
│  │ └──────┘  └────┬────┘                                               │    │
│  │                │                                                    │    │
│  │                ▼                                                    │    │
│  │         ┌──────────┐                                                │    │
│  │         │  Next    │                                                │    │
│  │         │ Handler  │                                                │    │
│  │         └──────────┘                                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## API Reference

### Config

```go
type Config struct {
    AllowedOrigins   []string // Allowed origins (empty = all)
    AllowedMethods   []string // Default: [GET, POST, PUT, DELETE, PATCH, OPTIONS]
    AllowedHeaders   []string // Default: [Content-Type, Authorization, X-API-Key]
    ExposedHeaders   []string // Headers browser can access
    AllowCredentials bool     // Allow cookies/auth headers
    MaxAge           int      // Preflight cache duration (seconds)
}
```

### Middleware

```go
func Middleware(cfg Config) func(http.Handler) http.Handler

func PreflightHandler() http.Handler
```

---

## Security

### Security Checklist

```
□ Never use wildcard (*) with AllowCredentials: true
□ Validate origins against explicit allowlist in production
□ Set appropriate MaxAge for caching
□ Include Vary: Origin header for dynamic origins
□ Reject null origin in production
□ Use HTTPS in production
```

### Secure Configuration

```go
func secureCORS() func(http.Handler) http.Handler {
    return cors.Middleware(cors.Config{
        AllowedOrigins:   []string{"https://app.example.com"},
        AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE"},
        AllowedHeaders:   []string{"Content-Type", "Authorization"},
        ExposedHeaders:   []string{"X-Request-ID"},
        AllowCredentials: true,
        MaxAge:           86400,
    })
}
```

---

## Examples

### Basic Middleware

```go
package main

import (
    "net/http"
    
    "github.com/coder/cors"
)

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("/api/", handleAPI)
    
    // Apply CORS middleware
    handler := cors.Middleware(cors.Config{
        AllowedOrigins: []string{"https://frontend.example.com"},
        AllowedMethods: []string{"GET", "POST", "PUT", "DELETE"},
        AllowedHeaders: []string{"Content-Type", "Authorization"},
    })(mux)
    
    http.ListenAndServe(":8080", handler)
}
```

### Standalone Preflight Handler

```go
func main() {
    mux := http.NewServeMux()
    
    // Dedicated OPTIONS handler
    mux.Handle("/api/", cors.PreflightHandler())
    mux.HandleFunc("/api/users", handleUsers)
    
    http.ListenAndServe(":8080", mux)
}
```

### Development Configuration

```go
func devCORS() func(http.Handler) http.Handler {
    return cors.Middleware(cors.Config{
        AllowedOrigins:   []string{},  // Allow all
        AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "PATCH"},
        AllowedHeaders:   []string{"*"},
        AllowCredentials: false,  // No credentials in dev
        MaxAge:           300,
    })
}
```

---

## Appendices

### Appendix A: CORS Headers Reference

| Header | Simple | Preflight | Description |
|--------|--------|-----------|-------------|
| Access-Control-Allow-Origin | ✓ | ✓ | Allowed origin |
| Access-Control-Allow-Methods | ✗ | ✓ | Allowed HTTP methods |
| Access-Control-Allow-Headers | ✗ | ✓ | Allowed request headers |
| Access-Control-Allow-Credentials | ✓ | ✓ | Allow credentials |
| Access-Control-Expose-Headers | ✓ | ✗ | Accessible response headers |
| Access-Control-Max-Age | ✗ | ✓ | Preflight cache time |

---

*Specification Version: 1.0.0*  
*Last Updated: 2026-04-05*
