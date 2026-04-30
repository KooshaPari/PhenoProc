# Pheno Storage Module

## Overview

The pheno storage module provides a flexible, pluggable repository system for data persistence with support for multiple backends.

## Quick Start

```python
import asyncio
from pheno.storage.repository import create_repository

async def main():
    # Create a repository (in-memory for testing)
    repo = create_repository("memory", entity_type="users")

    # Create
    await repo.create("user-1", {"name": "Alice", "age": 30})

    # Read
    user = await repo.read("user-1")
    print(user)  # {"name": "Alice", "age": 30}

    # Update
    await repo.update("user-1", {"name": "Alice", "age": 31})

    # Delete
    await repo.delete("user-1")

    await repo.close()

asyncio.run(main())
```

## Backends

### In-Memory Backend (Always Available)

Fast in-memory storage for testing and development:

```python
from pheno.storage.repository import InMemoryBackend

backend = InMemoryBackend(entity_type="test")
```

### SQLAlchemy Backend

Supports any SQL database (PostgreSQL, MySQL, SQLite, etc.):

```python
from pheno.storage.repository import SQLAlchemyBackend

# PostgreSQL
backend = SQLAlchemyBackend(
    database_url="postgresql+asyncpg://user:pass@localhost/db",
    entity_type="users",
    pool_size=10,
    max_overflow=20
)

# SQLite
backend = SQLAlchemyBackend(
    database_url="sqlite+aiosqlite:///./database.db",
    entity_type="users"
)
```

**Requirements**:
- `pip install 'sqlalchemy>=2.0.0'`
- Database driver (e.g., `aiosqlite`, `asyncpg`, `aiomysql`)

### MongoDB Backend (Coming Soon)

```python
from pheno.storage.repository import MongoDBBackend

# Will support MongoDB with Motor
backend = MongoDBBackend(
    connection_string="mongodb://localhost:27017",
    database="mydb",
    collection="users"
)
```

### Redis Backend (Coming Soon)

```python
from pheno.storage.repository import RedisBackend

# Will support Redis with aioredis
backend = RedisBackend(
    redis_url="redis://localhost:6379",
    key_prefix="app"
)
```

## Features

### CRUD Operations

```python
# Create
await repo.create("id-123", {"key": "value"})

# Read
data = await repo.read("id-123")

# Update
await repo.update("id-123", {"key": "new_value"})

# Delete
await repo.delete("id-123")

# Check existence
exists = await repo.exists("id-123")
```

### Query and Filtering

```python
# Query all
results = await repo.query(limit=100, offset=0)

# Query with filters
results = await repo.query(
    filters={"status": "active"},
    limit=50,
    order_by="-created_at"
)

# Count
total = await repo.count()
active = await repo.count(filters={"status": "active"})
```

### Transactions

```python
async with repo.transaction():
    await repo.create("id-1", {"data": "value1"})
    await repo.create("id-2", {"data": "value2"})
    # Both operations committed together

# Automatic rollback on error
try:
    async with repo.transaction():
        await repo.create("id-3", {"data": "value3"})
        raise ValueError("Error!")
except ValueError:
    pass
# id-3 will not be created (rolled back)
```

## Examples

See `/Users/kooshapari/temp-PRODVERCEL/485/kush/pheno-sdk/examples/repository_usage.py` for comprehensive examples.

## Documentation

See `/Users/kooshapari/temp-PRODVERCEL/485/kush/pheno-sdk/docs/repository-backend-implementation.md` for detailed documentation.

## Testing

```bash
# Run basic tests (no dependencies)
PYTHONPATH=src python tests/storage/test_basic.py

# Run full test suite (requires SQLAlchemy)
pip install 'sqlalchemy>=2.0.0' 'aiosqlite>=0.19.0'
pytest tests/storage/test_repository.py -v
```

## Error Handling

```python
from pheno.storage.repository import (
    EntityNotFoundError,
    RepositoryError,
    ConnectionError,
    TransactionError
)

try:
    await repo.update("nonexistent", {"data": "value"})
except EntityNotFoundError:
    print("Entity not found")
except RepositoryError as e:
    print(f"Repository error: {e}")
```

## API Reference

### RepositoryBackend (Abstract Base Class)

All backends implement this interface:

- `create(entity_id, data)`: Create a new entity
- `read(entity_id)`: Read an entity by ID
- `update(entity_id, data)`: Update an existing entity
- `delete(entity_id)`: Delete an entity
- `query(filters, limit, offset, order_by)`: Query entities
- `count(filters)`: Count entities
- `exists(entity_id)`: Check if entity exists
- `transaction()`: Start a transaction context
- `close()`: Close backend and cleanup

### create_repository(backend_type, entity_type, **kwargs)

Factory function to create repositories:

```python
repo = create_repository(
    backend_type='sqlalchemy',  # or 'memory', 'mongodb', 'redis'
    entity_type='users',
    database_url='...',
    # Additional backend-specific options
)
```

## License

Proprietary - ATOMS-PHENO Team
