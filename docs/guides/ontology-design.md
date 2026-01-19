# Ontology Design Guide

This guide covers designing data models (ontologies) in Open Forge using LinkML.

## Table of Contents

- [Introduction to Ontologies](#introduction-to-ontologies)
- [LinkML Overview](#linkml-overview)
- [Creating Your First Ontology](#creating-your-first-ontology)
- [Advanced Features](#advanced-features)
- [Code Generation](#code-generation)
- [Ontology Evolution](#ontology-evolution)
- [Best Practices](#best-practices)

---

## Introduction to Ontologies

In Open Forge, an **ontology** is a formal definition of your data model that describes:

- **Entities**: The core objects in your domain (Customer, Order, Product)
- **Attributes**: Properties of entities (name, price, quantity)
- **Relationships**: How entities connect (Customer places Orders)
- **Constraints**: Rules and validations (price must be positive)

### Why Use Ontologies?

| Benefit | Description |
|---------|-------------|
| **Single Source of Truth** | One schema generates all artifacts |
| **Multi-Target Generation** | SQL, GraphQL, Pydantic, TypeScript from one definition |
| **Validation** | Built-in data validation rules |
| **Documentation** | Self-documenting data model |
| **Evolution** | Version and migrate schemas safely |

```
                    ┌─────────────────┐
                    │  LinkML Schema  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐         ┌─────────┐         ┌─────────┐
   │   SQL   │         │ GraphQL │         │ Pydantic│
   └─────────┘         └─────────┘         └─────────┘
        │                    │                    │
        ▼                    ▼                    ▼
   PostgreSQL            API Schema           Python Models
   Apache AGE
```

---

## LinkML Overview

[LinkML](https://linkml.io) is a modeling language for linked data that Open Forge uses for ontology definitions.

### Basic Structure

```yaml
id: https://example.org/my-ontology
name: my_ontology
title: My Domain Ontology
description: Describes the core entities in my domain

prefixes:
  linkml: https://w3id.org/linkml/
  schema: http://schema.org/

default_range: string

classes:
  Entity:
    attributes:
      field_name:
        range: string
        required: true

enums:
  StatusEnum:
    permissible_values:
      active:
      inactive:
```

### Core Concepts

| Concept | Description | Example |
|---------|-------------|---------|
| **Class** | Entity definition | `Customer`, `Order` |
| **Attribute** | Property of a class | `name`, `email` |
| **Range** | Data type or reference | `string`, `integer`, `Customer` |
| **Enum** | Fixed set of values | `OrderStatus` |
| **Slot** | Reusable attribute | `created_at`, `updated_at` |

---

## Creating Your First Ontology

### Step 1: Define the Domain

Start by identifying core entities:

```yaml
id: https://example.org/ecommerce
name: ecommerce_ontology
title: E-Commerce Domain Ontology
description: Data model for e-commerce platform

prefixes:
  linkml: https://w3id.org/linkml/
  ecom: https://example.org/ecommerce/

default_range: string
```

### Step 2: Create Classes

Define your main entities:

```yaml
classes:
  Customer:
    description: A customer who can place orders
    attributes:
      customer_id:
        identifier: true
        range: string
        description: Unique customer identifier
      email:
        range: string
        required: true
        pattern: "^[\\w.-]+@[\\w.-]+\\.\\w+$"
      first_name:
        range: string
        required: true
      last_name:
        range: string
        required: true
      created_at:
        range: datetime
      status:
        range: CustomerStatus

  Product:
    description: A product available for purchase
    attributes:
      product_id:
        identifier: true
        range: string
      name:
        range: string
        required: true
      description:
        range: string
      price:
        range: decimal
        required: true
        minimum_value: 0
      category:
        range: Category
      in_stock:
        range: boolean
        ifabsent: "true"

  Order:
    description: A customer order
    attributes:
      order_id:
        identifier: true
        range: string
      customer:
        range: Customer
        required: true
        description: The customer who placed the order
      order_date:
        range: datetime
        required: true
      status:
        range: OrderStatus
      total_amount:
        range: decimal
      line_items:
        range: OrderLineItem
        multivalued: true
        inlined_as_list: true
```

### Step 3: Define Relationships

Add related entities:

```yaml
  OrderLineItem:
    description: A line item within an order
    attributes:
      line_item_id:
        identifier: true
        range: string
      order:
        range: Order
        required: true
      product:
        range: Product
        required: true
      quantity:
        range: integer
        required: true
        minimum_value: 1
      unit_price:
        range: decimal
        required: true

  Category:
    description: Product category
    attributes:
      category_id:
        identifier: true
        range: string
      name:
        range: string
        required: true
      parent_category:
        range: Category
        description: Parent category for hierarchical organization
```

### Step 4: Add Enumerations

Define allowed values:

```yaml
enums:
  CustomerStatus:
    description: Customer account status
    permissible_values:
      active:
        description: Active customer
      inactive:
        description: Inactive customer
      suspended:
        description: Suspended account

  OrderStatus:
    description: Order fulfillment status
    permissible_values:
      pending:
        description: Order placed, awaiting processing
      processing:
        description: Order being processed
      shipped:
        description: Order shipped to customer
      delivered:
        description: Order delivered
      cancelled:
        description: Order cancelled
```

### Step 5: Add Common Slots

Define reusable attributes:

```yaml
slots:
  created_at:
    range: datetime
    description: Timestamp when the record was created

  updated_at:
    range: datetime
    description: Timestamp when the record was last updated

  is_deleted:
    range: boolean
    description: Soft delete flag
    ifabsent: "false"
```

### Complete Example

```yaml
id: https://example.org/ecommerce
name: ecommerce_ontology
title: E-Commerce Domain Ontology
description: Data model for e-commerce platform
version: 1.0.0

prefixes:
  linkml: https://w3id.org/linkml/
  ecom: https://example.org/ecommerce/

default_range: string

types:
  decimal:
    uri: xsd:decimal
    base: float

slots:
  created_at:
    range: datetime
  updated_at:
    range: datetime
  is_deleted:
    range: boolean
    ifabsent: "false"

classes:
  Customer:
    slots:
      - created_at
      - updated_at
    attributes:
      customer_id:
        identifier: true
        range: string
      email:
        range: string
        required: true
      first_name:
        range: string
        required: true
      last_name:
        range: string
        required: true
      status:
        range: CustomerStatus

  Product:
    slots:
      - created_at
      - updated_at
    attributes:
      product_id:
        identifier: true
        range: string
      name:
        range: string
        required: true
      price:
        range: decimal
        minimum_value: 0
      category:
        range: Category

  Order:
    slots:
      - created_at
      - updated_at
    attributes:
      order_id:
        identifier: true
        range: string
      customer:
        range: Customer
        required: true
      status:
        range: OrderStatus
      line_items:
        range: OrderLineItem
        multivalued: true

  OrderLineItem:
    attributes:
      product:
        range: Product
        required: true
      quantity:
        range: integer
        minimum_value: 1
      unit_price:
        range: decimal

  Category:
    attributes:
      category_id:
        identifier: true
      name:
        range: string
        required: true
      parent_category:
        range: Category

enums:
  CustomerStatus:
    permissible_values:
      active:
      inactive:
      suspended:

  OrderStatus:
    permissible_values:
      pending:
      processing:
      shipped:
      delivered:
      cancelled:
```

---

## Advanced Features

### Inheritance

Classes can inherit from other classes:

```yaml
classes:
  NamedEntity:
    abstract: true
    attributes:
      name:
        range: string
        required: true
      description:
        range: string

  Product:
    is_a: NamedEntity
    attributes:
      product_id:
        identifier: true
      price:
        range: decimal

  Category:
    is_a: NamedEntity
    attributes:
      category_id:
        identifier: true
```

### Mixins

Share attributes across unrelated classes:

```yaml
classes:
  Auditable:
    mixin: true
    attributes:
      created_by:
        range: string
      created_at:
        range: datetime
      updated_by:
        range: string
      updated_at:
        range: datetime

  Order:
    mixins:
      - Auditable
    attributes:
      order_id:
        identifier: true
```

### Rules and Constraints

Add validation rules:

```yaml
classes:
  Order:
    attributes:
      order_date:
        range: datetime
      ship_date:
        range: datetime
    rules:
      - preconditions:
          slot_conditions:
            ship_date:
              value_presence: PRESENT
        postconditions:
          slot_conditions:
            ship_date:
              minimum_value: order_date
        description: Ship date must be after order date
```

### Pattern Validation

Validate string formats:

```yaml
attributes:
  email:
    range: string
    pattern: "^[\\w.-]+@[\\w.-]+\\.\\w+$"

  phone:
    range: string
    pattern: "^\\+?[1-9]\\d{1,14}$"

  postal_code:
    range: string
    pattern: "^\\d{5}(-\\d{4})?$"
```

### Annotations

Add metadata for code generation:

```yaml
classes:
  Customer:
    annotations:
      table_name: customers
      index_fields: email, last_name
    attributes:
      customer_id:
        annotations:
          column_name: id
          primary_key: true
```

---

## Code Generation

Open Forge compiles LinkML schemas into multiple formats.

### Using the Compiler

```python
from ontology.compiler import OntologyCompiler, OutputFormat

compiler = OntologyCompiler()

# Compile schema
result = compiler.compile(
    "path/to/schema.yaml",
    formats=[OutputFormat.ALL]
)

# Check for errors
if result.has_errors():
    for error in result.errors:
        print(f"Error: {error}")
else:
    # Access generated code
    sql = result.get_output(OutputFormat.SQL)
    graphql = result.get_output(OutputFormat.GRAPHQL)
    pydantic = result.get_output(OutputFormat.PYDANTIC)
    typescript = result.get_output(OutputFormat.TYPESCRIPT)
```

### Generated SQL

```sql
-- Generated from ecommerce_ontology v1.0.0

CREATE SCHEMA IF NOT EXISTS ontology;

CREATE TABLE ontology.customer (
    customer_id VARCHAR PRIMARY KEY,
    email VARCHAR NOT NULL,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    status VARCHAR CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE ontology.product (
    product_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    price DECIMAL CHECK (price >= 0),
    category_id VARCHAR REFERENCES ontology.category(category_id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- ... more tables
```

### Generated Pydantic

```python
# Generated from ecommerce_ontology v1.0.0

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum

class CustomerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class Customer(BaseModel):
    customer_id: str = Field(..., description="Unique customer identifier")
    email: str = Field(...)
    first_name: str = Field(...)
    last_name: str = Field(...)
    status: Optional[CustomerStatus] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        import re
        if not re.match(r'^[\w.-]+@[\w.-]+\.\w+$', v):
            raise ValueError('Invalid email format')
        return v
```

### Generated GraphQL

```graphql
# Generated from ecommerce_ontology v1.0.0

enum CustomerStatus {
  ACTIVE
  INACTIVE
  SUSPENDED
}

type Customer {
  customerId: ID!
  email: String!
  firstName: String!
  lastName: String!
  status: CustomerStatus
  createdAt: DateTime
  updatedAt: DateTime
  orders: [Order!]!
}

type Query {
  customer(id: ID!): Customer
  customers(
    first: Int
    after: String
    filter: CustomerFilter
  ): CustomerConnection!
}

type Mutation {
  createCustomer(input: CreateCustomerInput!): Customer!
  updateCustomer(id: ID!, input: UpdateCustomerInput!): Customer!
  deleteCustomer(id: ID!): Boolean!
}
```

---

## Ontology Evolution

### Versioning

Update version when making changes:

```yaml
id: https://example.org/ecommerce
name: ecommerce_ontology
version: 1.1.0  # Incremented from 1.0.0
```

### Migration Generation

Generate SQL migrations between versions:

```python
from ontology.compiler import OntologyCompiler

compiler = OntologyCompiler()

migration = compiler.generate_migration(
    from_schema="schema_v1.0.0.yaml",
    to_schema="schema_v1.1.0.yaml"
)

print(migration)
```

Output:
```sql
-- Migration from v1.0.0 to v1.1.0

-- Add new column
ALTER TABLE ontology.customer
ADD COLUMN phone VARCHAR;

-- Add new enum value
ALTER TYPE ontology.customer_status
ADD VALUE 'pending_verification';

-- Create new table
CREATE TABLE ontology.customer_address (
    address_id VARCHAR PRIMARY KEY,
    customer_id VARCHAR REFERENCES ontology.customer(customer_id),
    street VARCHAR NOT NULL,
    city VARCHAR NOT NULL,
    country VARCHAR NOT NULL
);
```

### Breaking vs Non-Breaking Changes

| Change Type | Breaking | Example |
|-------------|----------|---------|
| Add optional field | No | Add `phone` to Customer |
| Add required field | Yes | Add required `tax_id` |
| Remove field | Yes | Remove `legacy_id` |
| Rename field | Yes | Rename `name` to `full_name` |
| Change type | Maybe | `string` to `integer` (breaking) |
| Add enum value | No | Add `pending` to Status |
| Remove enum value | Yes | Remove `deprecated` status |

---

## Best Practices

### 1. Use Descriptive Names

```yaml
# Good
classes:
  CustomerShippingAddress:
    description: Physical address for shipping orders to customers

# Bad
classes:
  CustAddr:
```

### 2. Document Everything

```yaml
classes:
  Order:
    description: |
      Represents a customer order in the system.

      Orders progress through the following states:
      pending -> processing -> shipped -> delivered

      Orders can be cancelled at any point before shipping.
    attributes:
      order_id:
        description: Unique order identifier (UUID format)
```

### 3. Use Appropriate Types

```yaml
attributes:
  # Use decimal for money
  price:
    range: decimal

  # Use integer for counts
  quantity:
    range: integer

  # Use datetime for timestamps
  created_at:
    range: datetime

  # Use boolean for flags
  is_active:
    range: boolean
```

### 4. Define Clear Relationships

```yaml
classes:
  Order:
    attributes:
      customer:
        range: Customer
        required: true
        description: The customer who placed this order (required)

      shipping_address:
        range: Address
        description: Optional shipping address (uses customer default if not set)
```

### 5. Use Enums for Constrained Values

```yaml
# Good: Use enum for known values
attributes:
  status:
    range: OrderStatus

enums:
  OrderStatus:
    permissible_values:
      pending:
      processing:
      shipped:

# Bad: Use free-form string
attributes:
  status:
    range: string
```

### 6. Plan for Evolution

```yaml
# Reserve space for future fields
classes:
  Customer:
    attributes:
      # Core fields
      customer_id:
        identifier: true
      email:
        required: true

      # Extension point
      metadata:
        range: string
        description: JSON blob for extensible attributes
```

---

## Related Documentation

- [Getting Started](./getting-started.md)
- [Engagement Workflow](./engagement-workflow.md)
- [Pipeline Creation](./pipeline-creation.md)
- [Architecture Overview](../development/architecture.md)
