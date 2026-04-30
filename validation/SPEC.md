# Validation Library Specification

> Flexible Data Validation for Go - Input Sanitization

**Version**: 1.0  
**Status**: Production  
**Last Updated**: 2026-04-05

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Built-in Rules](#3-built-in-rules)
4. [Usage Patterns](#4-usage-patterns)
5. [Security](#5-security)
6. [Appendices](#6-appendices)

---

## 1. Overview

### 1.1 Purpose

The validation library provides flexible, extensible data validation for Go applications. It enables:

- **Input validation**: Ensure data meets requirements
- **Rule composition**: Combine rules for complex validation
- **Custom rules**: Extend with business-specific validators
- **Clear errors**: Descriptive validation failures

### 1.2 Goals

| Goal | Priority | Status |
|------|----------|--------|
| Rule-based validation | P0 | ✅ Implemented |
| Built-in common rules | P0 | ✅ Implemented |
| Custom rule support | P1 | ✅ Implemented |
| Field-level errors | P0 | ✅ Implemented |
| Struct tag support (future) | P2 | 📋 Planned |

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Rule** | Validation check with name and message |
| **Validator** | Collection of rules for validation |
| **Field error** | Validation failure for a specific field |
| **Validation result** | Map of field names to error lists |

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Validation Architecture                                │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    Validator                                          │   │
│  │                                                                        │   │
│  │   rules: map[string][]Rule                                          │   │
│  │                                                                        │   │
│  │   ┌──────────────────────────────────────────────────────────────┐    │   │
│  │   │                    Rules                                      │    │   │
│  │   │                                                                │    │   │
│  │   │   field "email":                                               │    │   │
│  │   │   - Rule: Required                                             │    │   │
│  │   │   - Rule: Email                                                │    │   │
│  │   │                                                                │    │   │
│  │   │   field "password":                                            │    │   │
│  │   │   - Rule: Required                                             │    │   │
│  │   │   - Rule: MinLength(8)                                         │    │   │
│  │   │                                                                │    │   │
│  │   │   field "age":                                                 │    │   │
│  │   │   - Rule: Min(18)                                                │    │   │
│  │   │   - Rule: Max(120)                                               │    │   │
│  │   │                                                                │    │   │
│  │   └──────────────────────────────────────────────────────────────┘    │   │
│  │                                                                        │   │
│  │   Validate(data) → (map[string][]string, bool)                      │   │
│  │                                                                        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Built-in Rules

### 3.1 String Rules

| Rule | Description | Example |
|------|-------------|---------|
| **Required** | Non-empty value | `"field is required"` |
| **MinLength(n)** | Minimum string length | `"must be at least %d characters"` |
| **MaxLength(n)** | Maximum string length | `"must be at most %d characters"` |
| **Email** | Valid email format | `"must be a valid email address"` |
| **Pattern(re, msg)** | Regex match | Custom message |
| **In(values...)** | Whitelist check | `"must be one of: %s"` |

### 3.2 Numeric Rules

| Rule | Description | Example |
|------|-------------|---------|
| **Min(n)** | Minimum value | `"must be at least %d"` |
| **Max(n)** | Maximum value | `"must be at most %d"` |

---

## 4. Usage Patterns

### 4.1 Basic Validation

```go
package main

import (
    "github.com/KooshaPari/phenotype-go-kit/validation"
)

type UserRegistration struct {
    Email    string `json:"email"`
    Password string `json:"password"`
    Age      int    `json:"age"`
}

func validateRegistration(req UserRegistration) (map[string][]string, bool) {
    v := validation.New()
    
    // Add validation rules
    v.AddRule("email", validation.Required)
    v.AddRule("email", validation.Email)
    
    v.AddRule("password", validation.Required)
    v.AddRule("password", validation.MinLength(8))
    v.AddRule("password", validation.MaxLength(100))
    
    v.AddRule("age", validation.Min(18))
    v.AddRule("age", validation.Max(120))
    
    // Validate
    return v.Validate(req)
}
```

### 4.2 Custom Rules

```go
// Define custom rule
var PhoneNumber = validation.Rule{
    Name:    "phone",
    Message: "must be a valid phone number",
    Validate: func(v interface{}) bool {
        s, ok := v.(string)
        if !ok {
            return false
        }
        // E.164 format validation
        matched, _ := regexp.MatchString(`^\+[1-9]\d{1,14}$`, s)
        return matched
    },
}

// Usage
v.AddRule("phone", PhoneNumber)
```

### 4.3 HTTP Handler Integration

```go
func handleRegistration(w http.ResponseWriter, r *http.Request) {
    var req UserRegistration
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    
    errors, valid := validateRegistration(req)
    if !valid {
        w.WriteHeader(http.StatusBadRequest)
        json.NewEncoder(w).Encode(map[string]interface{}{
            "errors": errors,
        })
        return
    }
    
    // Process valid registration
}
```

---

## 5. Security

### 5.1 Input Sanitization

| Threat | Protection |
|--------|------------|
| **SQL Injection** | Validate allowed characters |
| **XSS** | HTML encode output |
| **Command Injection** | Whitelist safe characters |
| **Path Traversal** | Path validation rules |

---

## 6. Appendices

### 6.1 API Reference

See [validator.go](../validator.go) for complete API documentation.

### 6.2 Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-05 | Initial release |

---

*This specification defines the validation library v1.0 for Phenotype Go Kit.*
