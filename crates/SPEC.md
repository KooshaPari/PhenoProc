# SPEC: Phenotype Crates

## Overview
========================================

Phenotype Rust crate collection — shared libraries providing foundational infrastructure for the entire Phenotype ecosystem. Modular, composable crates following hexagonal architecture principles.

**Version:** 1.0  
**Status:** Active Development  
**Author:** Phenotype Architecture Team  

---

## Table of Contents
========================================

1. [Executive Summary](#executive-summary)
2. [Architecture](#architecture)
3. [Foundation Layer](#foundation-layer)
4. [Infrastructure Layer](#infrastructure-layer)
5. [Storage Layer](#storage-layer)
6. [Security Layer](#security-layer)
7. [Testing Layer](#testing-layer)
8. [Integration Patterns](#integration-patterns)
9. [API Design Guidelines](#api-design-guidelines)
10. [Performance Specifications](#performance-specifications)
11. [Security Model](#security-model)
12. [Deployment and Operations](#deployment-and-operations)
13. [Development Workflow](#development-workflow)
14. [Quality Assurance](#quality-assurance)
15. [Appendices](#appendices)

---

## Executive Summary
========================================

The Phenotype Crates ecosystem is a comprehensive collection of 40+ Rust libraries organized into five architectural layers:

- **Foundation Layer**: Core types, errors, time, string utilities
- **Infrastructure Layer**: Logging, telemetry, metrics, configuration
- **Storage Layer**: In-memory stores, serialization adapters, event sourcing
- **Security Layer**: Policy engine, compliance scanning, security aggregation
- **Testing Layer**: Test utilities, fixtures, BDD framework

### Key Design Principles

1. **Hexagonal Architecture**: Clear separation of domain logic from infrastructure
2. **Zero-Cost Abstractions**: Performance is a first-class concern
3. **Composability**: Crates work independently and together
4. **Type Safety**: Leverage Rust's type system for correctness
5. **Async-First**: Native async/await support throughout

### Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Total crates | 50 | 42 |
| Test coverage | > 80% | 75% |
| Documentation | 100% public APIs | 90% |
| MSRV | 1.75 | 1.75 |
| Critical path latency | < 10ms | 8ms |

---

## Architecture
========================================

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHENOTYPE CRATES ECOSYSTEM                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                     FOUNDATION LAYER                                │    │
│  │                                                                      │    │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │   │  core    │  │  errors  │  │   time   │  │  string  │          │    │
│  │   │  (base)  │  │ (error)  │  │(chrono)  │  │(utilities)│         │    │
│  │   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │    │
│  │        │             │             │             │                 │    │
│  │   ┌────┴─────────────┴─────────────┴─────────────┘                 │    │
│  │   │                                                                │    │
│  │   ▼                                                                │    │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │   │ validation│  │  macros  │  │   iter   │  │  async-  │          │    │
│  │   │          │  │          │  │          │  │  traits  │          │    │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘          │    │
│  │                                                                      │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                      INFRASTRUCTURE LAYER                           │    │
│  │                                                                      │    │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │   │ logging  │  │ telemetry│  │ metrics  │  │ config-  │          │    │
│  │   │          │  │ (OTel)   │  │          │  │  core    │          │    │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘          │    │
│  │                                                                      │    │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │   │ error-   │  │ retry    │  │ state-   │  │ event-   │          │    │
│  │   │  core    │  │          │  │ machine  │  │  bus     │          │    │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘          │    │
│  │                                                                      │    │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │   │   bid    │  │ contract │  │  http-   │  │   bdd    │          │    │
│  │   │          │  │          │  │ client   │  │          │          │    │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘          │    │
│  │                                                                      │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                        STORAGE LAYER                                │    │
│  │                                                                      │    │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │   │in-memory │  │ serde-   │  │ event-   │  │   mock   │          │    │
│  │   │ -store   │  │adapters  │  │sourcing  │  │          │          │    │
│  │   │          │  │          │  │          │  │          │          │    │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘          │    │
│  │                                                                      │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                     SECURITY LAYER                                │    │
│  │                                                                      │    │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │   │ security │  │compliance│  │  policy  │  │  mcp-    │          │    │
│  │   │aggregator│  │ scanner │  │ engine   │  │  core    │          │    │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘          │    │
│  │                                                                      │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                      TESTING LAYER                                  │    │
│  │                                                                      │    │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │   │  testing │  │test-infra│  │test-     │  │  health  │          │    │
│  │   │          │  │          │  │fixtures  │  │          │          │    │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘          │    │
│  │                                                                      │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Dependency Flow

```
Foundation ─────────────────────────────────────────────────────────────────
   │
   ├──► phenotype-core ◄────┬──── phenotype-contracts
   │                         │
   ├──► phenotype-errors ◄───┤
   │                         │
   ├──► phenotype-time ◄─────┤
   │                         │
   ├──► phenotype-string ◄───┘
   │
Infrastructure ──────────────────────────────────────────────────────────────
   │
   ├──► phenotype-logging ───► tracing, tracing-subscriber
   │
   ├──► phenotype-telemetry ─► opentelemetry
   │
   ├──► phenotype-metrics ───► metrics
   │
   └──► phenotype-config-core ─► config
```

### Hexagonal Architecture Application

Each crate follows hexagonal (ports and adapters) architecture:

```
┌─────────────────────────────────────────┐
│           Application Core              │
│  ┌─────────────────────────────────┐   │
│  │         Domain Logic            │   │
│  │     (No external deps)          │   │
│  └─────────────────────────────────┘   │
│           ▲                    ▲       │
│           │                    │       │
│     ┌─────┘                    └─────┐  │
│     │                                │  │
│  ┌──┴──┐                        ┌──┴──┐│
│  │Driving│                        │Driven││
│  │Adapter│                        │Adapter││
│  │(CLI,  │                        │(DB,  ││
│  │HTTP) │                        │Queue)││
│  └──────┘                        └──────┘│
└─────────────────────────────────────────┘
```

---

## Foundation Layer
========================================

### phenotype-core

Core types and traits used across the ecosystem.

#### EntityId

Type-safe identifier with phantom type parameter:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct EntityId<T> {
    id: Uuid,
    _phantom: PhantomData<T>,
}

impl<T> EntityId<T> {
    pub fn new() -> Self;
    pub fn parse(s: &str) -> Option<Self>;
    pub fn as_uuid(&self) -> Uuid;
}

// Usage
let user_id = EntityId::<User>::new();
let order_id = EntityId::<Order>::new();
// user_id and order_id are different types!
```

#### DomainEvent

Standardized event structure for event sourcing:

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DomainEvent {
    pub id: Uuid,
    pub event_type: String,
    pub aggregate_id: String,
    pub aggregate_type: String,
    pub sequence: u64,
    pub payload: Value,
    pub metadata: HashMap<String, String>,
    pub timestamp: DateTime<Utc>,
}
```

#### Pagination

Consistent pagination across all APIs:

```rust
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Pagination {
    pub page: u32,      // 1-indexed
    pub per_page: u32,  // Default: 20, Max: 100
}

impl Pagination {
    pub fn offset(&self) -> usize;
    pub fn limit(&self) -> usize;
}
```

#### QueryParams

Standardized query parameter structure:

```rust
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct QueryParams {
    pub pagination: Pagination,
    pub sort: Vec<Sort>,
    pub filters: Vec<FilterOp>,
    pub search: Option<String>,
}
```

### phenotype-errors

Error hierarchy with structured context.

```rust
#[derive(Debug, thiserror::Error)]
pub enum PhenotypeError {
    #[error("Validation failed: {message}")]
    Validation { field: String, message: String },
    
    #[error("{resource} not found: {id}")]
    NotFound { resource: String, id: String },
    
    #[error("{resource} already exists: {id}")]
    Conflict { resource: String, id: String },
    
    #[error("External service {service} failed: {cause}")]
    External { service: String, cause: String },
    
    #[error("Internal error: {message}")]
    Internal { message: String },
}
```

Error conversion traits:

```rust
pub trait IntoPhenotypeError {
    fn into_not_found(self, resource: &str) -> PhenotypeError;
    fn into_validation(self, field: &str) -> PhenotypeError;
}
```

### phenotype-time

Time utilities and formatting.

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct Timestamp(DateTime<Utc>);

impl Timestamp {
    pub fn now() -> Self;
    pub fn to_rfc3339(&self) -> String;
    pub fn to_epoch_millis(&self) -> i64;
    pub fn from_epoch_millis(millis: i64) -> Self;
}
```

Formatting utilities:

```rust
pub mod format {
    pub fn human_readable(duration: Duration) -> String;
    pub fn iso8601(dt: DateTime<Utc>) -> String;
    pub fn compact(dt: DateTime<Utc>) -> String; // 20240115T143022Z
}
```

### phenotype-validation

Validation combinators and traits.

```rust
pub trait Validatable {
    fn validate(&self) -> ValidationResult;
}

pub type ValidationResult = Result<(), Vec<ValidationError>>;

pub struct ValidationError {
    pub field: String,
    pub code: String,
    pub message: String,
}

// Combinators
pub fn all(validators: Vec<Validator>) -> Validator;
pub fn any(validators: Vec<Validator>) -> Validator;
pub fn chain(validators: Vec<Validator>) -> Validator;
```

---

## Infrastructure Layer
========================================

### phenotype-logging

Structured logging with tracing integration.

```rust
use phenotype_logging::{info, debug, error, span};

#[derive(Debug)]
struct RequestContext {
    request_id: Uuid,
    user_id: EntityId<User>,
}

impl SpanFields for RequestContext {
    fn span_fields(&self) -> Vec<(String, Value)> {
        vec![
            ("request_id".to_string(), self.request_id.to_string().into()),
            ("user_id".to_string(), self.user_id.to_string().into()),
        ]
    }
}

// Usage
let ctx = RequestContext::new();
let _span = span!("process_order", &ctx);
info!(ctx, "Processing order", order_id = %order_id);
```

Configuration:

```rust
pub struct LoggingConfig {
    pub level: Level,
    pub format: LogFormat,  // Pretty, Json, Compact
    pub output: LogOutput,  // Stdout, File, Both
    pub filter: Option<String>, // EnvFilter directive
}
```

### phenotype-telemetry

OpenTelemetry integration.

```rust
use phenotype_telemetry::{init_tracer, TracerConfig};

let config = TracerConfig::builder()
    .service_name("api-gateway")
    .jaeger_endpoint("http://jaeger:14268/api/traces")
    .build();

let _guard = init_tracer(config)?;
```

Span creation:

```rust
use phenotype_telemetry::{span, SpanKind};

async fn process_order(order_id: EntityId<Order>) -> Result<()> {
    let span = span!("process_order", kind = SpanKind::Internal);
    
    async {
        // ... processing
    }
    .with_span(span)
    .await
}
```

### phenotype-metrics

Metrics collection with Prometheus export.

```rust
use phenotype_metrics::{counter, histogram, gauge, labels};

// Counter
counter!("requests_total", labels! { method = "GET", status = "200" }).increment();

// Histogram
histogram!("request_duration_seconds").record(duration.as_secs_f64());

// Gauge
gauge!("active_connections").set(connection_count as f64);
```

Metric types:

```rust
pub enum MetricType {
    Counter,     // Monotonically increasing
    Gauge,       // Can go up or down
    Histogram,   // Distribution of values
    Summary,     // Similar to histogram
}
```

### phenotype-config-core

Hierarchical configuration management.

```rust
use phenotype_config_core::{Config, Source};

let config = Config::builder()
    .add_source(Source::File("config/default.toml"))
    .add_source(Source::File("config/local.toml"))
    .add_source(Source::Env("PHENOTYPE_"))
    .build()?;

let db_url: String = config.get("database.url")?;
let timeout: Duration = config.get("database.timeout")?;
```

Configuration layers (highest precedence last):

1. Default values (code)
2. Configuration files (TOML)
3. Environment variables
4. Command-line arguments
5. Runtime overrides

### phenotype-retry

Retry policies with exponential backoff.

```rust
use phenotype_retry::{RetryPolicy, retry};

let policy = RetryPolicy::exponential()
    .max_attempts(5)
    .initial_delay(Duration::from_millis(100))
    .max_delay(Duration::from_secs(30))
    .jitter(true)
    .build();

let result = retry(policy, || async {
    client.fetch_data().await
}).await?;
```

Built-in policies:

```rust
impl RetryPolicy {
    pub fn fixed(delay: Duration) -> Builder;
    pub fn exponential() -> Builder;
    pub fn linear(increment: Duration) -> Builder;
}
```

### phenotype-state-machine

Finite state machine framework.

```rust
use phenotype_state_machine::{StateMachine, State, Event, Transition};

#[derive(Clone, Debug, PartialEq)]
enum OrderState { Pending, Confirmed, Shipped, Delivered }

#[derive(Clone, Debug, PartialEq)]
enum OrderEvent { Confirm, Ship, Deliver, Cancel }

impl StateMachine for OrderState {
    type Event = OrderEvent;
    type Error = OrderError;
    
    fn transition(&self, event: OrderEvent) -> Result<OrderState, OrderError> {
        match (self, event) {
            (Pending, Confirm) => Ok(Confirmed),
            (Confirmed, Ship) => Ok(Shipped),
            (Shipped, Deliver) => Ok(Delivered),
            (_, Cancel) if *self != Delivered => Ok(Cancelled),
            _ => Err(OrderError::InvalidTransition),
        }
    }
}
```

### phenotype-event-bus

In-memory event bus with async support.

```rust
use phenotype_event_bus::{EventBus, BusConfig};

let bus = EventBus::new(BusConfig {
    buffer_size: 1000,
    ..Default::default()
});

// Subscribe
let mut rx = bus.subscribe::<OrderEvent>();
tokio::spawn(async move {
    while let Some(event) = rx.recv().await {
        handle_order_event(event).await;
    }
});

// Publish
bus.publish(OrderEvent::Created { order_id }).await?;
```

### phenotype-http-client-core

HTTP client abstractions.

```rust
use phenotype_http_client_core::{HttpClient, Request, Response};

#[async_trait]
pub trait HttpClient: Send + Sync {
    async fn execute(&self, request: Request) -> Result<Response, HttpError>;
    async fn get(&self, url: &str) -> Result<Response, HttpError>;
    async fn post(&self, url: &str, body: impl Into<Body>) -> Result<Response, HttpError>;
}
```

Middleware support:

```rust
let client = Client::builder()
    .add_middleware(RetryMiddleware::new(policy))
    .add_middleware(TracingMiddleware::new())
    .add_middleware(MetricsMiddleware::new())
    .build()?;
```

---

## Storage Layer
========================================

### phenotype-in-memory-store

Generic in-memory storage with TTL and eviction.

```rust
use phenotype_in_memory_store::{InMemoryStore, StoreConfig, ExpiryPolicy};

let store = InMemoryStore::<String, User>::new(StoreConfig {
    max_size: 10_000,
    expiry: ExpiryPolicy::AfterWrite(Duration::from_secs(300)),
    eviction: EvictionPolicy::LRU,
});

// Operations
store.insert("user:123", user).await?;
let user = store.get("user:123").await?;
store.remove("user:123").await?;
```

### phenotype-serde-adapters

Serialization adapters for multiple formats.

```rust
use phenotype_serde_adapters::{Json, MessagePack, BinaryFormat};

// JSON
let json = Json::serialize(&data)?;
let data: MyType = Json::deserialize(&json)?;

// MessagePack
let packed = MessagePack::serialize(&data)?;
let data: MyType = MessagePack::deserialize(&packed)?;

// With compression
let compressed = Json::serialize_compressed(&data, Compression::Zstd)?;
```

### phenotype-event-sourcing

Event sourcing infrastructure.

```rust
use phenotype_event_sourcing::{EventStore, Aggregate, Snapshot};

#[derive(Aggregate)]
struct Order {
    id: EntityId<Order>,
    items: Vec<OrderItem>,
    status: OrderStatus,
}

impl Aggregate for Order {
    type Event = OrderEvent;
    type Command = OrderCommand;
    type Error = OrderError;
    
    fn apply(&mut self, event: OrderEvent) {
        match event {
            OrderEvent::ItemAdded { item } => self.items.push(item),
            OrderEvent::Confirmed => self.status = OrderStatus::Confirmed,
            // ...
        }
    }
}
```

Event store operations:

```rust
// Append events
store.append(order_id, vec![event1, event2], expected_version).await?;

// Read events
let events = store.read_all(order_id).await?;
let events = store.read_from(order_id, from_sequence).await?;

// Snapshots
store.snapshot(order_id, aggregate).await?;
let (snapshot, events) = store.read_with_snapshot(order_id).await?;
```

### phenotype-mock

Mock implementations for testing.

```rust
use phenotype_mock::{Mock, Expectation};

let mut mock = Mock::<UserRepository>::new();

mock.expect::<GetUser>(Expectation::once()
    .with_param(eq(user_id))
    .returns(Ok(user)));

mock.expect::<SaveUser>(Expectation::any()
    .returns(Ok(())));

// Use mock in test
let service = UserService::new(mock);
```

---

## Security Layer
========================================

### phenotype-security-aggregator

Security data aggregation from multiple sources.

```rust
use phenotype_security_aggregator::{SecurityAggregator, Source};

let aggregator = SecurityAggregator::new(vec![
    Source::CargoAudit,
    Source::Snyk("api_key".into()),
    Source::Custom(Box::new(my_scanner)),
]);

let report = aggregator.scan(&project).await?;

for finding in report.findings {
    match finding.severity {
        Severity::Critical => alert_oncall(&finding),
        Severity::High => create_ticket(&finding),
        _ => log_warning(&finding),
    }
}
```

### phenotype-compliance-scanner

Documentation and governance compliance scanning.

```rust
use phenotype_compliance_scanner::{Scanner, Rule};

let scanner = Scanner::new(vec![
    Rule::HasReadme,
    Rule::HasLicense,
    Rule::HasChangelog,
    Rule::SecurityPolicy,
    Rule::CodeOfConduct,
    Rule::Custom(Box::new(check_fn)),
]);

let report = scanner.scan_directory("./crates").await?;
```

### phenotype-policy-engine

Policy evaluation with Rhai scripting.

```rust
use phenotype_policy_engine::{Engine, Policy};

let engine = Engine::new();

engine.register_policy(Policy::new("authz", r#"
fn evaluate(ctx) {
    if ctx.user.role == "admin" {
        return true;
    }
    if ctx.resource.owner == ctx.user.id {
        return true;
    }
    return false;
}
"#))?;

let result = engine.evaluate("authz", &context)?;
```

### phenotype-mcp-core

Model Context Protocol core types.

```rust
use phenotype_mcp_core::{Server, Tool, Resource, Protocol};

let server = Server::new("phenotype-crates")
    .with_tool(Tool::new("search_crates")
        .with_handler(|params| async move {
            search_crates(params).await
        }))
    .with_resource(Resource::new("docs://spec.md"));
```

---

## Testing Layer
========================================

### phenotype-testing

Test utilities and assertions.

```rust
use phenotype_testing::{assert_ok, assert_err, assert_matches};

// Result assertions
assert_ok!(result);
assert_ok!(result, |val| val.id == expected_id);

assert_err!(result);
assert_err!(result, PhenotypeError::NotFound { .. });

// Pattern matching
assert_matches!(result, Ok(val) if val.active);
```

### phenotype-test-infra

Integration testing infrastructure.

```rust
use phenotype_test_infra::{TestContext, TestDatabase, TestCache};

#[tokio::test]
async fn user_workflow() {
    let ctx = TestContext::new().await;
    
    // Database
    let db = ctx.database().await;
    db.execute("INSERT INTO users ...").await?;
    
    // Cache
    let cache = ctx.cache().await;
    cache.set("key", "value").await?;
    
    // Test your service
    let service = UserService::new(db, cache);
    let user = service.create_user(params).await?;
    
    assert_eq!(user.name, params.name);
}
```

### phenotype-test-fixtures

Test data generation.

```rust
use phenotype_test_fixtures::{Fixture, Generator};

// Generate test data
let user = Fixture::<User>::new()
    .with(|u| u.email = "test@example.com")
    .generate();

// Generate many
let users = Generator::<User>::new()
    .count(100)
    .unique(|u| u.email)
    .generate();
```

### phenotype-bdd

BDD test framework (cucumber integration).

```rust
use phenotype_bdd::{World, given, when, then};

#[given("a user with name {string}")]
async fn given_user(world: &mut World, name: String) {
    world.user = Some(User::new(name));
}

#[when("I create an order")]
async fn create_order(world: &mut World) {
    world.order = Some(Order::new(world.user.as_ref().unwrap().id));
}

#[then("the order should be pending")]
async fn order_pending(world: &mut World) {
    assert_eq!(world.order.as_ref().unwrap().status, OrderStatus::Pending);
}
```

### phenotype-health

Health check framework.

```rust
use phenotype_health::{HealthCheck, HealthStatus, CompositeCheck};

let health = CompositeCheck::new("api")
    .add_check(DatabaseCheck::new(pool))
    .add_check(RedisCheck::new(redis))
    .add_check(ExternalAPICheck::new("https://api.partner.com/health"));

// Manual check
let status = health.check().await;

// HTTP endpoint
let app = Router::new()
    .route("/health", get(health.handler()));
```

---

## Integration Patterns
========================================

### Hexagonal Ports and Adapters

```rust
// Domain (crate core)
pub trait UserRepository: Send + Sync {
    async fn find_by_id(&self, id: EntityId<User>) -> Result<Option<User>>;
    async fn save(&self, user: &User) -> Result<()>;
}

// Driven adapter (crate sqlx)
pub struct SqlxUserRepository {
    pool: PgPool,
}

#[async_trait]
impl UserRepository for SqlxUserRepository {
    async fn find_by_id(&self, id: EntityId<User>) -> Result<Option<User>> {
        sqlx::query_as::<_, User>("SELECT * FROM users WHERE id = $1")
            .bind(id.as_uuid())
            .fetch_optional(&self.pool)
            .await
            .map_err(Into::into)
    }
    // ...
}

// Driving adapter (crate axum)
pub fn user_routes<R: UserRepository>(repo: R) -> Router {
    Router::new()
        .route("/users/:id", get(get_user::<R>))
        .with_state(repo)
}
```

### Event-Driven Architecture

```rust
// Event definition
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct OrderCreated {
    pub order_id: EntityId<Order>,
    pub user_id: EntityId<User>,
    pub total: Money,
    pub created_at: Timestamp,
}

// Publisher
impl DomainEvent for OrderCreated {
    fn event_type(&self) -> &'static str { "order.created" }
    fn aggregate_id(&self) -> String { self.order_id.to_string() }
}

// Subscriber
#[derive(EventHandler)]
struct NotificationHandler;

#[async_trait]
impl Handler<OrderCreated> for NotificationHandler {
    async fn handle(&self, event: OrderCreated) -> Result<()> {
        send_notification(event.user_id, "Order received!").await
    }
}
```

### Circuit Breaker Pattern

```rust
use phenotype_retry::{CircuitBreaker, CircuitConfig};

let breaker = CircuitBreaker::new(CircuitConfig {
    failure_threshold: 5,
    reset_timeout: Duration::from_secs(30),
    half_open_max_calls: 3,
});

let result = breaker.call(|| async {
    external_service.call().await
}).await;
```

### Saga Pattern (Distributed Transactions)

```rust
use phenotype_core::saga::{Saga, SagaBuilder, Compensation};

let saga = SagaBuilder::new("order_processing")
    .step("reserve_inventory", reserve_inventory, release_inventory)
    .step("process_payment", process_payment, refund_payment)
    .step("schedule_shipping", schedule_shipping, cancel_shipping)
    .build();

let result = saga.execute(order_context).await?;
```

---

## API Design Guidelines
========================================

### Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Types | PascalCase | `EntityId`, `DomainEvent` |
| Functions | snake_case | `parse_entity_id` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_PAGE_SIZE` |
| Modules | snake_case | `phenotype_core` |
| Traits | PascalCase | `Validatable`, `Entity` |
| Lifetimes | 'snake_case | `'a`, `'ctx` |

### Error Handling

```rust
// Use Result with typed errors
pub fn parse_id(s: &str) -> Result<EntityId<T>, ParseError>;

// Provide context
pub fn find_user(id: EntityId<User>) -> Result<User, PhenotypeError> {
    db.query(id).await
        .map_err(|e| PhenotypeError::External {
            service: "database",
            cause: e.to_string(),
        })
}

// Use ? operator
let user = find_user(id).await?;
```

### Async API Design

```rust
// Prefer &str over String for parameters
pub async fn search(query: &str) -> Result<Vec<Item>>;  // Good
pub async fn search(query: String) -> Result<Vec<Item>>; // Avoid

// Accept impl Into<Param> for flexibility
pub async fn create(name: impl Into<String>) -> Result<Item>;

// Return impl Stream for large collections
pub fn stream_all() -> impl Stream<Item = Result<Record>>;
```

### Builder Pattern

```rust
let config = Config::builder()
    .timeout(Duration::from_secs(30))
    .retries(3)
    .endpoint("https://api.example.com")
    .build()?;
```

### Documentation Requirements

Every public API must have:

1. Module-level documentation (`//!`)
2. Type/Trait documentation with examples
3. Function documentation with parameters, return values, and errors
4. Panic conditions documented
5. Unsafe conditions documented (if applicable)

```rust
/// Creates a new entity identifier.
///
/// # Examples
///
/// ```
/// use phenotype_core::EntityId;
///
/// let id = EntityId::<User>::new();
/// assert!(!id.to_string().is_empty());
/// ```
///
/// # Type Safety
///
/// The phantom type parameter ensures that `EntityId<User>` and
/// `EntityId<Order>` are different types at compile time.
pub fn new<T>() -> EntityId<T> {
    // ...
}
```

---

## Performance Specifications
========================================

### Compile Time Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Clean check | < 30s | `cargo check --workspace` |
| Clean build | < 2min | `cargo build --workspace` |
| Clean test | < 3min | `cargo test --workspace` |
| Incremental check | < 5s | After file change |
| Incremental build | < 10s | After file change |

### Runtime Performance

| Operation | Target | Measurement |
|-----------|--------|-------------|
| EntityId creation | < 100ns | Criterion benchmark |
| Validation (single) | < 1µs | Per-field validation |
| Event serialization | < 10µs | JSON encoding |
| Retry policy calc | < 1µs | With jitter |
| Log write (disabled) | < 1ns | No-op check |
| Telemetry span | < 10µs | Creation + enter |
| Config load | < 100ms | File + env |

### Memory Usage

| Component | Target | Notes |
|-----------|--------|-------|
| Core types | Zero overhead | Same as std equivalents |
| In-memory store | < 100MB | 10k entries |
| Event bus | < 50MB | 1000 subscriber buffer |
| Per-crate overhead | < 500KB | Release binary |

### Optimization Strategies

1. **Zero-copy deserialization**: Use `&str` and `&[u8]` where possible
2. **Arena allocation**: Batch allocations for event processing
3. **Object pooling**: Reuse buffers for serialization
4. **Lock-free structures**: Use `dashmap` and `crossbeam` channels
5. **Lazy evaluation**: Defer expensive operations

---

## Security Model
========================================

### Threat Model

| Threat | Severity | Mitigation |
|--------|----------|------------|
| Dependency confusion | High | Private registry + scoped names |
| Typosquatting | Medium | Verified publisher tracking |
| Malicious dependencies | High | cargo-audit + vendoring |
| Secret leakage | Critical | Zero-on-drop types |
| Timing attacks | Medium | Constant-time crypto |

### Security Features

1. **Zero-on-drop for secrets**

```rust
use zeroize::Zeroize;

#[derive(Zeroize)]
#[zeroize(drop)]
pub struct SecretKey([u8; 32]);
```

2. **Constant-time comparison**

```rust
use subtle::ConstantTimeEq;

if secret.ct_eq(&provided).into() {
    // Valid
}
```

3. **Input validation at boundaries**

```rust
pub fn set_api_key(&mut self, key: &str) -> Result<()> {
    if key.len() != 64 {
        return Err(ValidationError::invalid_length(64, key.len()));
    }
    if !key.chars().all(|c| c.is_ascii_hexdigit()) {
        return Err(ValidationError::invalid_format("hex"));
    }
    self.key = SecretKey::from_hex(key)?;
    Ok(())
}
```

### Audit Requirements

```yaml
# .github/workflows/audit.yml
name: Security Audit

on:
  schedule:
    - cron: '0 0 * * *'  # Daily
  push:
    paths:
      - '**/Cargo.toml'
      - '**/Cargo.lock'

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: rustsec/audit-check@v1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
```

---

## Deployment and Operations
========================================

### Registry Publishing

```bash
# Dry run
cargo publish -p phenotype-core --dry-run

# Actual publish
cargo publish -p phenotype-core

# With token
CARGO_REGISTRY_TOKEN=$TOKEN cargo publish -p phenotype-core
```

### Version Management

Using cargo-smart-release:

```bash
# Detect changes and bump versions
cargo smart-release --bump minor --no-confirm

# Publish all affected crates
cargo smart-release --bump minor --no-confirm --execute
```

### Documentation Publishing

```bash
# Generate docs
cargo doc --workspace --no-deps

# Serve locally
cargo doc --workspace --open

# Deploy to GitHub Pages
# (via GitHub Actions)
```

### Monitoring

```rust
// Health check endpoint
let health = phenotype_health::CompositeCheck::new("crates")
    .add_check(phenotype_core::health_check())
    .add_check(phenotype_errors::health_check());

// Metrics export
phenotype_metrics::prometheus_exporter()
    .with_prefix("phenotype")
    .install()?;
```

---

## Development Workflow
========================================

### Getting Started

```bash
# Clone repository
git clone https://github.com/phenotype-labs/phenotype.git
cd phenotype/crates

# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install required tools
cargo install cargo-nextest cargo-audit cargo-deny cargo-edit

# Build workspace
cargo build --workspace

# Run tests
cargo nextest run --workspace
```

### Branch Strategy

- `main`: Stable, production-ready code
- `feature/*`: New features and enhancements
- `fix/*`: Bug fixes
- `release/*`: Release preparation branches

### Commit Convention

Follow conventional commits:

```
type(scope): subject

body (optional)

footer (optional)
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:

```
feat(core): add EntityId type-safe identifiers

fix(errors): correct error message formatting

docs(logging): add examples for structured logging
```

### PR Requirements

1. All tests pass (`cargo nextest run --workspace`)
2. Linting passes (`cargo clippy --workspace -- -D warnings`)
3. Formatting passes (`cargo fmt --check`)
4. No SemVer violations (`cargo semver-checks`)
5. Security audit clean (`cargo audit`)
6. Documentation updated
7. CHANGELOG.md entry added

---

## Quality Assurance
========================================

### Testing Strategy

See [ADR 003: Testing Architecture](./docs/adr/003-testing-architecture.md)

### Code Review Checklist

- [ ] API follows design guidelines
- [ ] Documentation complete with examples
- [ ] Error handling comprehensive
- [ ] Tests cover edge cases
- [ ] No `unwrap()` or `expect()` in production code
- [ ] No `unsafe` without explicit justification
- [ ] Performance characteristics documented
- [ ] Security implications considered

### Static Analysis

```bash
# Formatting
cargo fmt --check

# Linting
cargo clippy --workspace --all-targets -- -D warnings

# Audit
cargo audit

# Deny
cargo deny check licenses advisories
```

### Continuous Integration

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - uses: Swatinem/rust-cache@v2
      
      - run: cargo fmt --check
      - run: cargo clippy --workspace --all-targets -- -D warnings
      - run: cargo check --workspace

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - uses: taiki-e/install-action@cargo-nextest
      - uses: Swatinem/rust-cache@v2
      
      - run: cargo nextest run --workspace
      - run: cargo test --doc --workspace  # Doctests

  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: rustsec/audit-check@v1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

  semver:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - uses: obi1kenobi/cargo-semver-checks-action@v2
```

---

## Components Reference
========================================

### Foundation Crates

| Crate | Purpose | Dependencies | Size |
|-------|---------|--------------|------|
| `phenotype-core` | Core types and traits | serde, chrono, uuid | Small |
| `phenotype-errors` | Error hierarchy | thiserror, anyhow | Small |
| `phenotype-time` | Time utilities | chrono, time | Small |
| `phenotype-string` | String processing | regex, unicode-segmentation | Small |
| `phenotype-validation` | Validation combinators | regex, once_cell | Small |
| `phenotype-macros` | Procedural macros | proc-macro2, quote, syn | Small |
| `phenotype-iter` | Iterator extensions | - | Tiny |
| `phenotype-async-traits` | Async patterns | async-trait | Tiny |

### Infrastructure Crates

| Crate | Purpose | Dependencies | Size |
|-------|---------|--------------|------|
| `phenotype-logging` | Structured logging | tracing | Medium |
| `phenotype-telemetry` | OpenTelemetry | opentelemetry | Medium |
| `phenotype-metrics` | Metrics collection | metrics | Medium |
| `phenotype-config-core` | Configuration | config | Medium |
| `phenotype-error-core` | Error handling | thiserror | Small |
| `phenotype-retry` | Retry policies | tokio, rand | Small |
| `phenotype-state-machine` | State machines | - | Small |
| `phenotype-event-bus` | Event bus | tokio, dashmap | Small |
| `phenotype-bid` | Auction primitives | - | Tiny |
| `phenotype-contract` | Contract testing | - | Small |
| `phenotype-http-client-core` | HTTP abstractions | http | Medium |
| `phenotype-bdd` | BDD framework | cucumber | Medium |

### Storage Crates

| Crate | Purpose | Dependencies | Size |
|-------|---------|--------------|------|
| `phenotype-in-memory-store` | In-memory storage | dashmap | Small |
| `phenotype-serde-adapters` | Serialization | serde_json, rmp-serde | Medium |
| `phenotype-event-sourcing` | Event sourcing | chrono, ulid | Medium |
| `phenotype-mock` | Mock implementations | mockall | Medium |

### Security Crates

| Crate | Purpose | Dependencies | Size |
|-------|---------|--------------|------|
| `phenotype-security-aggregator` | Security aggregation | - | Small |
| `phenotype-compliance-scanner` | Compliance scanning | - | Small |
| `phenotype-policy-engine` | Policy evaluation | rhai | Medium |
| `phenotype-mcp-core` | MCP core types | serde, schemars | Small |

### Testing Crates

| Crate | Purpose | Dependencies | Size |
|-------|---------|--------------|------|
| `phenotype-testing` | Test utilities | tokio, pretty_assertions | Small |
| `phenotype-test-infra` | Test infrastructure | testcontainers | Large |
| `phenotype-test-fixtures` | Test data | fake, rand | Small |
| `phenotype-health` | Health checks | axum, serde | Small |

### Port/Integration Crates

| Crate | Purpose | Dependencies | Size |
|-------|---------|--------------|------|
| `phenotype-port-traits` | Hexagonal ports | async-trait | Tiny |
| `phenotype-project-registry` | Project registry | serde, toml | Small |

---

## Data Models
========================================

### Core Error Type

```rust
#[derive(Debug, thiserror::Error, Serialize)]
#[serde(tag = "type", content = "details")]
pub enum PhenotypeError {
    #[error("Validation failed for {field}: {message}")]
    #[serde(rename = "validation")]
    Validation { field: String, message: String },
    
    #[error("{resource} not found with id {id}")]
    #[serde(rename = "not_found")]
    NotFound { resource: String, id: String },
    
    #[error("{resource} already exists with id {id}")]
    #[serde(rename = "conflict")]
    Conflict { resource: String, id: String },
    
    #[error("External service {service} error: {cause}")]
    #[serde(rename = "external")]
    External { service: String, cause: String },
    
    #[error("Internal error: {message}")]
    #[serde(rename = "internal")]
    Internal { message: String },
}

impl std::error::Error for PhenotypeError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        None
    }
}
```

### Time Wrapper

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(transparent)]
pub struct Timestamp(DateTime<Utc>);

impl Timestamp {
    pub fn now() -> Self {
        Self(Utc::now())
    }
    
    pub fn to_rfc3339(&self) -> String {
        self.0.to_rfc3339()
    }
    
    pub fn to_epoch_millis(&self) -> i64 {
        self.0.timestamp_millis()
    }
}

impl Default for Timestamp {
    fn default() -> Self {
        Self::now()
    }
}
```

### Validation Result

```rust
pub type ValidationResult = Result<(), Vec<ValidationError>>;

#[derive(Debug, Clone, Serialize)]
pub struct ValidationError {
    pub field: String,
    pub code: String,
    pub message: String,
    pub params: HashMap<String, serde_json::Value>,
}

pub trait Validatable {
    fn validate(&self) -> ValidationResult;
}

// Example implementation
impl Validatable for CreateUserRequest {
    fn validate(&self) -> ValidationResult {
        let mut errors = Vec::new();
        
        if self.email.is_empty() {
            errors.push(ValidationError::new("email", "required", "Email is required"));
        } else if !self.email.contains('@') {
            errors.push(ValidationError::new("email", "format", "Invalid email format"));
        }
        
        if self.name.len() < 2 {
            errors.push(ValidationError::new("name", "min_length", "Name too short"));
        }
        
        if errors.is_empty() {
            Ok(())
        } else {
            Err(errors)
        }
    }
}
```

### Retry Policy

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RetryPolicy {
    pub max_attempts: u32,
    pub initial_delay: Duration,
    pub max_delay: Duration,
    pub backoff_multiplier: f64,
    pub jitter: bool,
}

impl Default for RetryPolicy {
    fn default() -> Self {
        Self {
            max_attempts: 3,
            initial_delay: Duration::from_millis(100),
            max_delay: Duration::from_secs(30),
            backoff_multiplier: 2.0,
            jitter: true,
        }
    }
}

impl RetryPolicy {
    pub fn calculate_delay(&self, attempt: u32) -> Duration {
        let base = self.initial_delay
            .mul_f64(self.backoff_multiplier.powi(attempt as i32));
        
        let delay = std::cmp::min(base, self.max_delay);
        
        if self.jitter {
            let jitter = rand::random::<f64>() * 0.1 * delay.as_secs_f64();
            delay + Duration::from_secs_f64(jitter)
        } else {
            delay
        }
    }
}
```

### State Machine

```rust
pub trait StateMachine {
    type State: State;
    type Event: Event;
    type Error: std::error::Error;
    
    fn initial_state() -> Self::State;
    fn transition(state: Self::State, event: Self::Event) -> Result<Self::State, Self::Error>;
    fn valid_transitions(state: &Self::State) -> Vec<Self::Event>;
}

pub trait State: Clone + PartialEq + Display + Send + Sync {}
pub trait Event: Clone + PartialEq + Display + Send + Sync {}

// Example: Order state machine
#[derive(Clone, Debug, PartialEq, Display)]
pub enum OrderState {
    Pending,
    Confirmed,
    Shipped,
    Delivered,
    Cancelled,
}

#[derive(Clone, Debug, PartialEq, Display)]
pub enum OrderEvent {
    Confirm,
    Ship,
    Deliver,
    Cancel,
}

impl StateMachine for Order {
    type State = OrderState;
    type Event = OrderEvent;
    type Error = OrderError;
    
    fn transition(state: OrderState, event: OrderEvent) -> Result<OrderState, OrderError> {
        match (state, event) {
            (Pending, Confirm) => Ok(Confirmed),
            (Confirmed, Ship) => Ok(Shipped),
            (Shipped, Deliver) => Ok(Delivered),
            (Pending, Cancel) | (Confirmed, Cancel) => Ok(Cancelled),
            _ => Err(OrderError::InvalidTransition),
        }
    }
    
    fn valid_transitions(state: &OrderState) -> Vec<OrderEvent> {
        match state {
            Pending => vec![Confirm, Cancel],
            Confirmed => vec![Ship, Cancel],
            Shipped => vec![Deliver],
            Delivered | Cancelled => vec![],
        }
    }
}
```

### Config Source

```rust
#[derive(Debug, Clone)]
pub enum ConfigSource {
    File(PathBuf),
    Env { prefix: String },
    Memory(HashMap<String, Value>),
    Json(Value),
}

#[derive(Debug)]
pub struct ConfigLoader {
    sources: Vec<ConfigSource>,
    cache: Option<Config>,
}

impl ConfigLoader {
    pub fn new() -> Self {
        Self {
            sources: Vec::new(),
            cache: None,
        }
    }
    
    pub fn add_source(mut self, source: ConfigSource) -> Self {
        self.sources.push(source);
        self.cache = None;
        self
    }
    
    pub fn load(&mut self) -> Result<&Config, ConfigError> {
        if self.cache.is_none() {
            let mut config = Config::default();
            
            for source in &self.sources {
                match source {
                    ConfigSource::File(path) => {
                        let content = fs::read_to_string(path)?;
                        let value: Value = toml::from_str(&content)?;
                        config.merge(value)?;
                    }
                    ConfigSource::Env { prefix } => {
                        for (key, value) in env::vars() {
                            if key.starts_with(prefix) {
                                let config_key = key[prefix.len()..].to_lowercase();
                                config.set(config_key, value)?;
                            }
                        }
                    }
                    ConfigSource::Memory(map) => {
                        for (key, value) in map {
                            config.set(key.clone(), value.clone())?;
                        }
                    }
                    ConfigSource::Json(value) => {
                        config.merge(value.clone())?;
                    }
                }
            }
            
            self.cache = Some(config);
        }
        
        Ok(self.cache.as_ref().unwrap())
    }
}
```

---

## Appendices
========================================

### Appendix A: Crate Size Budgets

| Category | Max Size (Release) |
|----------|-------------------|
| Foundation | < 100KB |
| Infrastructure | < 500KB |
| Storage | < 1MB |
| Security | < 500KB |
| Testing | N/A (dev-only) |

### Appendix B: Dependency Guidelines

Preferred external dependencies:

| Use Case | Primary | Alternative |
|----------|---------|-------------|
| Serialization | serde | - |
| Async runtime | tokio | async-std |
| HTTP client | reqwest | hyper |
| Error handling | thiserror | anyhow |
| Tracing | tracing | log |
| Hash maps | hashbrown | std::collections |
| UUID | uuid | - |
| Time | chrono | time |
| Regex | regex | fancy-regex |
| Random | rand | getrandom |

### Appendix C: MSRV Policy

Current MSRV: 1.75.0

- MSRV bumps require minor version increment
- MSRV tested in CI
- Notation in CHANGELOG required

### Appendix D: Research Documents

- [RUST_PACKAGING_SOTA.md](./docs/research/RUST_PACKAGING_SOTA.md) - Packaging ecosystem analysis

### Appendix E: Architecture Decision Records

- [ADR 001: Workspace Versioning](./docs/adr/001-workspace-versioning.md)
- [ADR 002: Registry Strategy](./docs/adr/002-registry-strategy.md)
- [ADR 003: Testing Architecture](./docs/adr/003-testing-architecture.md)

### Appendix F: Migration Guides

#### Migrating to phenotype-core 0.2.x

Breaking changes from 0.1.x:

```rust
// Before (0.1.x)
let id = EntityId::new();  // Untyped

// After (0.2.x)
let id = EntityId::<User>::new();  // Typed with phantom parameter
```

Migration steps:

1. Update Cargo.toml:
```toml
[dependencies]
phenotype-core = "0.2"
```

2. Add type parameters to EntityId usages:
```rust
// Find all instances of EntityId without type parameter
// Add appropriate type markers
```

3. Run tests to identify remaining issues:
```bash
cargo check --workspace 2>&1 | grep "EntityId"
```

#### Migrating to phenotype-errors 0.2.x

Error construction changes:

```rust
// Before
PhenotypeError::validation("field", "message")

// After
PhenotypeError::Validation {
    field: "field".into(),
    message: "message".into(),
}
```

#### Migrating to phenotype-logging 0.3.x

Structured logging migration:

```rust
// Before
tracing::info!("Processing order {}", order_id);

// After
phenotype_logging::info!("Processing order", order_id = %order_id);
```

### Appendix G: Troubleshooting Guide

#### Common Build Issues

**Issue: `Cargo.lock` conflicts after merge**

Solution:
```bash
# Delete lockfile and regenerate
cargo update --workspace
```

**Issue: Feature unification errors**

Symptoms:
```
error: cannot find macro `trace` in this scope
```

Solution:
```toml
# Add explicit feature in Cargo.toml
[dependencies]
phenotype-logging = { workspace = true, features = ["tracing"] }
```

**Issue: MSRV violations**

Check:
```bash
cargo +1.75 check --workspace
```

#### Common Runtime Issues

**Issue: Memory growth in long-running services**

Diagnosis:
```bash
# Enable jemalloc stats
MALLOC_CONF="stats_print:true" ./myapp
```

Solutions:
- Check for unbounded growth in phenotype-in-memory-store
- Verify TTL settings on cache entries
- Review event bus subscriber cleanup

**Issue: High CPU usage in idle state**

Diagnosis:
```bash
# Enable tracing spans
tokio-console
```

Solutions:
- Check for busy loops in custom adapters
- Verify async runtime configuration
- Review polling intervals in health checks

#### Common Test Issues

**Issue: Flaky tests**

Symptoms:
```
test test_name ... FAILED (after retry)
```

Solutions:
```rust
// Add retry annotation
#[test]
#[retry(flaky = 3)]
async fn test_name() { }
```

**Issue: Test database conflicts**

Solution:
```rust
// Use unique database per test
let db = TestDatabase::new()
    .with_prefix(&format!("test_{}", uuid::Uuid::new_v4()))
    .await;
```

### Appendix H: FAQ

**Q: Why use phantom types for EntityId?**

A: Phantom types provide compile-time guarantees that prevent mixing different entity types:

```rust
let user_id = EntityId::<User>::new();
let order_id = EntityId::<Order>::new();

// This is a compile error:
// function_expecting_user(user_id, order_id);
```

**Q: How do I handle circular dependencies between crates?**

A: Use trait-based abstractions or merge the crates:

```rust
// Instead of direct dependency, use trait
pub trait OrderService {
    async fn get_order(&self, id: EntityId<Order>) -> Result<Order>;
}

// Implementation in separate crate
impl OrderService for OrderServiceImpl { }
```

**Q: What's the recommended retry strategy for external APIs?**

A: Use exponential backoff with jitter:

```rust
let policy = RetryPolicy::exponential()
    .max_attempts(5)
    .initial_delay(Duration::from_millis(100))
    .jitter(true)
    .build();
```

**Q: How do I mock phenotype-core types in tests?**

A: Use phenotype-mock:

```rust
let mut mock = Mock::<UserRepository>::new();
mock.expect::<GetUser>(Expectation::once()
    .with_param(eq(user_id))
    .returns(Ok(user)));
```

**Q: Can I use these crates in a non-async context?**

A: Most crates support both sync and async. For async-only crates, use:

```rust
// Block on async code
let result = tokio::runtime::Runtime::new()
    .unwrap()
    .block_on(async_function());
```

**Q: How do I configure tracing for production?**

A: Use JSON format with sampling:

```rust
let config = LoggingConfig {
    level: Level::INFO,
    format: LogFormat::Json,
    filter: Some("info,phenotype=debug".into()),
};
```

### Appendix I: Advanced Patterns

#### Custom Middleware Chain

```rust
pub struct MiddlewareChain<C> {
    client: C,
    middlewares: Vec<Box<dyn Middleware>>,
}

#[async_trait]
impl<C: HttpClient> HttpClient for MiddlewareChain<C> {
    async fn execute(&self, request: Request) -> Result<Response> {
        let mut ctx = Context::new(request);
        
        // Pre-process
        for mw in &self.middlewares {
            ctx = mw.before(ctx).await?;
        }
        
        // Execute
        let response = self.client.execute(ctx.request).await?;
        
        // Post-process
        for mw in self.middlewares.iter().rev() {
            ctx = mw.after(ctx, &response).await?;
        }
        
        Ok(response)
    }
}
```

#### Event Sourcing with Projections

```rust
pub struct Projection<E, S> {
    event_store: Arc<dyn EventStore<E>>,
    state_store: Arc<dyn StateStore<S>>,
    projector: Box<dyn Projector<E, S>>,
}

impl<E: Event, S: State> Projection<E, S> {
    pub async fn rebuild(&self, aggregate_id: EntityId<A>) -> Result<()> {
        let events = self.event_store.read_all(aggregate_id).await?;
        let mut state = S::default();
        
        for event in events {
            state = self.projector.apply(state, event).await?;
        }
        
        self.state_store.save(aggregate_id, state).await
    }
    
    pub async fn handle_event(&self, event: E) -> Result<()> {
        let id = event.aggregate_id();
        let state = self.state_store.get(id).await?.unwrap_or_default();
        let new_state = self.projector.apply(state, event).await?;
        self.state_store.save(id, new_state).await
    }
}
```

#### Rate-Limiting Circuit Breaker

```rust
pub struct RateLimitedBreaker {
    breaker: CircuitBreaker,
    limiter: RateLimiter,
}

impl RateLimitedBreaker {
    pub async fn call<F, Fut, T>(&self, f: F) -> Result<T>
    where
        F: FnOnce() -> Fut,
        Fut: Future<Output = Result<T>>,
    {
        // Check rate limit
        self.limiter.acquire().await?;
        
        // Check circuit breaker
        if !self.breaker.allow_request() {
            return Err(Error::CircuitOpen);
        }
        
        // Execute
        match f().await {
            Ok(result) => {
                self.breaker.record_success();
                Ok(result)
            }
            Err(e) => {
                self.breaker.record_failure();
                Err(e)
            }
        }
    }
}
```

### Appendix J: Benchmarking Guide

#### Writing Criterion Benchmarks

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};

fn bench_entity_id(c: &mut Criterion) {
    let mut group = c.benchmark_group("entity_id");
    
    group.bench_function("new", |b| {
        b.iter(|| EntityId::<String>::new())
    });
    
    group.bench_function("parse", |b| {
        let uuid_str = "550e8400-e29b-41d4-a716-446655440000";
        b.iter(|| EntityId::<String>::parse(black_box(uuid_str)))
    });
    
    group.finish();
}

fn bench_validation(c: &mut Criterion) {
    let mut group = c.benchmark_group("validation");
    
    for size in [10, 100, 1000].iter() {
        let items = generate_items(*size);
        
        group.bench_with_input(
            BenchmarkId::new("validate_many", size),
            &items,
            |b, items| {
                b.iter(|| validate_all(black_box(items)))
            },
        );
    }
    
    group.finish();
}

criterion_group!(benches, bench_entity_id, bench_validation);
criterion_main!(benches);
```

#### Benchmark CI Integration

```yaml
# .github/workflows/bench.yml
name: Benchmark

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run benchmarks
        run: cargo bench --workspace -- --output-format bencher | tee output.txt
      
      - name: Upload results
        uses: benchmark-action/github-action-benchmark@v1
        with:
          tool: 'cargo'
          output-file-path: output.txt
          github-token: ${{ secrets.GITHUB_TOKEN }}
          auto-push: true
```

### Appendix K: FFI and Foreign Language Bindings

#### C FFI Example

```rust
// lib.rs
use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_int};

#[no_mangle]
pub extern "C" fn phenotype_entity_id_new() -> *mut c_char {
    let id = EntityId::<String>::new().to_string();
    CString::new(id).unwrap().into_raw()
}

#[no_mangle]
pub extern "C" fn phenotype_entity_id_free(s: *mut c_char) {
    if s.is_null() { return; }
    unsafe {
        let _ = CString::from_raw(s);
    }
}

#[no_mangle]
pub extern "C" fn phenotype_validate_email(email: *const c_char) -> c_int {
    let email = unsafe { CStr::from_ptr(email) }
        .to_str()
        .unwrap_or("");
    
    if validate_email(email).is_ok() {
        0  // Success
    } else {
        1  // Failure
    }
}
```

#### Generating Headers

```bash
# Using cbindgen
cbindgen --config cbindgen.toml --crate phenotype-core --output include/phenotype.h
```

### Appendix L: Unsafe Guidelines

When unsafe code is necessary:

1. **Minimize scope**: Keep unsafe blocks as small as possible
2. **Document invariants**: Explain what makes the code safe
3. **Use safe abstractions**: Wrap unsafe in safe APIs
4. **Review required**: All unsafe code requires two-person review

```rust
/// # Safety
/// 
/// The caller must ensure:
/// 1. `ptr` is valid and aligned
/// 2. `len` does not exceed the allocated size
/// 3. The memory is not accessed after this function returns
pub unsafe fn from_raw_parts(ptr: *const u8, len: usize) -> Self {
    // Implementation
}
```

### Appendix M: Deprecated Features

| Feature | Deprecated In | Removal | Migration |
|---------|---------------|-----------|-----------|
| `EntityId::new()` (untyped) | 0.2.0 | 0.3.0 | Use `EntityId::<T>::new()` |
| `PhenotypeError::validation()` | 0.2.0 | 0.3.0 | Use struct constructor |
| `RetryPolicy::default()` | 0.2.0 | 0.3.0 | Use builder pattern |
| `InMemoryStore::new()` | 0.2.0 | 0.3.0 | Use `StoreConfig` |

### Appendix N: Ecosystem Integration

#### Axum Integration

```rust
use phenotype_health::HealthCheck;
use phenotype_telemetry::TracingLayer;
use phenotype_metrics::MetricsLayer;

let app = Router::new()
    .route("/health", get(health.handler()))
    .layer(TracingLayer::new())
    .layer(MetricsLayer::new());
```

#### Tokio-Tracing Integration

```rust
use phenotype_logging::TelemetryLayer;

let subscriber = tracing_subscriber::registry()
    .with(TelemetryLayer::new(telemetry_config))
    .with(tracing_subscriber::fmt::layer());

tracing::subscriber::set_global_default(subscriber)?;
```

#### Serde Integration

```rust
use phenotype_serde_adapters::json;

// Custom serialization
#[derive(Serialize, Deserialize)]
pub struct Order {
    #[serde(with = "phenotype_serde_adapters::json::money")]
    pub total: Money,
    #[serde(with = "phenotype_serde_adapters::json::timestamp")]
    pub created_at: Timestamp,
}

### Appendix O: Feature Flag Reference

#### phenotype-core Features

| Feature | Default | Description |
|---------|---------|-------------|
| `serde` | Yes | Serialization support |
| `uuid-v4` | Yes | UUID v4 generation |
| `uuid-v7` | No | UUID v7 (time-sortable) |
| `arbitrary` | No | Arbitrary trait for fuzzing |

#### phenotype-errors Features

| Feature | Default | Description |
|---------|---------|-------------|
| `serde` | Yes | Error serialization |
| `backtrace` | No | Backtrace capture |
| `anyhow` | No | Anyhow integration |

#### phenotype-logging Features

| Feature | Default | Description |
|---------|---------|-------------|
| `tracing` | Yes | Tracing integration |
| `json` | Yes | JSON formatting |
| `pretty` | Yes | Human-readable format |
| `opentelemetry` | No | OTLP export |
| `tokio-console` | No | Tokio console support |

#### phenotype-telemetry Features

| Feature | Default | Description |
|---------|---------|-------------|
| `otlp-grpc` | Yes | gRPC OTLP exporter |
| `otlp-http` | No | HTTP OTLP exporter |
| `jaeger` | No | Jaeger exporter |
| `zipkin` | No | Zipkin exporter |

#### phenotype-metrics Features

| Feature | Default | Description |
|---------|---------|-------------|
| `prometheus` | Yes | Prometheus export |
| `statsd` | No | StatsD export |
| `cloudwatch` | No | AWS CloudWatch |


### Appendix P: Complete Workspace Example

```toml
# Cargo.toml (workspace root)
[workspace]
members = [
    "crates/phenotype-core",
    "crates/phenotype-errors",
    "tools/phenotype-cli",
]
resolver = "2"

[workspace.package]
version = "0.2.0"
edition = "2021"
rust-version = "1.75"
license = "MIT OR Apache-2.0"

[workspace.dependencies]
tokio = { version = "1", features = ["rt", "macros"] }
serde = { version = "1.0", features = ["derive"] }
phenotype-core = { path = "crates/phenotype-core", version = "0.2.0" }

[profile.release]
opt-level = 3
lto = true
```

### Appendix Q: Builder Pattern

```rust
#[derive(Debug, Default)]
pub struct ConfigBuilder {
    timeout: Option<Duration>,
    retries: Option<u32>,
}

impl ConfigBuilder {
    pub fn timeout(mut self, timeout: Duration) -> Self {
        self.timeout = Some(timeout);
        self
    }
    
    pub fn build(self) -> Result<Config> {
        Ok(Config {
            timeout: self.timeout.unwrap_or(Duration::from_secs(30)),
            retries: self.retries.unwrap_or(3),
        })
    }
}
```

### Appendix R: Common Patterns

```rust
// Newtype pattern
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(transparent)]
pub struct UserId(Uuid);

// Type-safe identifiers
impl UserId {
    pub fn new() -> Self { Self(Uuid::new_v4()) }
    pub fn parse(s: &str) -> Result<Self> {
        Uuid::parse_str(s).map(Self)
            .map_err(|e| PhenotypeError::validation("id", &e.to_string()))
    }
}
```


---


### Appendix S: Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PHENOTYPE_LOG` | info | Log level filter |
| `PHENOTYPE_CONFIG` | - | Config file path |
| `PHENOTYPE_REGISTRY` | crates.io | Default registry |

### Appendix T: CLI Tools

```bash
# phenotype-cli commands
phenotype check     # Validate crate configuration
phenotype lint      # Run clippy and fmt checks
phenotype test      # Run workspace tests
phenotype release   # Smart release workflow
```


### Appendix U: Testing Checklist

- [ ] Unit tests for all public functions
- [ ] Integration tests for cross-crate interactions
- [ ] Property-based tests for invariants
- [ ] Benchmarks for hot paths
- [ ] Documentation tests for all examples
- [ ] Doctests pass: `cargo test --doc`
- [ ] Coverage > 80%

### Appendix V: Release Checklist

- [ ] All tests passing
- [ ] Semver-checks passing
- [ ] Audit clean
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Git tag created
- [ ] Documentation published
- [ ] Announcement drafted

## Document Information
========================================

**Version:** 1.0  
**Last Updated:** 2024  
**Maintainer:** Phenotype Architecture Team  
**Review Cycle:** Quarterly  

**Traceability:** `/// @trace CRATES-SPEC-001`

---

*This specification follows the nanovms documentation format. For questions or suggestions, please open an issue on the Phenotype repository.*
