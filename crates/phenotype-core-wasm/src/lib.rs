use serde::{Deserialize, Serialize};
use wasm_bindgen::prelude::*;

// When the `wee_alloc` feature is enabled, use `wee_alloc` as the global allocator.
#[cfg(feature = "wee_alloc")]
#[global_allocator]
static ALLOC: wee_alloc::WeeAlloc = wee_alloc::WeeAlloc::INIT;

/// Initialize panic hook for better error messages
#[wasm_bindgen(start)]
pub fn start() {
    console_error_panic_hook::set_once();
}

/// EntityId for WASM/TypeScript
#[wasm_bindgen]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WasmEntityId {
    id: String,
    namespace: String,
}

#[wasm_bindgen]
impl WasmEntityId {
    #[wasm_bindgen(constructor)]
    pub fn new(id: String, namespace: String) -> Self {
        Self { id, namespace }
    }

    #[wasm_bindgen(getter)]
    pub fn id(&self) -> String {
        self.id.clone()
    }

    #[wasm_bindgen(getter)]
    pub fn namespace(&self) -> String {
        self.namespace.clone()
    }

    #[wasm_bindgen(js_name = toJSON)]
    pub fn to_json(&self) -> Result<String, JsValue> {
        serde_json::to_string(self).map_err(|e| JsValue::from_str(&e.to_string()))
    }

    #[wasm_bindgen(js_name = fromJSON)]
    pub fn from_json(json: String) -> Result<WasmEntityId, JsValue> {
        serde_json::from_str(&json).map_err(|e| JsValue::from_str(&e.to_string()))
    }

    #[wasm_bindgen(js_name = toObject)]
    pub fn to_object(&self) -> Result<JsValue, JsValue> {
        serde_wasm_bindgen::to_value(self).map_err(|e| JsValue::from_str(&e.to_string()))
    }
}

/// Config for WASM/TypeScript
#[wasm_bindgen]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WasmConfig {
    key: String,
    value: String,
}

#[wasm_bindgen]
impl WasmConfig {
    #[wasm_bindgen(constructor)]
    pub fn new(key: String, value: String) -> Self {
        Self { key, value }
    }

    #[wasm_bindgen(getter)]
    pub fn key(&self) -> String {
        self.key.clone()
    }

    #[wasm_bindgen(getter)]
    pub fn value(&self) -> String {
        self.value.clone()
    }
}

/// Validate entity via WASM
#[wasm_bindgen(js_name = validateEntity)]
pub fn validate_entity(id: String, namespace: String) -> bool {
    !id.is_empty() && !namespace.is_empty()
}

/// Batch validation for multiple entities
#[wasm_bindgen(js_name = validateEntities)]
pub fn validate_entities(entities: JsValue) -> Result<JsValue, JsValue> {
    let entities: Vec<WasmEntityId> =
        serde_wasm_bindgen::from_value(entities).map_err(|e| JsValue::from_str(&e.to_string()))?;

    let results: Vec<bool> = entities
        .iter()
        .map(|e| validate_entity(e.id.clone(), e.namespace.clone()))
        .collect();

    serde_wasm_bindgen::to_value(&results).map_err(|e| JsValue::from_str(&e.to_string()))
}
