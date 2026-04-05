use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

/// Python module for phenotype-core FFI bindings
#[pymodule]
fn phenotype_core_py(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyEntityId>()?;
    m.add_class::<PyConfig>()?;
    m.add_function(wrap_pyfunction!(py_validate_entity, m)?)?;
    Ok(())
}

/// EntityId wrapper for Python
#[pyclass(name = "EntityId")]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PyEntityId {
    #[pyo3(get, set)]
    pub id: String,
    #[pyo3(get, set)]
    pub namespace: String,
}

#[pymethods]
impl PyEntityId {
    #[new]
    fn new(id: String, namespace: String) -> Self {
        Self { id, namespace }
    }

    fn __repr__(&self) -> String {
        format!("EntityId(id='{}', namespace='{}')", self.id, self.namespace)
    }

    fn to_json(&self) -> PyResult<String> {
        serde_json::to_string(self)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
    }
}

/// Config wrapper for Python
#[pyclass(name = "Config")]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PyConfig {
    #[pyo3(get, set)]
    pub key: String,
    #[pyo3(get, set)]
    pub value: String,
}

#[pymethods]
impl PyConfig {
    #[new]
    fn new(key: String, value: String) -> Self {
        Self { key, value }
    }
}

/// Validate entity function
#[pyfunction]
fn py_validate_entity(entity_id: &PyEntityId) -> PyResult<bool> {
    // Call into Rust core validation logic
    Ok(!entity_id.id.is_empty() && !entity_id.namespace.is_empty())
}
