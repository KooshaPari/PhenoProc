# phenotype-test-fixtures

Test fixtures and builders for the phenotype workspace.

Provides factory functions and builders for creating test data, mock objects, and common test scenarios.

## Usage

```rust
use phenotype_test_fixtures::{TestData, TestDataBuilder};

let data = TestDataBuilder::new()
    .name("test".to_string())
    .value(42)
    .build();
```
