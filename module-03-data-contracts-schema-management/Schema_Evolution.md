# Schema Evolution in Apache Kafka

## Overview

Schema Evolution is the process of changing the structure of schemas over time without breaking existing producers or consumers. This module explores how to safely evolve data schemas in production systems using Apache Avro and Confluent Schema Registry, ensuring system reliability while enabling continuous development.

## Learning Objectives

By the end of this module, you will understand:
- The critical importance of schema evolution in production systems
- How Schema Registry prevents schema drift through version management
- Different compatibility modes and their use cases
- Safe vs. breaking schema changes
- Practical strategies for implementing schema evolution
- Testing and validation approaches for schema changes
- Real-world scenarios and best practices

## What is Schema Evolution?

**Schema Evolution is the process of changing the structure of schemas over time without breaking existing producers or consumers.** This capability is essential for maintaining long-running, production data systems that must adapt to changing business requirements.

### The Evolution Challenge

```python
# Day 1: Simple user schema
user_v1 = {
    "type": "record",
    "name": "User",
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "name", "type": "string"}
    ]
}

# Day 30: Business needs email field
user_v2 = {
    "type": "record", 
    "name": "User",
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "name", "type": "string"},
        {"name": "email", "type": "string"}  # New required field
    ]
}

# Problem: Old data doesn't have email field
# Existing consumers crash when they encounter old data
# New consumers can't read old data
```

### Why Schema Evolution Matters

**In production, data formats constantly change** due to:
- **New Features**: Additional fields for enhanced functionality
- **Business Requirements**: Changing data models to support new use cases
- **Compliance Needs**: Adding fields for regulatory requirements
- **Performance Optimizations**: Restructuring data for better efficiency
- **Bug Fixes**: Correcting field types or structures
- **Integration Requirements**: Adapting to external system changes


## Schema Registry

**Schema Registry prevents schema drift by storing multiple versions of the same schema and enforcing compatibility rules.** It acts as a central authority for schema management and evolution.

### Schema Registry Workflow

**When a new version of a schema is registered:**

1. **Comparison**: The Schema Registry compares it to the previous version
2. **Compatibility Check**: If it violates the compatibility mode, registration is rejected
3. **Storage**: Otherwise, it's saved and assigned a new schema ID
4. **Distribution**: The new schema version becomes available to clients

```python
# Example of the registration process
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.error import SchemaRegistryError

client = SchemaRegistryClient({'url': 'http://localhost:8081'})

# Step 1: Try to register new schema
new_schema = """
{
  "type": "record",
  "name": "User", 
  "fields": [
    {"name": "id", "type": "int"},
    {"name": "name", "type": "string"},
    {"name": "email", "type": "string"}
  ]
}
"""

try:
    # Step 2: Schema Registry performs compatibility check
    schema_id = client.register_schema('user-value', new_schema)
    print(f"Schema registered with ID: {schema_id}")
    
except SchemaRegistryError as e:
    # Step 3: Registration rejected due to compatibility violation
    print(f"Schema registration failed: {e}")
    print("Schema is not compatible with existing versions")
```

### Versioning System

Schema Registry maintains a complete version history:

```python
# Schema versions over time
subject = 'user-value'

# Version 1: Initial schema
v1_id = 1001
v1_schema = {"type": "record", "name": "User", "fields": [...]}

# Version 2: Added optional email
v2_id = 1002  
v2_schema = {"type": "record", "name": "User", "fields": [..., email_field]}

# Version 3: Added optional phone
v3_id = 1003
v3_schema = {"type": "record", "name": "User", "fields": [..., phone_field]}

# Consumers can specify which version to use
consumer_config = {
    'schema.registry.url': 'http://localhost:8081',
    'specific.avro.reader': 'true',
    'use.latest.version': 'false',
    'schema.id': v2_id  # Use specific version
}
```

## Compatibility Modes

Schema Registry supports different compatibility modes that define how schemas can evolve. Each mode provides different guarantees about what types of changes are allowed.

### Backward Compatibility

**Ensures that newer readers can update their schema and still consume events written by old writers.**

```python
# Backward Compatibility Example
# Old Writer Schema (v1)
old_writer_schema = {
    "type": "record",
    "name": "User",
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "name", "type": "string"}
    ]
}

# New Reader Schema (v2) - Backward Compatible
new_reader_schema = {
    "type": "record",
    "name": "User", 
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "name", "type": "string"},
        {"name": "email", "type": ["null", "string"], "default": null}  # Optional field
    ]
}

# Result: v2 readers can process v1 data (email will be null)
```

#### Backward Compatible Changes
- **Add optional fields** with default values
- **Remove fields** (readers ignore unknown fields)
- **Widen types** (int → long, float → double)
- **Add union types** (make existing field nullable)

#### Example Implementation
```python
class BackwardCompatibleEvolution:
    def demonstrate_evolution(self):
        # Producer using old schema
        old_producer = AvroProducer('localhost:9092', 'http://localhost:8081')
        old_data = {"id": 123, "name": "Alice"}
        old_producer.send_message('users', old_writer_schema, old_data)
        
        # Consumer using new schema can read old data
        new_consumer = AvroConsumer('localhost:9092', 'http://localhost:8081', 'new-group')
        
        # When consuming old message:
        # {"id": 123, "name": "Alice", "email": null}
        # Email field gets default value
```

