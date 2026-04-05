//! Behavior-Driven Development (BDD) testing utilities for Phenotype
//!
//! Provides types and traits for writing Given-When-Then style tests.

/// Step types in BDD scenarios
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StepType {
    /// Setup/precondition step
    Given,
    /// Action step
    When,
    /// Assertion step
    Then,
}