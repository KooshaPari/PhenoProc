# ADR-001: UUID as Entity Identifier

## Status
**Accepted**

## Context

The domain layer needs a consistent way to identify entities across the system. Entity identity is fundamental to DDD - it's what distinguishes one entity from another regardless of attribute values.

### Requirements

1. **Uniqueness:** Globally unique across all instances
2. **Immutable:** Cannot change after assignment
3. **Comparable:** Easy to compare for equality
4. **Sortable:** Can be used in ordered collections
5. **Portable:** Works across different systems and databases

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **UUID (v4)** | Globally unique, no coordination needed | 128 bits, not sortable by time |
| **UUID (v7)** | Time-sortable, unique | Newer standard, less support |
| **Auto-increment int** | Small, fast, sortable | Requires central coordination |
| **ULID** | Sortable, unique | Less common, needs library |
| **Snowflake** | Sortable, distributed | Requires infrastructure |
| **Composite key** | Domain meaning | Complex, harder to reference |

## Decision

**We will use UUID v4** for entity identifiers, with the option to migrate to UUID v7 in the future.

### Rationale

1. **Simplicity:** UUID v4 is widely supported and well-understood
2. **Uniqueness:** 122 bits of randomness ensures global uniqueness
3. **No Coordination:** Can generate IDs anywhere without central authority
4. **Standard Library:** Go's google/uuid is the standard

### Consequences

**Positive:**
- Simple implementation
- No central ID generator needed
- Works with any database
- Collision probability is negligible

**Negative:**
- Not time-sortable (v4)
- Larger than integer (16 bytes vs 8)
- Not human-readable

## Implementation

```go
package domain

import "github.com/google/uuid"

// EntityID represents a unique identifier for entities
type EntityID = uuid.UUID

// NewEntityID creates a new unique entity ID
func NewEntityID() EntityID {
    return uuid.New()
}

// ParseEntityID parses a string into an entity ID
func ParseEntityID(s string) (EntityID, error) {
    return uuid.Parse(s)
}

// MustParseEntityID parses a string or panics
func MustParseEntityID(s string) EntityID {
    return uuid.MustParse(s)
}

// EntityIDFromBytes creates an EntityID from bytes
func EntityIDFromBytes(b []byte) (EntityID, error) {
    return uuid.FromBytes(b)
}

// String returns the string representation
func EntityIDString(id EntityID) string {
    return id.String()
}

// IsNil checks if the ID is nil
func IsNilEntityID(id EntityID) bool {
    return id == uuid.Nil
}
```

### Usage in Entities

```go
type BaseEntity struct {
    id        EntityID
    createdAt time.Time
    updatedAt time.Time
}

func NewBaseEntity(id EntityID) *BaseEntity {
    now := time.Now()
    return &BaseEntity{
        id:        id,
        createdAt: now,
        updatedAt: now,
    }
}

func (e *BaseEntity) ID() EntityID {
    return e.id
}

func (e *BaseEntity) Equals(other Entity) bool {
    if other == nil {
        return false
    }
    return e.id == other.ID()
}
```

## Migration Path to UUIDv7

```go
// UUIDv7 support (future)
func NewEntityIDV7() EntityID {
    // When uuid package supports v7
    // return uuid.Must(uuid.NewV7())
    
    // For now, use v4
    return uuid.New()
}
```

## Related Decisions

- ADR-002: Value Objects for Domain Primitives
- ADR-003: Domain Events for State Changes

---

*Last Updated: 2026-04-05*
