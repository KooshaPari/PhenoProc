# phenotype-core-wasm

WASM bindings for `phenotype-core` for TypeScript/JavaScript.

## Building

```bash
# Install wasm-pack
curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh

# Build for bundler (webpack, rollup, etc.)
wasm-pack build --target bundler --out-dir pkg

# Build for Node.js
wasm-pack build --target nodejs --out-dir pkg-node

# Build for web (no bundler)
wasm-pack build --target web --out-dir pkg-web
```

## Usage (TypeScript)

```typescript
import { WasmEntityId, WasmConfig, validateEntity } from '@phenotype/core-wasm';

// Create an EntityId
const entity = new WasmEntityId("123", "user");
console.log(entity.id); // "123"
console.log(entity.namespace); // "user"

// Serialize to JSON
const json = entity.toJSON(); // '{"id":"123","namespace":"user"}'

// Deserialize
const parsed = WasmEntityId.fromJSON(json);

// Validate
const isValid = validateEntity("123", "user"); // true
```

## Usage (JavaScript)

```javascript
import init, { WasmEntityId, validateEntity } from '@phenotype/core-wasm';

async function run() {
  await init();
  
  const entity = new WasmEntityId("123", "user");
  const isValid = validateEntity("123", "user");
  console.log(isValid); // true
}

run();
```

## Publishing to npm

```bash
wasm-pack build --target bundler --out-dir pkg
cd pkg
npm publish --access public
```
