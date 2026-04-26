# phenotype-governance Specification

**Version**: 1.0.0 | **Status**: Active | **Last Updated**: 2026-04-06

## 1. Executive Summary

phenotype-governance is a comprehensive governance framework for the Phenotype ecosystem, providing policy enforcement, compliance auditing, and organizational standards management. This specification defines the canonical behavior, architecture, and operational characteristics of the governance system.

---

## 2. Architecture Overview

### 2.1 High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                           PHENOTYPE GOVERNANCE SYSTEM                                        │
│                              (Hexagonal Architecture)                                        │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                              PRIMARY ADAPTERS (Driving)                               │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │  │
│  │  │  Policy     │  │  Audit      │  │  Compliance │  │  Integration               │  │  │
│  │  │  Engine     │  │  Logger     │  │  Scanner    │  │  Adapters                  │  │  │
│  │  │  Adapter    │  │  Adapter    │  │  Adapter    │  │                            │  │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────────────┬──────────────┘  │  │
│  │         │                │                │                       │                │  │
│  └─────────┼────────────────┼────────────────┼───────────────────────┼────────────────┘  │
│            │                │                │                       │                  │
│  ┌─────────▼────────────────▼────────────────▼───────────────────────▼────────────────┐  │
│  │                              CORE DOMAIN (Application Core)                            │  │
│  │                                                                                        │  │
│  │   ┌─────────────────────────────────────────────────────────────────────────────┐   │  │
│  │   │                          GOVERNANCE SERVICES                                   │   │  │
│  │   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │  │
│  │   │  │   Policy    │  │   Rule      │  │  Compliance │  │   Audit     │         │   │  │
│  │   │  │   Service   │  │   Engine    │  │   Service   │  │   Service   │         │   │  │
│  │   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │   │  │
│  │   │                                                                              │   │  │
│  │   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │  │
│  │   │  │   Role      │  │  Approval   │  │   Config    │  │   Report    │         │   │  │
│  │   │  │   Service   │  │   Workflow  │  │   Service   │  │   Generator │         │   │  │
│  │   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │   │  │
│  │   └─────────────────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                                        │  │
│  │   ┌─────────────────────────────────────────────────────────────────────────────┐   │  │
│  │   │                              DOMAIN MODELS                                   │   │  │
│  │   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │   │  │
│  │   │  │    Policy   │  │    Rule     │  │   Violation │  │   Audit     │         │   │  │
│  │   │  │             │  │             │  │             │  │   Record    │         │   │  │
│  │   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │   │  │
│  │   └─────────────────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                                        │  │
│  └─────────────────────────────────────────────────────────────────────────────────────┘  │
│            │                │                │                       │                     │
│  ┌─────────┼────────────────┼────────────────┼───────────────────────┼────────────────┐  │
│  │         │                │                │                       │                │  │
│  │  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐  ┌───────────▼────────────┐  │  │
│  │  │  Policy     │  │  Audit      │  │  Compliance │  │  Reporting             │  │  │
│  │  │  Port       │  │  Port       │  │  Port       │  │  Port                  │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────────────────┘  │  │
│  │                                                                                    │  │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
│            │                │                │                       │                     │
│  ┌─────────┼────────────────┼────────────────┼───────────────────────┼────────────────┐  │
│            │                │                │                       │                │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                           SECONDARY ADAPTERS (Driven)                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │  │
│  │  │  PostgreSQL │  │    Redis    │  │    S3       │  │   Event Bus               │ │  │
│  │  │  Repository │  │   Cache     │  │  Storage    │  │   (Kafka/NATS)            │ │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────────────┘ │  │
│  │                                                                                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │  │
│  │  │   Email     │  │   Slack     │  │   GitHub    │  │   Metrics                 │ │  │
│  │  │   Service   │  │   Service   │  │   Webhooks  │  │   (Prometheus)            │ │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Policy Enforcement Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Event Source    │────▶│  Policy Engine  │────▶│   Rule Evaluator│────▶│  Action Executor │
│                 │     │                 │     │                 │     │                 │
│ • Code Push       │     │ • Load Policies │     │ • Parse Rules   │     │ • Allow/Deny    │
│ • Config Change   │     │ • Match Context │     │ • Check Conditions│   │ • Log Decision  │
│ • User Action     │     │ • Apply Filters │     │ • Evaluate Logic│     │ • Notify        │
│ • Scheduled Check │     │ • Queue Rules   │     │ • Score Risk    │     │ • Escalate      │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    AUDIT TRAIL                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Event ID    │  │ Policy Ref  │  │ Rule Chain  │  │ Decision    │  │ Timestamp   │     │
│  │ User/Agent  │  │ Context     │  │ Evaluated   │  │ Outcome     │  │ Metadata    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Component Interactions

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                     CLIENT LAYER                         │
                    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
                    │  │  CLI     │  │  Web UI  │  │  API     │  │  Webhook │ │
                    │  │  Client  │  │          │  │  Client  │  │  Handler │ │
                    │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
                    └───────┼─────────────┼─────────────┼─────────────┼────────┘
                            │             │             │             │
                            └─────────────┴─────────────┴─────────────┘
                                          │
                    ┌─────────────────────▼─────────────────────────────────┐
                    │                    API GATEWAY                            │
                    │           (Rate Limiting, Auth, Routing)                │
                    └─────────────────────┬───────────────────────────────────┘
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
┌───────▼────────┐              ┌──────────▼──────────┐            ┌──────────▼──────────┐
│   GOVERNANCE   │              │    POLICY ENGINE    │            │   AUDIT SERVICE     │
│     CORE       │              │                     │            │                     │
│ ┌────────────┐ │              │ ┌─────────────────┐ │            │ ┌─────────────────┐ │
│ │ Policy Mgmt│ │◀────────────▶│ │ Rule Parser     │ │            │ │ Event Collector │ │
│ └────────────┘ │              │ │ Rule Evaluator  │ │            │ │ Log Storage     │ │
│ ┌────────────┐ │              │ │ Rule Registry │ │            │ │ Query Engine    │ │
│ │ Role Mgmt  │ │◀────────────▶│ └─────────────────┘ │            │ │ Report Gen      │ │
│ └────────────┘ │              └─────────────────────┘            │ └─────────────────┘ │
│ ┌────────────┐ │                                                   └─────────────────────┘
│ │ Config Mgmt│ │
│ └────────────┘ │
│ ┌────────────┐ │              ┌─────────────────────┐            ┌─────────────────────┐
│ │ Workflow   │ │◀────────────▶│  COMPLIANCE ENGINE  │            │  NOTIFICATION SVC   │
│ └────────────┘ │              │                     │            │                     │
└────────────────┘              │ ┌───────────────┐   │            │ ┌─────────────┐     │
                                │ │ Scanner Core│   │            │ │ Email       │     │
                                │ │ Check Runner│   │            │ │ Slack       │     │
                                │ │ Reporter    │   │            │ │ Webhook     │     │
                                │ └───────────────┘   │            │ └─────────────┘     │
                                └─────────────────────┘            └─────────────────────┘
```

---

## 3. Data Models

### 3.1 Core Domain Models (Rust)

```rust
//! Core governance domain models

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// Unique identifier for governance entities
pub type EntityId = Uuid;
pub type PolicyId = Uuid;
pub type RuleId = Uuid;
pub type AuditId = Uuid;

