//! Hierarchical State Machine implementation for the phenotype ecosystem.
//!
//! Provides a flexible, type-safe state machine with support for hierarchical states,
//! history tracking, and async event handling.
//!
//! # Example
//!
//! ```rust
//! use phenotype_state_machine::{State, StateMachine, Handler, HandlerResult};
//! use std::fmt;
//!
//! #[derive(Debug, Clone)]
//! enum MyState {
//!     Idle,
//!     Running,
//!     Stopped,
//! }
//!
//! impl State for MyState {
//!     type Id = String;
//!
//!     fn id(&self) -> Self::Id {
//!         match self {
//!             MyState::Idle => "idle".to_string(),
//!             MyState::Running => "running".to_string(),
//!             MyState::Stopped => "stopped".to_string(),
//!         }
//!     }
//!
//!     fn validate_transition(&self, to: &Self) -> Result<(), String> {
//!         match (self, to) {
//!             (MyState::Idle, MyState::Running) => Ok(()),
//!             (MyState::Running, MyState::Stopped) => Ok(()),
//!             (MyState::Stopped, MyState::Idle) => Ok(()),
//!             _ => Err("Invalid transition".to_string()),
//!         }
//!     }
//!
//!     fn on_enter(&self) {
//!         println!("Entering state: {:?}", self);
//!     }
//!
//!     fn on_exit(&self) {
//!         println!("Exiting state: {:?}", self);
//!     }
//! }
//! ```

use std::collections::HashMap;
use std::fmt::Debug;
use std::hash::Hash;

pub mod models;

pub use models::*;

/// Core trait for state machine states
pub trait State: Debug + Clone + Send + Sync + 'static {
    /// State identifier type
    type Id: Debug + Clone + Eq + Hash + Send + Sync;

    /// Get the state identifier
    fn id(&self) -> Self::Id;

    /// Validate transition from this state to another
    fn validate_transition(&self, to: &Self) -> Result<(), String>;

    /// Called when entering this state
    fn on_enter(&self);

    /// Called when exiting this state
    fn on_exit(&self);
}

/// Handler trait for processing events and triggering state transitions
pub trait Handler: Debug + Send + Sync + 'static {
    /// The state type this handler works with
    type State: State;

    /// Handle an event and return the resulting handler result
    fn handle(&self, state: &Self::State, event: Event) -> HandlerResult<Self::State>;
}

/// Event type for state machine interactions
#[derive(Debug, Clone)]
pub struct Event {
    /// Event type identifier
    pub event_type: String,
    /// Event payload data
    pub payload: Option<serde_json::Value>,
}

/// Result type for handler operations
#[derive(Debug)]
pub enum HandlerResult<S: State> {
    /// Stay in current state
    Stay,
    /// Transition to new state
    Transition(S),
    /// Exit the state machine
    Exit,
}

/// Hierarchical state machine supporting nested states and history
#[derive(Debug)]
pub struct HierarchicalStateMachine<S: State> {
    current: S,
    parent: Option<Box<Self>>,
    children: HashMap<S::Id, Box<Self>>,
    handler: Option<Box<dyn Handler<State = S>>>,
    history: Vec<S>,
}

impl<S: State + Default> Default for HierarchicalStateMachine<S> {
    fn default() -> Self {
        Self {
            current: S::default(),
            parent: None,
            children: HashMap::new(),
            handler: None,
            history: Vec::new(),
        }
    }
}

impl<S: State> HierarchicalStateMachine<S> {
    /// Create new hierarchical state machine
    pub fn new(initial: S) -> Self {
        HierarchicalStateMachine {
            current: initial,
            parent: None,
            children: HashMap::new(),
            handler: None,
            history: Vec::new(),
        }
    }

    /// Add child state machine
    pub fn add_child(&mut self, id: S::Id, child: Self) {
        self.children.insert(id, Box::new(child));
    }

    /// Get parent reference
    pub fn parent(&self) -> Option<&Self> {
        self.parent.as_ref().map(|b| b.as_ref())
    }

    /// Get mutable parent reference
    pub fn parent_mut(&mut self) -> Option<&mut Self> {
        self.parent.as_mut().map(|b| b.as_mut())
    }

    /// Get current state
    pub fn current(&self) -> &S {
        &self.current
    }

    /// Get handler reference
    pub fn handler(&self) -> Option<&dyn Handler<State = S>> {
        self.handler.as_ref().map(|b| b.as_ref())
    }

    /// Transition to new state
    pub fn transition(&mut self, new_state: S) -> Result<(), String> {
        self.current.validate_transition(&new_state)?;
        self.current.on_exit();
        self.history.push(self.current.clone());
        new_state.on_enter();
        self.current = new_state;
        Ok(())
    }

    /// Process an event
    pub fn process(&mut self, event: Event) -> HandlerResult<S> {
        if let Some(handler) = &self.handler {
            handler.handle(&self.current, event)
        } else {
            HandlerResult::Stay
        }
    }

    /// Get history
    pub fn history(&self) -> &[S] {
        &self.history
    }

    /// Reset to initial state
    pub fn reset(&mut self, initial: S) {
        self.current = initial;
        self.history.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Debug, Clone, Default)]
    struct TestState {
        value: u32,
    }

    impl State for TestState {
        type Id = String;

        fn state_id(&self) -> Self::Id {
            format!("state_{}", self.value)
        }

        fn validate_transition(&self, _to: &Self) -> Result<(), String> {
            Ok(())
        }

        fn on_enter(&self) {}
        fn on_exit(&self) {}
    }

    #[test]
    fn test_hierarchical_state_machine() {
        let sm = HierarchicalStateMachine::new(TestState { value: 0 });
        assert_eq!(sm.current().value, 0);
    }
}
