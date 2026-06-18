# Order Service — Business Requirements

## Overview

Build a RESTful Order Management Service using Java 21 and Spring Boot 3.
The service manages Products, Customers, and Orders for a simple e-commerce backend.

## Domain Model

### Product
- `id` (Long, auto-generated)
- `name` (String, required, max 100 chars)
- `price` (BigDecimal, required, > 0)
- `stock` (Integer, required, >= 0)

### Customer
- `id` (Long, auto-generated)
- `name` (String, required, max 100 chars)
- `email` (String, required, unique, valid email format)

### Order
- `id` (Long, auto-generated)
- `customerId` (Long, required, must reference existing customer)
- `status` (Enum: PENDING, CONFIRMED, CANCELLED)
- `createdAt` (timestamp, auto-set)
- `items` (list of OrderItem)

### OrderItem
- `productId` (Long, must reference existing product)
- `quantity` (Integer, >= 1)
- `unitPrice` (BigDecimal, snapshot of product price at order time)

## API Requirements

### Products
- `POST /products` — create product
- `GET /products/{id}` — get product by id
- `GET /products` — list all products
- `PUT /products/{id}` — update product (name, price, stock)

### Customers
- `POST /customers` — create customer
- `GET /customers/{id}` — get customer by id

### Orders
- `POST /orders` — create order
  - Validates customer exists
  - Validates each product exists and has sufficient stock
  - Deducts stock for each item
  - Sets unitPrice from current product price
  - Initial status: PENDING
- `GET /orders/{id}` — get order with items
- `GET /orders?customerId={id}` — list orders for a customer
- `PUT /orders/{id}/confirm` — confirm order (PENDING → CONFIRMED)
- `PUT /orders/{id}/cancel` — cancel order (PENDING → CANCELLED), restores stock

## Business Rules
1. Cannot create an order if any product has insufficient stock
2. Only PENDING orders can be confirmed or cancelled
3. Cancelling an order restores the stock of all items
4. Email must be unique across customers
5. Return HTTP 409 for duplicate email, 404 for missing resources, 422 for business rule violations (insufficient stock, invalid status transition)

## Technical Requirements
- Spring Boot 3.x with Spring Web, Spring Data JPA
- H2 in-memory database (no external DB required)
- Maven build tool (use Maven Wrapper `./mvnw`)
- Input validation with Jakarta Bean Validation
- Proper HTTP status codes (200, 201, 404, 409, 422)
- The application must start on port 8080

## Deliverables
1. **Source code** — complete Spring Boot project under `order-service/`
2. **Tests** — at least one integration test per API endpoint using Spring Boot Test (`./mvnw test` must pass)
3. **Dockerfile** — multi-stage build: compile with `eclipse-temurin:21-jdk-alpine`, run with `eclipse-temurin:21-jre-alpine`; exposes port 8080
4. **README.md** — how to build, test, and run (plain text, 10+ lines)