### Forward Compatibility

**Ensures newer writers can produce events with an updated schema that can still be read by older readers.**

```python
# Forward Compatibility Example
# Old Reader Schema (v1) 
old_reader_schema = {
    "type": "record",
    "name": "User",
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "name", "type": "string"},
        {"name": "email", "type": ["null", "string"], "default": null}  # Optional field exists
    ]
}

# New Writer Schema (v2) - Forward Compatible
new_writer_schema = {
    "type": "record",
    "name": "User",
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "name", "type": "string"}
        # email field removed from writer schema
    ]
}

# Result: v1 readers can process v2 data (email uses default value)
```

#### Forward Compatible Changes
- **Remove optional fields**
- **Add fields** that existed in previous schema versions
- **Narrow types** (long → int, double → float) - with caution
- **Remove union types** (make nullable field required)

#### Example Implementation
```python
class ForwardCompatibleEvolution:
    def demonstrate_evolution(self):
        # Consumer using old schema
        old_consumer = AvroConsumer('localhost:9092', 'http://localhost:8081', 'old-group')
        
        # Producer using new schema (removed email field)
        new_producer = AvroProducer('localhost:9092', 'http://localhost:8081') 
        new_data = {"id": 456, "name": "Bob"}  # No email field
        new_producer.send_message('users', new_writer_schema, new_data)
        
        # Old consumer can still read:
        # {"id": 456, "name": "Bob", "email": null}
        # Email gets default value from old schema
```

### Full Compatibility

**Combines both backward and forward compatibility** - the most restrictive but safest mode.

```python
# Full Compatibility Example
# Changes must be both backward AND forward compatible

# Safe Change: Add optional field with default
safe_evolution = {
    "type": "record",
    "name": "User", 
    "fields": [
        {"name": "id", "type": "int"},
        {"name": "name", "type": "string"},
        {"name": "phone", "type": ["null", "string"], "default": null}  # Safe addition
    ]
}

# This works for both:
# - New readers consuming old data (phone = null)
# - Old readers consuming new data (phone field ignored or defaulted)
```

#### Full Compatible Changes
- **Add optional fields** with default values only
- **Use field aliases** for renaming
- **Careful type widening** that works in both directions

### Transitive Compatibility

Extends compatibility checks across all previous versions, not just the immediate predecessor.

```python
# Transitive Backward: v3 must be compatible with v1 AND v2
# Non-transitive: v3 only needs to be compatible with v2

# Example where transitive matters:
v1 = {"fields": [{"name": "id", "type": "int"}]}
v2 = {"fields": [{"name": "id", "type": "int"}, {"name": "email", "type": "string", "default": ""}]}
v3 = {"fields": [{"name": "id", "type": "int"}]}  # Removed email

# Non-transitive: v3 compatible with v2 ✓
# Transitive: v3 NOT compatible with v1 (lost email evolution) ✗
```

### None Compatibility

Disables compatibility checking - allows any schema changes.

```python
# Set compatibility mode
client = SchemaRegistryClient({'url': 'http://localhost:8081'})
client.set_compatibility_level('NONE', subject='experimental-topic-value')

# Any schema change will be accepted
# Use with extreme caution!
```

## Compatibility Mode Configuration

### Global Configuration
```python
from confluent_kafka.schema_registry import SchemaRegistryClient

client = SchemaRegistryClient({'url': 'http://localhost:8081'})

# Set global default compatibility mode
client.set_compatibility_level('BACKWARD')

# Available modes:
# - BACKWARD: New schema can read old data
# - FORWARD: Old schema can read new data  
# - FULL: Both backward and forward compatible
# - BACKWARD_TRANSITIVE: Backward across all versions
# - FORWARD_TRANSITIVE: Forward across all versions
# - FULL_TRANSITIVE: Full across all versions
# - NONE: No compatibility checking
```

### Subject-Specific Configuration
```python
# Different topics can have different compatibility requirements
client.set_compatibility_level('FULL', subject='critical-events-value')
client.set_compatibility_level('BACKWARD', subject='user-events-value') 
client.set_compatibility_level('NONE', subject='experimental-data-value')

# Check current compatibility level
level = client.get_compatibility_level('user-events-value')
print(f"Compatibility level: {level}")
```

## Conclusion

Schema Evolution is a critical capability for maintaining long-running, production data systems. By understanding compatibility modes, implementing proper versioning strategies, and following best practices, you can safely evolve your data schemas while maintaining system reliability and enabling continuous development.

The key to successful schema evolution is planning ahead, testing thoroughly, and implementing gradual rollout strategies that minimize risk while enabling innovation.

## Key Takeaways

- **Schema Evolution** enables safe changes to data structures over time
- **Compatibility modes** define what types of changes are allowed
- **Backward compatibility** ensures new readers can process old data
- **Forward compatibility** ensures old readers can process new data
- **Testing** is crucial for validating schema evolution strategies
- **Gradual rollouts** minimize risk during schema changes
- **Monitoring** helps detect and resolve evolution issues quickly
- **Documentation** ensures teams understand evolution impacts
