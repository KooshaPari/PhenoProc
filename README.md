# phenotype-core-py

Python FFI bindings for `phenotype-core` via PyO3.

## Installation

```bash
pip install maturin
maturin develop  # Development install
maturin build --release  # Production build
```

## Usage

```python
from phenotype_core_py import EntityId, Config, validate_entity

# Create an EntityId
entity = EntityId(id="123", namespace="user")
print(entity.to_json())  # '{"id":"123","namespace":"user"}'

# Validate
is_valid = validate_entity(entity)  # True
```

## Building

```bash
cd PhenoKit/rust/phenotype-core-py
maturin develop --release
```