/// Policy definition for governance enforcement
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Policy {
    pub id: PolicyId,
    pub name: String,
    pub description: String,
    pub version: String,
    pub status: PolicyStatus,
    pub scope: PolicyScope,
    pub rules: Vec<Rule>,
    pub metadata: PolicyMetadata,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub created_by: String,
    pub updated_by: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum PolicyStatus {
    Draft,
    Active,
    Deprecated,
    Archived,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum PolicyScope {
    Global,
    Organization { org_id: String },
    Project { project_id: String },
    Team { team_id: String },
    Resource { resource_type: String },
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
pub struct PolicyMetadata {
    pub tags: Vec<String>,
    pub priority: i32,
    pub auto_apply: bool,
    pub requires_approval: bool,
    pub approval_workflow_id: Option<Uuid>,
    pub custom_properties: HashMap<String, String>,
}

/// Governance rule with evaluation logic
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Rule {
    pub id: RuleId,
    pub policy_id: PolicyId,
    pub name: String,
    pub description: String,
    pub rule_type: RuleType,
    pub condition: RuleCondition,
    pub action: RuleAction,
    pub severity: Severity,
    pub metadata: RuleMetadata,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum RuleType {
    Validation,
    Restriction,
    Requirement,
    Workflow,
    Notification,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RuleCondition {
    pub expression: String,
    pub operator: ConditionOperator,
    pub operands: Vec<ConditionOperand>,
    pub evaluation_context: EvaluationContext,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ConditionOperator {
    Equals,
    NotEquals,
    GreaterThan,
    LessThan,
    Contains,
    Matches,
    In,
    NotIn,
    Exists,
    All,
    Any,
    None,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ConditionOperand {
    pub value_type: OperandType,
    pub value: serde_json::Value,
    pub path: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum OperandType {
    String,
    Number,
    Boolean,
    Array,
    Object,
    Reference,
    Function,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct EvaluationContext {
    pub requires_data_sources: Vec<DataSource>,
    pub caching_strategy: CachingStrategy,
    pub timeout_ms: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum DataSource {
    Database { table: String },
    Api { endpoint: String },
    Cache { key_pattern: String },
    External { service: String },
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum CachingStrategy {
    NoCache,
    CacheForSeconds(u64),
    CacheUntilInvalidated,
}

/// Action to take when rule evaluates to true
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum RuleAction {
    Allow,
    Deny { reason: String },
    Warn { message: String },
    RequireApproval { workflow_id: Uuid },
    TriggerWorkflow { workflow_id: Uuid },
    Notify { channels: Vec<NotificationChannel> },
    Log { level: LogLevel },
    Mutate { transformation: Transformation },
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum NotificationChannel {
    Email { recipients: Vec<String> },
    Slack { channel: String },
    Webhook { url: String, headers: HashMap<String, String> },
    Sms { phone_numbers: Vec<String> },
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum LogLevel {
    Debug,
    Info,
    Warning,
    Error,
    Critical,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Transformation {
    pub target_field: String,
    pub operation: TransformOperation,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TransformOperation {
    SetValue(serde_json::Value),
    RemoveField,
    AddLabel { key: String, value: String },
    Encrypt { algorithm: String },
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum Severity {
    Critical,
    High,
    Medium,
    Low,
    Info,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
pub struct RuleMetadata {
    pub category: String,
    pub tags: Vec<String>,
    pub documentation_url: Option<String>,
    pub remediation_guide: Option<String>,
    pub custom_properties: HashMap<String, String>,
}

/// Compliance violation record
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Violation {
    pub id: Uuid,
    pub policy_id: PolicyId,
    pub rule_id: RuleId,
    pub severity: Severity,
    pub title: String,
    pub description: String,
    pub resource: ResourceReference,
    pub context: ViolationContext,
    pub status: ViolationStatus,
    pub remediation: Option<RemediationPlan>,
    pub created_at: DateTime<Utc>,
    pub resolved_at: Option<DateTime<Utc>>,
    pub resolved_by: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ResourceReference {
    pub resource_type: String,
    pub resource_id: String,
    pub resource_name: String,
    pub location: String,
    pub owner: String,
    pub metadata: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ViolationContext {
    pub triggered_by: String,
    pub trigger_event: String,
    pub evaluated_conditions: Vec<EvaluatedCondition>,
    pub data_snapshot: serde_json::Value,
    pub environment: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct EvaluatedCondition {
    pub condition_id: String,
    pub expression: String,
    pub result: bool,
    pub actual_value: serde_json::Value,
    pub expected_value: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ViolationStatus {
    Open,
    Acknowledged,
    InRemediation,
    Resolved,
    FalsePositive,
    Suppressed,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RemediationPlan {
    pub steps: Vec<RemediationStep>,
    pub estimated_duration_minutes: u32,
    pub requires_approval: bool,
    pub auto_remediate: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RemediationStep {
    pub step_number: u32,
    pub title: String,
    pub description: String,
    pub action_type: RemediationActionType,
    pub status: RemediationStepStatus,
    pub result: Option<RemediationResult>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum RemediationActionType {
    Manual { instructions: String },
    Automated { script: String, parameters: HashMap<String, String> },
    ApiCall { endpoint: String, method: String, payload: serde_json::Value },
    Workflow { workflow_id: Uuid },
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum RemediationStepStatus {
    Pending,
    InProgress,
    Completed,
    Failed,
    Skipped,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RemediationResult {
    pub success: bool,
    pub message: String,
    pub output: Option<String>,
    pub completed_at: DateTime<Utc>,
}

/// Audit trail entry for all governance actions
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct AuditRecord {
    pub id: AuditId,
    pub event_type: AuditEventType,
    pub actor: Actor,
    pub action: GovernanceAction,
    pub target: Target,
    pub outcome: ActionOutcome,
    pub context: AuditContext,
    pub timestamp: DateTime<Utc>,
    pub correlation_id: Uuid,
    pub session_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum AuditEventType {
    PolicyCreated,
    PolicyUpdated,
    PolicyDeleted,
    PolicyActivated,
    PolicyDeactivated,
    RuleEvaluated,
    RuleTriggered,
    ViolationDetected,
    ViolationResolved,
    ApprovalRequested,
    ApprovalGranted,
    ApprovalDenied,
    ConfigChanged,
    RoleAssigned,
    RoleRevoked,
    AccessGranted,
    AccessDenied,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Actor {
    pub actor_type: ActorType,
    pub id: String,
    pub name: String,
    pub email: Option<String>,
    pub ip_address: Option<String>,
    pub user_agent: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ActorType {
    User,
    ServiceAccount,
    System,
    Automation,
    External,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct GovernanceAction {
    pub action_type: String,
    pub parameters: HashMap<String, serde_json::Value>,
    pub justification: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Target {
    pub target_type: String,
    pub target_id: String,
    pub target_name: String,
    pub resource_path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ActionOutcome {
    pub success: bool,
    pub result_code: String,
    pub result_message: String,
    pub result_data: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct AuditContext {
    pub request_id: Uuid,
    pub trace_id: String,
    pub span_id: String,
    pub environment: String,
    pub region: String,
    pub additional_data: HashMap<String, serde_json::Value>,
}

/// Role-based access control definitions
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Role {
    pub id: Uuid,
    pub name: String,
    pub description: String,
    pub permissions: Vec<Permission>,
    pub scope: RoleScope,
    pub conditions: Vec<RoleCondition>,
    pub metadata: RoleMetadata,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Permission {
    pub resource: String,
    pub action: String,
    pub effect: PermissionEffect,
    pub conditions: Vec<PermissionCondition>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum PermissionEffect {
    Allow,
    Deny,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PermissionCondition {
    pub attribute: String,
    pub operator: String,
    pub value: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum RoleScope {
    Global,
    Organization(String),
    Project(String),
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RoleCondition {
    pub condition_type: String,
    pub parameters: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
pub struct RoleMetadata {
    pub is_system_role: bool,
    pub tags: Vec<String>,
    pub max_session_duration_hours: u32,
}

/// Approval workflow configuration
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ApprovalWorkflow {
    pub id: Uuid,
    pub name: String,
    pub description: String,
    pub steps: Vec<ApprovalStep>,
    pub configuration: WorkflowConfiguration,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ApprovalStep {
    pub step_number: u32,
    pub name: String,
    pub approver_type: ApproverType,
    pub approvers: Vec<String>,
    pub timeout_hours: u32,
    pub escalation_policy: EscalationPolicy,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ApproverType {
    User,
    Role,
    Team,
    ExternalService,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct EscalationPolicy {
    pub enabled: bool,
    pub escalation_hours: u32,
    pub escalate_to: Vec<String>,
    pub auto_approve_on_timeout: bool,
    pub auto_reject_on_timeout: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct WorkflowConfiguration {
    pub allow_parallel_approvals: bool,
    pub require_all_approvers: bool,
    pub min_approvals_required: u32,
    pub max_approvals_allowed: u32,
}

/// Governance configuration
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct GovernanceConfig {
    pub enforcement_mode: EnforcementMode,
    pub audit_retention_days: u32,
    pub violation_retention_days: u32,
    pub auto_remediation_enabled: bool,
    pub notification_defaults: NotificationDefaults,
    pub compliance_schedule: ComplianceSchedule,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum EnforcementMode {
    AuditOnly,
    Warn,
    Enforce,
    Strict,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct NotificationDefaults {
    pub channels: Vec<NotificationChannel>,
    pub min_severity: Severity,
    pub digest_enabled: bool,
    pub digest_frequency_hours: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ComplianceSchedule {
    pub enabled_checks: Vec<String>,
    pub schedule_expression: String,
    pub timezone: String,
    pub notification_recipients: Vec<String>,
}

/// Request/Response types for API operations
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct EvaluatePolicyRequest {
    pub policy_id: PolicyId,
    pub context: EvaluationContextRequest,
    pub resource_data: serde_json::Value,
    pub actor: Actor,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct EvaluationContextRequest {
    pub resource_type: String,
    pub resource_id: String,
    pub action: String,
    pub environment: HashMap<String, String>,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct EvaluatePolicyResponse {
    pub evaluation_id: Uuid,
    pub policy_id: PolicyId,
    pub outcome: PolicyOutcome,
    pub triggered_rules: Vec<TriggeredRule>,
    pub violations: Vec<Violation>,
    pub actions_taken: Vec<ActionTaken>,
    pub execution_time_ms: u64,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum PolicyOutcome {
    Compliant,
    NonCompliant,
    PartiallyCompliant,
    RequiresReview,
    Error,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TriggeredRule {
    pub rule_id: RuleId,
    pub rule_name: String,
    pub severity: Severity,
    pub condition_results: Vec<ConditionResult>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ConditionResult {
    pub condition_id: String,
    pub passed: bool,
    pub actual_value: serde_json::Value,
    pub expected_value: serde_json::Value,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ActionTaken {
    pub action_type: String,
    pub success: bool,
    pub message: String,
    pub executed_at: DateTime<Utc>,
}

/// Search and filtering types
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
pub struct ViolationSearchQuery {
    pub policy_ids: Option<Vec<PolicyId>>,
    pub severity_levels: Option<Vec<Severity>>,
    pub status: Option<Vec<ViolationStatus>>,
    pub resource_types: Option<Vec<String>>,
    pub date_range: Option<DateRange>,
    pub text_query: Option<String>,
    pub pagination: PaginationParams,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DateRange {
    pub from: DateTime<Utc>,
    pub to: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
pub struct PaginationParams {
    pub page: u32,
    pub per_page: u32,
    pub sort_by: String,
    pub sort_order: SortOrder,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SortOrder {
    Ascending,
    Descending,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ViolationSearchResult {
    pub items: Vec<Violation>,
    pub total_count: u64,
    pub page: u32,
    pub per_page: u32,
    pub has_more: bool,
}
```

---

## 4. API Specifications

### 4.1 REST API Endpoints

#### Base URL
```
https://api.phenotype.io/v1/governance
```

#### Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer <access_token>
X-API-Version: 2024-01
```

### 4.2 Policy Management API

#### Create Policy
```http
POST /policies
Content-Type: application/json

{
  "name": "security-code-review-policy",
  "description": "Enforces code review requirements for security-sensitive changes",
  "version": "1.0.0",
  "scope": {
    "type": "Global"
  },
  "rules": [
    {
      "name": "require-security-review",
      "rule_type": "Requirement",
      "condition": {
        "expression": "files.matches('**/security/**') OR files.matches('**/auth/**')",
        "operator": "Any",
        "operands": []
      },
      "action": {
        "type": "RequireApproval",
        "workflow_id": "550e8400-e29b-41d4-a716-446655440000"
      },
      "severity": "High"
    }
  ],
  "metadata": {
    "tags": ["security", "compliance"],
    "priority": 100,
    "auto_apply": true,
    "requires_approval": false
  }
}
```

**Response (201 Created):**
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "name": "security-code-review-policy",
  "status": "Draft",
  "created_at": "2026-04-06T10:30:00Z",
  "updated_at": "2026-04-06T10:30:00Z",
  "created_by": "admin@phenotype.io",
  "version": "1.0.0"
}
```

#### Get Policy
```http
GET /policies/{policy_id}
```

**Response (200 OK):**
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "name": "security-code-review-policy",
  "description": "Enforces code review requirements for security-sensitive changes",
  "version": "1.0.0",
  "status": "Active",
  "scope": {
    "type": "Global"
  },
  "rules": [
    {
      "id": "rule-001",
      "policy_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "name": "require-security-review",
      "rule_type": "Requirement",
      "condition": {
        "expression": "files.matches('**/security/**')",
        "operator": "Matches",
        "operands": [
          {
            "value_type": "String",
            "value": "**/security/**",
            "path": "files.pattern"
          }
        ],
        "evaluation_context": {
          "requires_data_sources": [],
          "caching_strategy": "NoCache",
          "timeout_ms": 5000
        }
      },
      "action": {
        "type": "RequireApproval",
        "workflow_id": "550e8400-e29b-41d4-a716-446655440000"
      },
      "severity": "High",
      "metadata": {
        "category": "Security",
        "tags": ["code-review", "security"]
      }
    }
  ],
  "metadata": {
    "tags": ["security", "compliance"],
    "priority": 100,
    "auto_apply": true,
    "requires_approval": false
  },
  "created_at": "2026-04-06T10:30:00Z",
  "updated_at": "2026-04-06T11:45:00Z",
  "created_by": "admin@phenotype.io",
  "updated_by": "admin@phenotype.io"
}
```

#### List Policies
```http
GET /policies?status=Active&scope_type=Global&page=1&per_page=50
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "name": "security-code-review-policy",
      "status": "Active",
      "scope": { "type": "Global" },
      "rule_count": 3,
      "created_at": "2026-04-06T10:30:00Z",
      "updated_at": "2026-04-06T11:45:00Z"
    }
  ],
  "total_count": 1,
  "page": 1,
  "per_page": 50,
  "has_more": false
}
```

#### Update Policy
```http
PUT /policies/{policy_id}
Content-Type: application/json

{
  "name": "security-code-review-policy-v2",
  "description": "Updated policy with additional compliance checks",
  "version": "1.1.0",
  "status": "Draft"
}
```

#### Activate Policy
```http
POST /policies/{policy_id}/activate
```

#### Delete Policy
```http
DELETE /policies/{policy_id}
```

### 4.3 Policy Evaluation API

#### Evaluate Policy
```http
POST /evaluate
Content-Type: application/json

{
  "policy_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "context": {
    "resource_type": "pull_request",
    "resource_id": "pr-12345",
    "action": "merge",
    "environment": {
      "repository": "phenotype-core",
      "branch": "main",
      "changed_files": "src/security/auth.rs,src/api/endpoints.rs"
    },
    "metadata": {
      "author": "developer@phenotype.io",
      "commit_count": 5,
      "is_draft": false
    }
  },
  "resource_data": {
    "title": "Add OAuth2 authentication",
    "files": [
      { "path": "src/security/auth.rs", "lines_added": 150, "lines_deleted": 20 },
      { "path": "src/api/endpoints.rs", "lines_added": 50, "lines_deleted": 10 }
    ],
    "reviewers": ["senior-dev@phenotype.io"],
    "approvals": 1
  },
  "actor": {
    "actor_type": "User",
    "id": "user-123",
    "name": "John Developer",
    "email": "developer@phenotype.io"
  }
}
```

**Response (200 OK):**
```json
{
  "evaluation_id": "eval-789",
  "policy_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "outcome": "NonCompliant",
  "triggered_rules": [
    {
      "rule_id": "rule-001",
      "rule_name": "require-security-review",
      "severity": "High",
      "condition_results": [
        {
          "condition_id": "cond-1",
          "passed": true,
          "actual_value": "src/security/auth.rs",
          "expected_value": "**/security/**",
          "message": "File path matches security pattern"
        }
      ]
    }
  ],
  "violations": [
    {
      "id": "viol-456",
      "policy_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "rule_id": "rule-001",
      "severity": "High",
      "title": "Security review required",
      "description": "Changes to security-related files require additional security review",
      "resource": {
        "resource_type": "pull_request",
        "resource_id": "pr-12345",
        "resource_name": "Add OAuth2 authentication",
        "location": "phenotype-core/main",
        "owner": "developer@phenotype.io"
      },
      "status": "Open",
      "created_at": "2026-04-06T10:30:00Z"
    }
  ],
  "actions_taken": [
    {
      "action_type": "RequireApproval",
      "success": true,
      "message": "Approval workflow triggered",
      "executed_at": "2026-04-06T10:30:00Z"
    }
  ],
  "execution_time_ms": 45,
  "timestamp": "2026-04-06T10:30:00Z"
}
```

#### Batch Evaluate
```http
POST /evaluate/batch
Content-Type: application/json

{
  "evaluations": [
    {
      "policy_id": "policy-1",
      "context": { "resource_type": "pull_request", "resource_id": "pr-123" },
      "resource_data": {},
      "actor": { "actor_type": "User", "id": "user-1", "name": "User" }
    },
    {
      "policy_id": "policy-2",
      "context": { "resource_type": "deployment", "resource_id": "dep-456" },
      "resource_data": {},
      "actor": { "actor_type": "ServiceAccount", "id": "svc-1", "name": "Service" }
    }
  ]
}
```

### 4.4 Violation Management API

#### List Violations
```http
GET /violations?severity=High,Critical&status=Open&page=1&per_page=100
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "viol-456",
      "policy_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "rule_id": "rule-001",
      "severity": "High",
      "title": "Security review required",
      "description": "Changes to security-related files require additional security review",
      "resource": {
        "resource_type": "pull_request",
        "resource_id": "pr-12345",
        "resource_name": "Add OAuth2 authentication",
        "location": "phenotype-core/main",
        "owner": "developer@phenotype.io"
      },
      "context": {
        "triggered_by": "policy-evaluation",
        "trigger_event": "pull_request.merge_attempt",
        "evaluated_conditions": [],
        "data_snapshot": {},
        "environment": {}
      },
      "status": "Open",
      "remediation": {
        "steps": [
          {
            "step_number": 1,
            "title": "Request security review",
            "description": "Tag @security-team for review",
            "action_type": { "Manual": { "instructions": "Comment on PR with /security-review" } },
            "status": "Pending"
          }
        ],
        "estimated_duration_minutes": 60,
        "requires_approval": true,
        "auto_remediate": false
      },
      "created_at": "2026-04-06T10:30:00Z",
      "resolved_at": null,
      "resolved_by": null
    }
  ],
  "total_count": 1,
  "page": 1,
  "per_page": 100,
  "has_more": false
}
```

#### Get Violation
```http
GET /violations/{violation_id}
```

#### Update Violation Status
```http
PATCH /violations/{violation_id}
Content-Type: application/json

{
  "status": "Acknowledged",
  "resolution_notes": "Security team notified, awaiting review"
}
```

#### Resolve Violation
```http
POST /violations/{violation_id}/resolve
Content-Type: application/json

{
  "resolution_type": "Manual",
  "resolution_notes": "Security review completed by @security-lead",
  "resolved_by": "security-lead@phenotype.io"
}
```

### 4.5 Audit API

#### Query Audit Log
```http
GET /audit?event_type=PolicyCreated,RuleEvaluated&actor_id=user-123&from=2026-04-01&to=2026-04-06&page=1&per_page=100
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "audit-001",
      "event_type": "RuleEvaluated",
      "actor": {
        "actor_type": "System",
        "id": "governance-engine",
        "name": "Governance Engine"
      },
      "action": {
        "action_type": "evaluate_policy",
        "parameters": {
          "policy_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
          "resource_id": "pr-12345"
        },
        "justification": null
      },
      "target": {
        "target_type": "pull_request",
        "target_id": "pr-12345",
        "target_name": "Add OAuth2 authentication",
        "resource_path": "/repos/phenotype-core/pulls/12345"
      },
      "outcome": {
        "success": true,
        "result_code": "RULE_TRIGGERED",
        "result_message": "Security review rule triggered",
        "result_data": { "violation_id": "viol-456" }
      },
      "context": {
        "request_id": "req-789",
        "trace_id": "trace-abc-123",
        "span_id": "span-xyz-456",
        "environment": "production",
        "region": "us-east-1"
      },
      "timestamp": "2026-04-06T10:30:00Z",
      "correlation_id": "corr-xyz-789",
      "session_id": "sess-abc-123"
    }
  ],
  "total_count": 150,
  "page": 1,
  "per_page": 100,
  "has_more": true
}
```

#### Export Audit Log
```http
POST /audit/export
Content-Type: application/json

{
  "format": "json",
  "date_range": {
    "from": "2026-04-01T00:00:00Z",
    "to": "2026-04-06T23:59:59Z"
  },
  "event_types": ["PolicyCreated", "PolicyUpdated", "ViolationDetected"],
  "delivery": {
    "method": "s3",
    "s3_bucket": "phenotype-audit-exports",
    "s3_key": "audit-exports/2026-04.json.gz"
  }
}
```

### 4.6 WebSocket Real-time Events

#### Connect to Event Stream
```javascript
const ws = new WebSocket('wss://api.phenotype.io/v1/governance/events');

ws.onopen = () => {
  // Subscribe to specific event types
  ws.send(JSON.stringify({
    action: 'subscribe',
    channels: ['violations', 'policy_changes', 'audit_events'],
    filters: {
      severity: ['High', 'Critical'],
      resource_types: ['pull_request', 'deployment']
    }
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Governance event:', data);
};
```

**Event Format:**
```json
{
  "event_id": "evt-123",
  "event_type": "violation_detected",
  "timestamp": "2026-04-06T10:30:00Z",
  "payload": {
    "violation_id": "viol-456",
    "severity": "High",
    "resource": {
      "type": "pull_request",
      "id": "pr-12345"
    }
  },
  "correlation_id": "corr-xyz-789"
}
```

---

## 5. Configuration

### 5.1 System Configuration (TOML)

```toml
# phenotype-governance.toml
# System-wide governance configuration

[server]
host = "0.0.0.0"
port = 8080
workers = 4
request_timeout_seconds = 30
max_request_size_mb = 10

[database]
url = "postgresql://localhost:5432/phenotype_governance"
pool_size = 20
connection_timeout_seconds = 5
idle_timeout_seconds = 300

[cache]
provider = "redis"
url = "redis://localhost:6379"
ttl_seconds = 300
eviction_policy = "allkeys-lru"

[audit]
retention_days = 365
storage_backend = "s3"
batch_size = 1000
flush_interval_seconds = 60

[audit.s3]
bucket = "phenotype-audit-logs"
region = "us-east-1"
prefix = "governance/"

[notifications]
default_channels = ["email", "slack"]
min_severity = "Medium"
digest_enabled = true
digest_frequency_hours = 24

[notifications.email]
provider = "sendgrid"
from_address = "governance@phenotype.io"
template_id = "d-governance-alert"

[notifications.slack]
webhook_url = "${SLACK_WEBHOOK_URL}"
channel = "#governance-alerts"
username = "GovernanceBot"

[enforcement]
mode = "Enforce"
auto_remediation_enabled = false
evaluation_timeout_ms = 5000
max_rule_chain_depth = 10

[compliance]
enabled_checks = ["security", "access_control", "data_protection"]
schedule_expression = "0 0 * * *"
timezone = "UTC"
notification_recipients = ["compliance@phenotype.io"]

[logging]
level = "info"
format = "json"
output = "stdout"
include_trace_ids = true

[metrics]
enabled = true
endpoint = "/metrics"
provider = "prometheus"
report_interval_seconds = 60

[security]
api_key_header = "X-API-Key"
rate_limit_requests_per_minute = 1000
enable_request_signing = true
trusted_proxies = ["10.0.0.0/8", "172.16.0.0/12"]

[rbac]
enabled = true
cache_roles_seconds = 300
default_role = "viewer"
admin_roles = ["admin", "super-admin"]
```

### 5.2 Policy DSL (YAML)

```yaml
# policy-definition.yaml
# Example policy definition using the governance DSL

api_version: governance.phenotype.io/v1
kind: Policy
metadata:
  name: security-sensitive-changes
  description: Enforces additional controls for security-sensitive changes
  version: "2.1.0"
  labels:
    category: security
    compliance: soc2
    priority: critical
  annotations:
    documentation_url: https://docs.phenotype.io/policies/security-sensitive
    remediation_guide: https://docs.phenotype.io/remediations/security-review

spec:
  scope:
    type: Organization
    org_id: "phenotype"

  enforcement:
    mode: Enforce
    auto_apply: true
    requires_approval: true
    approval_workflow: security-review-workflow

  rules:
    - name: require-security-team-review
      rule_type: Requirement
      description: Security-related changes require review from security team
      severity: Critical
      condition:
        all:
          - condition:
              operator: Matches
              path: files.changed
              value: "**/security/**,**/auth/**,**/crypto/**"
          - condition:
              operator: NotIn
              path: reviewers.teams
              value: ["security"]
      action:
        type: RequireApproval
        parameters:
          workflow_id: security-team-review
          min_approvers: 2
          required_teams: ["security"]
      metadata:
        category: code-review
        tags: ["security", "compliance"]

    - name: block-secrets-in-code
      rule_type: Restriction
      description: Prevent hardcoded secrets in source code
      severity: Critical
      condition:
        any:
          - condition:
              operator: Matches
              path: files.content
              value: "(password|secret|key|token)\s*=\s*['\"][^'\"]+['\"]"
          - condition:
              operator: Matches
              path: files.content
              value: "AWS_ACCESS_KEY_ID|AKIA[0-9A-Z]{16}"
          - condition:
              operator: Matches
              path: files.content
              value: "PRIVATE KEY|ssh-rsa"
      action:
        type: Deny
        parameters:
          reason: "Potential secrets detected in code. Use secret management system."
          block_merge: true
          notify:
            channels: [email, slack]
            recipients: ["security@phenotype.io"]
            severity: Critical
      metadata:
        category: secret-detection
        tags: ["security", "secrets", "compliance"]

    - name: warn-on-large-security-changes
      rule_type: Validation
      description: Warn when security-related changes exceed threshold
      severity: Medium
      condition:
        all:
          - condition:
              operator: Matches
              path: files.changed
              value: "**/security/**"
          - condition:
              operator: GreaterThan
              path: files.total_lines_changed
              value: 500
      action:
        type: Warn
        parameters:
          message: "Large security-related changes detected. Consider breaking into smaller PRs."
          notify:
            channels: [slack]
            recipients: ["#security-alerts"]
      metadata:
        category: change-management
        tags: ["security", "best-practice"]

    - name: require-tests-for-security-code
      rule_type: Requirement
      description: Security code changes must include tests
      severity: High
      condition:
        all:
          - condition:
              operator: Matches
              path: files.changed
              value: "**/security/**"
          - condition:
              operator: NotMatches
              path: files.changed
              value: "**/tests/**,**/*_test.go,**/*.spec.ts"
      action:
        type: RequireApproval
        parameters:
          workflow_id: security-test-exception
          message: "Security code changes should include tests. Request exception if justified."
      metadata:
        category: testing
        tags: ["security", "testing"]

  remediation:
    auto_remediate: false
    default_workflow: manual-security-review
    escalation_policy:
      enabled: true
      escalation_hours: 24
      escalate_to: ["security-lead@phenotype.io"]
```

### 5.3 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOVERNANCE_SERVER_HOST` | Server bind address | `0.0.0.0` | No |
| `GOVERNANCE_SERVER_PORT` | Server port | `8080` | No |
| `GOVERNANCE_DATABASE_URL` | PostgreSQL connection URL | - | Yes |
| `GOVERNANCE_REDIS_URL` | Redis connection URL | - | Yes |
| `GOVERNANCE_LOG_LEVEL` | Logging level | `info` | No |
| `GOVERNANCE_ENFORCEMENT_MODE` | Policy enforcement mode | `Enforce` | No |
| `GOVERNANCE_AUDIT_S3_BUCKET` | S3 bucket for audit logs | - | Yes |
| `GOVERNANCE_SLACK_WEBHOOK_URL` | Slack webhook for notifications | - | No |
| `GOVERNANCE_EMAIL_API_KEY` | Email service API key | - | No |
| `GOVERNANCE_JWT_SECRET` | JWT signing secret | - | Yes |
| `GOVERNANCE_API_RATE_LIMIT` | Requests per minute | `1000` | No |

---

## 6. Performance Benchmarks

### 6.1 Target Performance Metrics

| Metric | Target | Critical Threshold | Measurement Method |
|--------|--------|-------------------|-------------------|
| Policy Evaluation Latency (p50) | < 50ms | 100ms | Synthetic transactions |
| Policy Evaluation Latency (p99) | < 200ms | 500ms | Synthetic transactions |
| Violation Detection Rate | > 10K/sec | 5K/sec | Load testing |
| Audit Log Write Throughput | > 50K/sec | 20K/sec | Load testing |
| API Request Throughput | > 5K RPS | 2K RPS | Load testing |
| Database Query Time (p99) | < 20ms | 50ms | Query metrics |
| Cache Hit Rate | > 95% | 85% | Cache statistics |
| Memory Usage | < 2GB | 4GB | Resource monitoring |
| CPU Usage | < 70% | 90% | Resource monitoring |

### 6.2 Load Testing Scenarios

```yaml
# load-test-scenarios.yaml

scenarios:
  - name: policy_evaluation_baseline
    description: Baseline policy evaluation throughput
    duration_minutes: 10
    virtual_users: 100
    ramp_up_seconds: 30

    steps:
      - name: evaluate_simple_policy
        weight: 70
        request:
          endpoint: POST /evaluate
          body:
            policy_id: "simple-policy"
            context: { resource_type: "test", resource_id: "test-001" }
            resource_data: {}
        expected_response_time_ms: 50

      - name: evaluate_complex_policy
        weight: 30
        request:
          endpoint: POST /evaluate
          body:
            policy_id: "complex-policy"
            context: { resource_type: "test", resource_id: "test-002" }
            resource_data: { large: true, nested: { data: "value" } }
        expected_response_time_ms: 200

  - name: violation_detection_stress
    description: Stress test violation detection pipeline
    duration_minutes: 5
    virtual_users: 500
    ramp_up_seconds: 60

    steps:
      - name: generate_violations
        weight: 100
        request:
          endpoint: POST /evaluate
          body:
            policy_id: "strict-policy"
            context: { resource_type: "trigger", resource_id: "{{random}}" }
        expected_violation_rate: 0.8

  - name: audit_log_throughput
    description: Test audit log write throughput
    duration_minutes: 10
    virtual_users: 200

    steps:
      - name: mixed_operations
        weight: 100
        requests:
          - endpoint: GET /policies
          - endpoint: POST /evaluate
          - endpoint: GET /violations
        expected_audit_entries_per_second: 50000
```

### 6.3 Performance Optimization Strategies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PERFORMANCE OPTIMIZATION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │   CACHING LAYER  │    │  CONNECTION POOL │    │  ASYNC PROCESSING│      │
│  │                  │    │                  │    │                  │      │
│  │ • Policy Cache   │    │ • DB Pool (20)   │    │ • Rule Eval      │      │
│  │ • Rule Cache     │    │ • Redis Pool     │    │ • Audit Writes   │      │
│  │ • Role Cache     │    │ • HTTP Clients   │    │ • Notifications  │      │
│  │ • TTL: 5 min     │    │ • Keep-alive     │    │ • Batch Ops      │      │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘      │
│                                                                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │  QUERY OPTIMIZATION│   │  BATCHING        │    │  INDEXING        │      │
│  │                    │   │                  │    │                  │      │
│  │ • Prepared Stmts   │   │ • Audit Batch    │    │ • Policy ID      │      │
│  │ • Selective Fields │   │ • Rule Chain     │    │ • Resource ID    │      │
│  │ • Query Planning   │   │ • Notification   │    │ • Timestamp      │      │
│  │ • Result Caching   │   │ • Bulk Inserts   │    │ • Severity       │      │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Security Model

### 7.1 Authentication & Authorization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AUTHENTICATION FLOW                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Client                    API Gateway                    Auth Service     │
│    │                           │                              │            │
│    │  1. Request + API Key     │                              │            │
│    │──────────────────────────▶│                              │            │
│    │                           │  2. Validate Token           │            │
│    │                           │─────────────────────────────▶│            │
│    │                           │                              │            │
│    │                           │  3. Token Valid + Claims    │            │
│    │                           │◀─────────────────────────────│            │
│    │                           │                              │            │
│    │                           │  4. Enrich with RBAC        │            │
│    │                           │─────────────────────────────┐            │
│    │                           │                             │            │
│    │                           │  5. Roles & Permissions    │            │
│    │                           │◀────────────────────────────┘            │
│    │                           │                              │            │
│    │                           │  6. Request + Context         │            │
│    │                           │──────────────────────────────│            │
│    │                           │                              │            │
│    │     7. Response           │                              │            │
│    │◀──────────────────────────│                              │            │
│    │                           │                              │            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 RBAC Matrix

| Role | Policy Read | Policy Write | Rule Eval | Violation Read | Violation Write | Audit Read | Admin |
|------|:-----------:|:------------:|:---------:|:--------------:|:---------------:|:----------:|:-----:|
| viewer | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| developer | ✅ | ❌ | ✅ | ✅ | ✅ (own) | ❌ | ❌ |
| security | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| admin | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| service | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |

### 7.3 Security Controls

| Control | Implementation | Verification |
|---------|---------------|--------------|
| API Authentication | JWT with RS256 | Token validation middleware |
| Request Signing | HMAC-SHA256 | Signature verification |
| Rate Limiting | Token bucket algorithm | Middleware enforcement |
| Input Validation | JSON Schema + custom validators | Request preprocessing |
| SQL Injection Prevention | Parameterized queries | ORM layer |
| XSS Prevention | Output encoding | Response middleware |
| Audit Logging | Immutable S3 + tamper detection | Log verification |
| Encryption at Rest | AES-256-GCM | Database encryption |
| Encryption in Transit | TLS 1.3 | Network layer |
| Secret Management | HashiCorp Vault | Secret rotation |

### 7.4 Threat Model

| Threat | Likelihood | Impact | Mitigation |
|--------|-----------|--------|------------|
| Unauthorized policy modification | Low | Critical | MFA + approval workflow |
| Audit log tampering | Low | Critical | Immutable storage + checksums |
| Policy evaluation bypass | Medium | High | Defense in depth + monitoring |
| DoS via complex rules | Medium | Medium | Timeout + complexity limits |
| Data exfiltration | Low | Critical | Encryption + access controls |
| Privilege escalation | Low | Critical | RBAC + least privilege |

---

## 8. Deployment Guide

### 8.1 Infrastructure Requirements

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| CPU | 2 cores | 4+ cores | For rule evaluation |
| Memory | 4GB | 8GB+ | Includes caching |
| Storage | 100GB SSD | 500GB SSD | Audit logs grow |
| PostgreSQL | 2 cores, 4GB | 4 cores, 8GB | Connection pooling |
| Redis | 1GB | 4GB | Policy/rule cache |
| Network | 100Mbps | 1Gbps | API throughput |

### 8.2 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION DEPLOYMENT                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                               ┌─────────────┐                              │
│                               │   CDN/WAF   │                              │
│                               │  (CloudFlare)│                              │
│                               └──────┬──────┘                              │
│                                      │                                      │
│                               ┌──────▼──────┐                              │
│                               │  Load Balancer│                            │
│                               │   (HAProxy)  │                             │
│                               └──────┬──────┘                              │
│                                      │                                      │
│        ┌─────────────────────────────┼─────────────────────────────┐       │
│        │                             │                             │       │
│  ┌─────▼─────┐               ┌──────▼──────┐               ┌──────▼──────┐│
│  │ API Server│               │  API Server │               │  API Server ││
│  │   #1      │               │    #2       │               │    #3       ││
│  │           │               │             │               │             ││
│  │ • REST    │               │  • REST     │               │  • REST     ││
│  │ • GraphQL │               │  • GraphQL  │               │  • GraphQL  ││
│  │ • WS      │               │  • WS       │               │  • WS       ││
│  └─────┬─────┘               └──────┬──────┘               └──────┬──────┘│
│        │                             │                             │       │
│        └─────────────────────────────┼─────────────────────────────┘       │
│                                      │                                      │
│        ┌─────────────────────────────┼─────────────────────────────┐       │
│        │                             │                             │       │
│  ┌─────▼─────┐               ┌──────▼──────┐               ┌──────▼──────┐│
│  │ PostgreSQL│               │    Redis    │               │    Kafka    ││
│  │ Primary   │◀───────────────▶│   Cluster   │◀─────────────▶│   (Events)  ││
│  │           │  Streaming Repl.│             │               │             ││
│  └─────┬─────┘               └─────────────┘               └─────────────┘│
│        │                                                                    │
│  ┌─────▼─────┐                                                             │
│  │PostgreSQL │                                                             │
│  │ Replica   │                                                             │
│  └───────────┘                                                             │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                         MONITORING STACK                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │  │
│  │  │ Prometheus  │  │   Grafana   │  │    Jaeger   │  │   Alert   │ │  │
│  │  │  (Metrics)  │  │ (Dashboards)│  │  (Tracing)  │  │  Manager  │ │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.3 Kubernetes Deployment

```yaml
# governance-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: phenotype-governance
  namespace: governance
  labels:
    app: phenotype-governance
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: phenotype-governance
  template:
    metadata:
      labels:
        app: phenotype-governance
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
    spec:
      serviceAccountName: governance-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: governance
          image: phenotype/governance:v1.0.0
          imagePullPolicy: Always
          ports:
            - containerPort: 8080
              name: http
              protocol: TCP
            - containerPort: 9090
              name: metrics
              protocol: TCP
          env:
            - name: GOVERNANCE_SERVER_HOST
              value: "0.0.0.0"
            - name: GOVERNANCE_SERVER_PORT
              value: "8080"
            - name: GOVERNANCE_DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: governance-db-secret
                  key: url
            - name: GOVERNANCE_REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: governance-redis-secret
                  key: url
            - name: GOVERNANCE_LOG_LEVEL
              value: "info"
            - name: GOVERNANCE_ENFORCEMENT_MODE
              value: "Enforce"
            - name: GOVERNANCE_JWT_SECRET
              valueFrom:
                secretKeyRef:
                  name: governance-auth-secret
                  key: jwt-secret
          resources:
            requests:
              memory: "2Gi"
              cpu: "1000m"
            limits:
              memory: "4Gi"
              cpu: "2000m"
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          volumeMounts:
            - name: config
              mountPath: /etc/governance
              readOnly: true
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: config
          configMap:
            name: governance-config
        - name: tmp
          emptyDir: {}
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchExpressions:
                    - key: app
                      operator: In
                      values:
                        - phenotype-governance
                topologyKey: kubernetes.io/hostname
---
apiVersion: v1
kind: Service
metadata:
  name: phenotype-governance
  namespace: governance
  labels:
    app: phenotype-governance
spec:
  type: ClusterIP
  ports:
    - port: 8080
      targetPort: 8080
      name: http
    - port: 9090
      targetPort: 9090
      name: metrics
  selector:
    app: phenotype-governance
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: phenotype-governance
  namespace: governance
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "1000"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
    - hosts:
        - governance.phenotype.io
      secretName: governance-tls
  rules:
    - host: governance.phenotype.io
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: phenotype-governance
                port:
                  number: 8080
```

### 8.4 Health Checks

```http
GET /health/live
```
Liveness probe - returns 200 if process is running.

```http
GET /health/ready
```
Readiness probe - returns 200 if dependencies (DB, cache) are healthy.

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "database": { "status": "up", "latency_ms": 5 },
    "cache": { "status": "up", "latency_ms": 2 },
    "event_bus": { "status": "up", "latency_ms": 8 }
  },
  "timestamp": "2026-04-06T10:30:00Z",
  "version": "1.0.0"
}
```

---

## 9. Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Policy** | A set of rules that define governance requirements |
| **Rule** | A condition-action pair within a policy |
| **Violation** | A record of non-compliance with a policy rule |
| **Enforcement Mode** | How strictly policies are applied (AuditOnly, Warn, Enforce) |
| **Remediation** | Actions to resolve a violation |
| **Audit Trail** | Immutable record of all governance actions |
| **Approval Workflow** | Multi-step process for obtaining authorization |
| **RBAC** | Role-Based Access Control |
| **Scope** | The boundary where a policy applies (Global, Org, Project) |
| **Severity** | The impact level of a violation (Critical, High, Medium, Low) |

### Appendix B: Error Codes

| Code | HTTP Status | Description | Resolution |
|------|-------------|-------------|------------|
| `POLICY_NOT_FOUND` | 404 | Policy does not exist | Verify policy ID |
| `POLICY_INVALID` | 400 | Policy definition is invalid | Check syntax and schema |
| `RULE_SYNTAX_ERROR` | 400 | Rule expression has syntax error | Review rule definition |
| `EVALUATION_TIMEOUT` | 504 | Policy evaluation exceeded timeout | Simplify rules or increase timeout |
| `CIRCULAR_RULE_CHAIN` | 400 | Rule dependencies form a cycle | Review rule dependencies |
| `VIOLATION_NOT_FOUND` | 404 | Violation ID does not exist | Verify violation ID |
| `UNAUTHORIZED` | 401 | Authentication required | Provide valid credentials |
| `FORBIDDEN` | 403 | Insufficient permissions | Check RBAC configuration |
| `RATE_LIMITED` | 429 | Too many requests | Wait and retry |
| `INTERNAL_ERROR` | 500 | Unexpected server error | Contact support |

### Appendix C: Event Types

| Event Type | Description | Payload Fields |
|------------|-------------|----------------|
| `policy.created` | New policy created | `policy_id`, `name`, `created_by` |
| `policy.updated` | Policy modified | `policy_id`, `changes`, `updated_by` |
| `policy.activated` | Policy activated | `policy_id`, `previous_status` |
| `policy.deactivated` | Policy deactivated | `policy_id`, `reason` |
| `rule.evaluated` | Rule was evaluated | `rule_id`, `policy_id`, `result` |
| `rule.triggered` | Rule conditions met | `rule_id`, `context`, `severity` |
| `violation.detected` | New violation found | `violation_id`, `severity`, `resource` |
| `violation.resolved` | Violation closed | `violation_id`, `resolution_type` |
| `approval.requested` | Approval needed | `workflow_id`, `requester`, `approvers` |
| `approval.granted` | Approval received | `workflow_id`, `approver`, `timestamp` |
| `approval.denied` | Approval rejected | `workflow_id`, `denier`, `reason` |
| `audit.exported` | Audit log exported | `export_id`, `format`, `location` |

### Appendix D: Database Schema

```sql
-- Policies table
CREATE TABLE policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Draft',
    scope_type VARCHAR(50) NOT NULL,
    scope_id VARCHAR(255),
    rules JSONB NOT NULL DEFAULT '[]',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    updated_by VARCHAR(255) NOT NULL,
    CONSTRAINT chk_status CHECK (status IN ('Draft', 'Active', 'Deprecated', 'Archived'))
);

CREATE INDEX idx_policies_status ON policies(status);
CREATE INDEX idx_policies_scope ON policies(scope_type, scope_id);

-- Violations table
CREATE TABLE violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL REFERENCES policies(id),
    rule_id VARCHAR(255) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    resource_type VARCHAR(255) NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    resource_name VARCHAR(500),
    resource_location VARCHAR(500),
    resource_owner VARCHAR(255),
    context JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) NOT NULL DEFAULT 'Open',
    remediation JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_by VARCHAR(255),
    CONSTRAINT chk_violation_status CHECK (status IN ('Open', 'Acknowledged', 'InRemediation', 'Resolved', 'FalsePositive', 'Suppressed'))
);

CREATE INDEX idx_violations_policy ON violations(policy_id);
CREATE INDEX idx_violations_status ON violations(status);
CREATE INDEX idx_violations_severity ON violations(severity);
CREATE INDEX idx_violations_resource ON violations(resource_type, resource_id);
CREATE INDEX idx_violations_created ON violations(created_at DESC);

-- Audit log table (partitioned by month)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    actor_type VARCHAR(50) NOT NULL,
    actor_id VARCHAR(255) NOT NULL,
    actor_name VARCHAR(255),
    action_type VARCHAR(100) NOT NULL,
    action_parameters JSONB,
    action_justification TEXT,
    target_type VARCHAR(100) NOT NULL,
    target_id VARCHAR(255) NOT NULL,
    target_name VARCHAR(500),
    resource_path TEXT,
    outcome_success BOOLEAN NOT NULL,
    outcome_code VARCHAR(100),
    outcome_message TEXT,
    outcome_data JSONB,
    request_id UUID NOT NULL,
    trace_id VARCHAR(255),
    span_id VARCHAR(255),
    environment VARCHAR(100),
    region VARCHAR(100),
    additional_data JSONB,
    correlation_id UUID NOT NULL,
    session_id VARCHAR(255),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions
CREATE TABLE audit_logs_2026_04 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_actor ON audit_logs(actor_type, actor_id);
CREATE INDEX idx_audit_correlation ON audit_logs(correlation_id);
CREATE INDEX idx_audit_request ON audit_logs(request_id);

-- Roles table
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '[]',
    scope_type VARCHAR(50) NOT NULL,
    scope_id VARCHAR(255),
    conditions JSONB DEFAULT '[]',
    is_system_role BOOLEAN NOT NULL DEFAULT FALSE,
    tags JSONB DEFAULT '[]',
    max_session_duration_hours INTEGER DEFAULT 24,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Approval workflows table
CREATE TABLE approval_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    steps JSONB NOT NULL DEFAULT '[]',
    configuration JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Appendix E: CLI Reference

```bash
# Install CLI
curl -fsSL https://phenotype.io/install-governance.sh | sh

# Authenticate
governance auth login --api-key $API_KEY

# Policy commands
governance policy create --file policy.yaml
governance policy get <policy-id>
governance policy list --status Active
governance policy update <policy-id> --file policy.yaml
governance policy activate <policy-id>
governance policy delete <policy-id>

# Evaluation commands
governance evaluate --policy <policy-id> --resource <resource-file>
governance evaluate --policy <policy-id> --stdin < data.json

# Violation commands
governance violation list --severity High,Critical
governance violation get <violation-id>
governance violation resolve <violation-id> --reason "Fixed"

# Audit commands
governance audit query --from 2026-04-01 --to 2026-04-06
governance audit export --format json --output audit.json

# Configuration
governance config set enforcement.mode Enforce
governance config get enforcement.mode
governance config validate --file governance.toml

# Monitoring
governance health check
governance metrics get --format prometheus
governance status
```

### Appendix F: Integration Examples

#### GitHub Actions Integration

```yaml
# .github/workflows/governance-check.yml
name: Governance Check

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  governance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Evaluate Governance Policies
        uses: phenotype/governance-action@v1
        with:
          api-url: https://governance.phenotype.io
          api-key: ${{ secrets.GOVERNANCE_API_KEY }}
          policy-id: security-code-review-policy
          fail-on-violation: true
```

#### Terraform Provider

```hcl
# main.tf
terraform {
  required_providers {
    phenotype_governance = {
      source = "phenotype/governance"
      version = "~> 1.0"
    }
  }
}

provider "phenotype_governance" {
  api_url = "https://governance.phenotype.io"
  api_key = var.governance_api_key
}

resource "phenotype_governance_policy" "security_policy" {
  name        = "security-sensitive-changes"
  description = "Enforces security review requirements"
  version     = "1.0.0"

  scope {
    type = "Global"
  }

  rule {
    name        = "require-security-review"
    rule_type   = "Requirement"
    severity    = "High"

    condition {
      expression = "files.matches('**/security/**')"
      operator   = "Matches"
    }

    action {
      type = "RequireApproval"
      workflow_id = phenotype_governance_approval_workflow.security_review.id
    }
  }
}

resource "phenotype_governance_approval_workflow" "security_review" {
  name        = "security-review-workflow"
  description = "Security team review workflow"

  step {
    number        = 1
    name          = "security-team-review"
    approver_type = "Team"
    approvers     = ["security"]
    timeout_hours = 48
  }
}
```

### Appendix G: Migration Guide

#### From Legacy Systems

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MIGRATION WORKFLOW                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Phase 1: Discovery (Week 1)                                                │
│  ─────────────────────────                                                  │
│  • Export existing policies from legacy system                              │
│  • Map legacy policy constructs to phenotype format                        │
│  • Identify custom rules and logic                                          │
│  • Document integration points                                              │
│                                                                             │
│  Phase 2: Translation (Week 2)                                            │
│  ────────────────────────────                                               │
│  • Convert policy definitions using migration tool                         │
│  • Validate rule syntax                                                     │
│  • Test evaluation logic                                                    │
│  • Create approval workflows                                                │
│                                                                             │
│  Phase 3: Parallel Run (Week 3-4)                                          │
│  ──────────────────────────────                                             │
│  • Deploy phenotype governance in AuditOnly mode                          │
│  • Run both systems in parallel                                             │
│  • Compare results and tune policies                                        │
│  • Train teams on new system                                                │
│                                                                             │
│  Phase 4: Cutover (Week 5)                                                  │
│  ─────────────────────────                                                  │
│  • Switch enforcement mode to Enforce                                       │
│  • Decommission legacy system                                               │
│  • Monitor and support                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Appendix H: Troubleshooting Guide

| Symptom | Possible Cause | Solution |
|---------|---------------|----------|
| High evaluation latency | Complex rule chains | Simplify rules, add caching |
| Cache misses | Short TTL or high churn | Increase TTL, optimize cache keys |
| DB connection errors | Pool exhaustion | Increase pool size, check for leaks |
| Audit log delays | High write volume | Enable batching, scale consumers |
| Policy not triggering | Wrong scope or condition | Verify scope, test condition |
| Notification failures | Invalid webhook URL | Check URL, test connectivity |
| Memory growth | Large audit buffers | Reduce batch size, flush more often |

### Appendix I: Compliance Mapping

| Compliance Standard | phenotype-governance Feature | Evidence |
|--------------------|------------------------------|----------|
| SOC 2 Type II | Audit logging, access controls | Audit logs, RBAC config |
| ISO 27001 | Policy enforcement, risk assessment | Policy definitions, violation reports |
| GDPR | Data protection policies | Privacy-related rules |
| HIPAA | PHI access controls | Healthcare-specific policies |
| PCI-DSS | Cardholder data protection | Security policies |
| FedRAMP | Continuous monitoring | Audit trail, metrics |

### Appendix J: Performance Tuning

```toml
# high-performance-config.toml
# Optimized for high-throughput scenarios

[server]
workers = 16
request_timeout_seconds = 60
max_request_size_mb = 50

[database]
pool_size = 50
connection_timeout_seconds = 10
idle_timeout_seconds = 600
max_lifetime_seconds = 1800

[cache]
ttl_seconds = 600
eviction_policy = "allkeys-lfu"
max_memory_mb = 2048

[evaluation]
max_rule_chain_depth = 20
evaluation_timeout_ms = 10000
enable_parallel_evaluation = true
max_parallel_rules = 10

[audit]
batch_size = 5000
flush_interval_seconds = 30
async_writes = true
compression_enabled = true

[notifications]
batch_notifications = true
batch_interval_seconds = 60
max_batch_size = 100
```

### Appendix K: API Versioning

| Version | Status | End of Support | Breaking Changes |
|---------|--------|----------------|------------------|
| v1.0 | Active | 2027-01-01 | Initial release |
| v1.1 | Preview | - | Added batch operations |
| v2.0 | Planned | - | WebSocket streaming, GraphQL |

### Appendix L: SDK Examples

#### Python SDK

```python
from phenotype_governance import GovernanceClient

# Initialize client
client = GovernanceClient(
    api_url="https://governance.phenotype.io",
    api_key="your-api-key"
)

# Create a policy
policy = client.policies.create({
    "name": "security-review-policy",
    "description": "Require security review",
    "version": "1.0.0",
    "rules": [
        {
            "name": "require-review",
            "rule_type": "Requirement",
            "condition": {
                "expression": "files.matches('**/security/**')",
                "operator": "Matches"
            },
            "action": {"type": "RequireApproval"},
            "severity": "High"
        }
    ]
})

# Evaluate a resource
result = client.evaluate(
    policy_id=policy.id,
    context={
        "resource_type": "pull_request",
        "resource_id": "pr-123",
        "environment": {"repository": "my-repo"}
    },
    resource_data={"files": [{"path": "src/security/auth.rs"}]}
)

# List violations
violations = client.violations.list(
    severity=["High", "Critical"],
    status="Open"
)

for violation in violations:
    print(f"{violation.id}: {violation.title}")
```

#### TypeScript/JavaScript SDK

```typescript
import { GovernanceClient } from '@phenotype/governance';

const client = new GovernanceClient({
  apiUrl: 'https://governance.phenotype.io',
  apiKey: process.env.GOVERNANCE_API_KEY!
});

// Subscribe to real-time events
const subscription = client.events.subscribe({
  channels: ['violations', 'policy_changes'],
  filters: { severity: ['Critical', 'High'] }
});

subscription.on('violation_detected', (event) => {
  console.log('New violation:', event.payload);
  // Send notification, update dashboard, etc.
});

// Evaluate policy
async function checkCompliance(resource: Resource) {
  const result = await client.evaluate({
    policyId: 'security-policy',
    context: {
      resourceType: resource.type,
      resourceId: resource.id,
      environment: { repository: resource.repo }
    },
    resourceData: resource.toJSON()
  });

  if (result.outcome === 'NonCompliant') {
    console.warn('Compliance issues:', result.violations);
    return false;
  }

  return true;
}
```

---

## Document Information

| Field | Value |
|-------|-------|
| **Document ID** | SPEC-GOVERNANCE-001 |
| **Version** | 1.0.0 |
| **Status** | Active |
| **Author** | Phenotype Engineering |
| **Last Updated** | 2026-04-06 |
| **Review Cycle** | Quarterly |
| **Next Review** | 2026-07-06 |

---

*This specification is the canonical definition of phenotype-governance system behavior. All implementations must conform to this specification.*
