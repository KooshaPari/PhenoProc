# SPEC: Application Framework

## Table of Contents

1. Overview
2. Architecture
3. Clean Architecture
4. DDD Implementation
5. CQRS Pattern
6. API Reference
7. Testing
8. Examples

## Overview

Application framework implementing Clean Architecture, DDD, and CQRS patterns.

## Architecture

```
┌─────────────────────────────────┐
│     Interface Layer              │
├─────────────────────────────────┤
│    Application Layer             │
├─────────────────────────────────┤
│      Domain Layer                │
├─────────────────────────────────┤
│   Infrastructure Layer           │
└─────────────────────────────────┘
```

## Clean Architecture

- Entities: Enterprise business rules
- Use Cases: Application-specific logic
- Interface Adapters: Controllers, presenters
- Frameworks: External tools

## DDD Implementation

```go
// Aggregate
type Feature struct {
    ID     string
    Name   string
    Status FeatureStatus
}

// Repository
type FeatureRepository interface {
    FindByID(ctx context.Context, id string) (*Feature, error)
    Save(ctx context.Context, feature *Feature) error
}
```

## CQRS

```go
// Command
type CreateFeatureCommand struct {
    Name        string
    Description string
}

// Query
type GetFeatureQuery struct {
    ID string
}
```

## API Reference

```go
type UseCase[I, O any] interface {
    Execute(ctx context.Context, input I) (O, error)
}
```

## Examples

```go
// Create use case
createHandler := application.NewCommandHandler(
    NewCreateFeatureUseCase(repo, eventBus),
)

// Execute
result, err := createHandler.Handle(ctx, command)
```

---
*Specification Version: 1.0*
*Last Updated: 2026-04-05*
