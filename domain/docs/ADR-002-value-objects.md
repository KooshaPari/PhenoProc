# ADR-002: Value Objects for Domain Primitives

## Status
**Accepted**

## Context

The domain layer needs to represent primitive concepts like Email, Money, and identifiers with validation and type safety. Using raw strings and integers leads to validation being scattered and invalid states being representable.

### Requirements

1. **Validation:** Values must be validated at creation
2. **Immutability:** Once created, values cannot change
3. **Equality:** Values are compared by their contents, not identity
4. **Type Safety:** Different concepts should have different types
5. **Self-Documenting:** Types communicate meaning

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Value Objects** | Type-safe, validated, immutable | More code, allocation |
| **Primitive Types** | Simple, fast | No validation, errors at runtime |
| **Type Aliases** | Some type safety | No validation, still primitives |
| **Pointers to Primitives** | Can be nil | No validation, nil checks needed |

## Decision

**We will use Value Objects** for all domain primitives with validation requirements.

### Rationale

1. **Fail Fast:** Invalid values are rejected at creation, not later
2. **Type Safety:** Cannot accidentally use an Email where a Name is expected
3. **Centralized Validation:** Validation logic is in one place
4. **Immutable:** Values can be safely shared without defensive copying

### Consequences

**Positive:**
- Invalid states are unrepresentable
- Validation logic is centralized
- Better type safety
- Clear domain model

**Negative:**
- More boilerplate code
- Small allocation overhead
- Learning curve for team

## Implementation

### Value Object Interface

```go
// ValueObject is the interface that all value objects implement
type ValueObject interface {
    Equals(ValueObject) bool
    String() string
}

// BaseValueObject provides common value object functionality
type BaseValueObject struct {
    value string
}

func (v *BaseValueObject) String() string {
    return v.value
}

func (v *BaseValueObject) Equals(other ValueObject) bool {
    if other == nil {
        return false
    }
    return v.String() == other.String()
}
```

### Email Value Object

```go
// Email is a value object for email addresses
type Email struct {
    address string
}

// NewEmail creates a new email value object
func NewEmail(address string) (*Email, error) {
    // RFC 5322 simplified regex
    emailRegex := regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
    
    if !emailRegex.MatchString(address) {
        return nil, &DomainError{
            Code:    "INVALID_EMAIL",
            Message: fmt.Sprintf("'%s' is not a valid email address", address),
        }
    }
    
    return &Email{address: strings.ToLower(address)}, nil
}

// MustNewEmail creates a new email or panics
func MustNewEmail(address string) *Email {
    email, err := NewEmail(address)
    if err != nil {
        panic(err)
    }
    return email
}

func (e *Email) Address() string {
    return e.address
}

func (e *Email) Equals(other ValueObject) bool {
    if other == nil {
        return false
    }
    o, ok := other.(*Email)
    if !ok {
        return false
    }
    return e.address == o.address
}

func (e *Email) String() string {
    return e.address
}

func (e *Email) Domain() string {
    parts := strings.Split(e.address, "@")
    if len(parts) == 2 {
        return parts[1]
    }
    return ""
}
```

### Money Value Object

```go
// Money represents a monetary value
type Money struct {
    amount   int64  // Stored in cents to avoid float issues
    currency string // ISO 4217 currency code
}

// NewMoney creates a new money value object
func NewMoney(dollars int64, cents int, currency string) (*Money, error) {
    currency = strings.ToUpper(currency)
    
    // Validate currency code
    validCurrencies := map[string]bool{
        "USD": true, "EUR": true, "GBP": true,
        "JPY": true, "CAD": true, "AUD": true,
    }
    
    if !validCurrencies[currency] {
        return nil, &DomainError{
            Code:    "INVALID_CURRENCY",
            Message: fmt.Sprintf("'%s' is not a valid currency code", currency),
        }
    }
    
    amount := dollars*100 + int64(cents)
    
    return &Money{
        amount:   amount,
        currency: currency,
    }, nil
}

func (m *Money) Amount() float64 {
    return float64(m.amount) / 100
}

func (m *Money) Currency() string {
    return m.currency
}

func (m *Money) Add(other *Money) (*Money, error) {
    if m.currency != other.currency {
        return nil, &DomainError{
            Code:    "CURRENCY_MISMATCH",
            Message: fmt.Sprintf("cannot add %s to %s", m.currency, other.currency),
        }
    }
    
    return &Money{
        amount:   m.amount + other.amount,
        currency: m.currency,
    }, nil
}

func (m *Money) Subtract(other *Money) (*Money, error) {
    if m.currency != other.currency {
        return nil, &DomainError{
            Code:    "CURRENCY_MISMATCH",
            Message: fmt.Sprintf("cannot subtract %s from %s", other.currency, m.currency),
        }
    }
    
    result := m.amount - other.amount
    if result < 0 {
        return nil, &DomainError{
            Code:    "NEGATIVE_MONEY",
            Message: "result cannot be negative",
        }
    }
    
    return &Money{
        amount:   result,
        currency: m.currency,
    }, nil
}

func (m *Money) Multiply(factor int64) *Money {
    return &Money{
        amount:   m.amount * factor,
        currency: m.currency,
    }
}

func (m *Money) Equals(other ValueObject) bool {
    if other == nil {
        return false
    }
    o, ok := other.(*Money)
    if !ok {
        return false
    }
    return m.amount == o.amount && m.currency == o.currency
}

func (m *Money) String() string {
    return fmt.Sprintf("%s %.2f", m.currency, m.Amount())
}
```

### NonEmptyString Value Object

```go
// NonEmptyString is a value object that ensures non-empty strings
type NonEmptyString struct {
    value string
}

// NewNonEmptyString creates a new non-empty string value object
func NewNonEmptyString(value string) (*NonEmptyString, error) {
    if strings.TrimSpace(value) == "" {
        return nil, &DomainError{
            Code:    "EMPTY_STRING",
            Message: "string cannot be empty or whitespace only",
        }
    }
    return &NonEmptyString{value: value}, nil
}

func (s *NonEmptyString) Value() string {
    return s.value
}

func (s *NonEmptyString) Equals(other ValueObject) bool {
    if other == nil {
        return false
    }
    o, ok := other.(*NonEmptyString)
    if !ok {
        return false
    }
    return s.value == o.value
}

func (s *NonEmptyString) String() string {
    return s.value
}
```

## Related Decisions

- ADR-001: UUID as Entity Identifier
- ADR-003: Domain Events for State Changes

---

*Last Updated: 2026-04-05*
