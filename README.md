![CI](https://github.com/Paolo-Cypher/grupo4-carrito/actions/workflows/ci.yml/badge.svg)

# Grupo 4 - Carrito y Checkout (G4)

**E4 Integracion de Servicios - Mini Marketplace Cloud 2026**

Microservicio de Carrito y Checkout que integra autenticacion (G2), catalogo de productos (G3) y servicio de pedidos (G5) con patrones de idempotencia y trazabilidad distribuida.

**API:** https://grupo4-carrito.onrender.com
**Swagger:** https://grupo4-carrito.onrender.com/docs

---

## Estado del Proyecto E4

| Componente | Estado | Descripcion |
|------------|--------|-------------|
| **G2 - Autenticacion** | Funcionando | Validacion de token Bearer en todos los endpoints |
| **G3 - Catalogo** | Funcionando | Consulta de precios reales con headers de trazabilidad |
| **G5 - Pedidos** | Funcionando | Creacion de ordenes con idempotencia |
| **Trazabilidad** | Implementado | X-Correlation-Id, X-Request-Id, X-Consumer |
| **Idempotencia** | Implementado | Header Idempotency-Key en POST /checkout |
| **CI/CD** | Configurado | GitHub Actions con pipeline verde |

---

## Endpoints

### Headers Requeridos

Todos los endpoints requieren:

```
Authorization: Bearer {access_token}
X-Correlation-Id: {uuid}
X-Request-Id: {uuid}
X-Consumer: grupo-4
Accept: application/json
```

---

### GET /cart/{userId}

Obtiene el carrito de un usuario con sus items y precios reales.

**Request:**
```bash
curl -X GET https://grupo4-carrito.onrender.com/cart/USR-01 \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "X-Correlation-Id: abc-123" \
  -H "X-Request-Id: prueba-123" \
  -H "X-Consumer: grupo-4" \
  -H "Accept: application/json"
```

**Response 200 OK:**
```json
{
  "id": "1b793710-9a51-4324-a0b1-0fff78726a3b",
  "userId": "USR-01",
  "status": "ACTIVE",
  "items": [
    {
      "id": "848d9742-068d-4ba1-9cf1-843beef97fbb",
      "cart_id": "1b793710-9a51-4324-a0b1-0fff78726a3b",
      "product_id": "0e319c09-7aa8-4162-b0dd-7f8e6f5a610a",
      "quantity": 1,
      "unit_price": 89990,
      "subtotal": 89990
    },
    {
      "id": "6b4180d4-9882-475d-90c4-7139fc828501",
      "product_id": "6e334f56-66c4-4e2c-8e0b-e8f981d3c80a",
      "quantity": 1,
      "unit_price": 8990,
      "subtotal": 8990
    }
  ],
  "totalAmount": 98980
}
```

**Response 401 Unauthorized:**
```json
{
  "timestamp": "2026-07-09T00:00:00.000Z",
  "status": 401,
  "code": "UNAUTHORIZED",
  "message": "Token requerido",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### POST /cart/{userId}/items

Agrega un item al carrito consultando el precio real en G3.

**Request:**
```bash
curl -X POST https://grupo4-carrito.onrender.com/cart/USR-01/items \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "X-Correlation-Id: abc-123" \
  -H "X-Request-Id: 123456" \
  -H "X-Consumer: grupo-4" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "productId": "0e319c09-7aa8-4162-b0dd-7f8e6f5a610a",
    "quantity": 1
  }'
```

**Response 200 OK:**
```json
{
  "id": "uuid",
  "userId": "USR-01",
  "productId": "0e319c09-7aa8-4162-b0dd-7f8e6f5a610a",
  "unitPrice": 89990,
  "quantity": 1,
  "subtotal": 89990
}
```

**Response 503 Service Unavailable:**
```json
{
  "timestamp": "2026-07-09T00:00:00.000Z",
  "status": 503,
  "code": "SERVICE_UNAVAILABLE",
  "message": "Grupo 3 no responde",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### DELETE /cart/{userId}/items/{productId}

Elimina un item del carrito.

**Request:**
```bash
curl -X DELETE https://grupo4-carrito.onrender.com/cart/USR-01/items/0e319c09-7aa8-4162-b0dd-7f8e6f5a610a \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "X-Correlation-Id: abc-123" \
  -H "X-Request-Id: prueba-123" \
  -H "X-Consumer: grupo-4" \
  -H "Accept: application/json"
```

**Response 204 No Content:** Item eliminado exitosamente

**Response 403 Forbidden:**
```json
{
  "timestamp": "2026-07-09T00:00:00.000Z",
  "status": 403,
  "code": "FORBIDDEN",
  "message": "El usuario del token no coincide con el recurso solicitado",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response 404 Not Found:**
```json
{
  "timestamp": "2026-07-09T00:00:00.000Z",
  "status": 404,
  "code": "NOT_FOUND",
  "message": "Item not found",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### POST /checkout

Procesa el checkout del carrito creando una orden en G5.

**Request:**
```bash
curl -X POST https://grupo4-carrito.onrender.com/checkout \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "X-Correlation-Id: abc-123" \
  -H "X-Request-Id: prueba-123" \
  -H "X-Consumer: grupo-4" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: 8d5d4d9f-7c82-4b1f-bf92-4df3c6d7d5e2" \
  -d '{
    "userId": "USR-01"
  }'
```

**Response 201 Created:**
```json
{
  "orderId": "ORD-1783567511437",
  "status": "CREATED",
  "totalAmount": 61980
}
```

**Response 409 Conflict (Idempotencia):**
```json
{
  "timestamp": "2026-07-09T00:00:00.000Z",
  "status": 409,
  "code": "DUPLICATED_ORDER",
  "message": "Intento duplicado, orderId existente: ORD-1783567511437",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response 400 Bad Request:**
```json
{
  "timestamp": "2026-07-09T00:00:00.000Z",
  "status": 400,
  "code": "EMPTY_CART",
  "message": "Carrito vacio",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Integraciones E4

### G2 - Autenticacion
- **URL:** https://auth-minimarket-cloud.onrender.com
- **Endpoint:** GET /auth/validate
- **Proposito:** Validar token Bearer antes de procesar requests
- **Implementacion:** Middleware global authMiddleware
- **Estado:** Funcionando

### G3 - Catalogo
- **URL:** https://catalog-api-cm1l.onrender.com/api/v1/products
- **Endpoint:** GET /products/{id}
- **Headers Requeridos:** X-Consumer, X-Request-Id, X-Correlation-Id, Accept
- **Proposito:** Obtener precio real de productos
- **Estado:** Funcionando (requiere headers de trazabilidad)
- **Nota:** Sin los headers correctos, G3 devuelve 400 o timeout

### G5 - Pedidos
- **URL:** https://pedidos-g5.onrender.com/orders
- **Endpoint:** POST /orders
- **Header:** Idempotency-Key
- **Proposito:** Crear orden final con idempotencia
- **Estado:** Funcionando

---

## Arquitectura

```
+-----------------+
|   Cliente G1    |
+--------+--------+
         | HTTP Requests
         | (Auth + Headers)
         v
+-----------------------------+
|  G4 - Carrito y Checkout    |
|  grupo4-carrito.onrender.com|
|                             |
|  GET /cart/{userId}         |
|  POST /cart/{userId}/items  |
|  DELETE /cart/{userId}/items/{id}
|  POST /checkout             |
+---+-----------+-------------+
    |           |             |
    v           v             v
+------+  +-----------+  +-----------+
|  G2  |  |    G3     |  |    G5     |
| Auth |  | Catalogo  |  |  Pedidos  |
+------+  +-----------+  +-----------+
                  |
                  v
            +-----------+
            |  Supabase |
            | PostgreSQL|
            +-----------+
```

**Diagrama completo:** docs/diagrama_arquitectura.png
**Diagrama de secuencia:** docs/diagrama_secuencia_trazabilidad.png

---

## Patrones Tecnicos

### Idempotencia
- **Implementacion:** Header Idempotency-Key en POST /checkout
- **Almacenamiento:** Tabla checkout_attempts con UNIQUE constraint
- **Comportamiento:**
  - Primera peticion: 201 Created (crea orden)
  - Peticion duplicada: 409 Conflict (devuelve orderId existente)
- **Beneficio:** Previene ordenes duplicadas en retries de red

### Trazabilidad
- **Headers:** X-Correlation-Id, X-Request-Id, X-Consumer
- **Propagacion:** Se propagan a G2, G3 y G5
- **Beneficio:** Permite rastrear requests en logs distribuidos
- **Ejemplo:** 550e8400-e29b-41d4-a716-446655440000

### Formato de Error Estandar
Todos los errores siguen este formato:
```json
{
  "timestamp": "2026-07-09T00:00:00.000Z",
  "status": 400,
  "code": "ERROR_CODE",
  "message": "Descripcion del error",
  "correlationId": "uuid-aqui"
}
```

---

## Pruebas de Integracion

### Pruebas Exitosas
| Test | Endpoint | Status | Descripcion |
|------|----------|--------|-------------|
| 1 | GET /cart/USR-01 | 200 OK | Autenticacion G2 funcionando |
| 2 | POST /items con headers G3 | 200 OK | Precio real de G3 (89990, 8990) |
| 3 | POST /checkout | 201 Created | Orden creada: ORD-1783567511437 |
| 4 | POST /checkout (duplicado) | 409 Conflict | Idempotencia funcionando |
| 5 | GET G3 directo | 200 OK | G3 operativo con headers |

### Pruebas Fallidas (Manejo de Errores)
| Test | Endpoint | Status | Descripcion |
|------|----------|--------|-------------|
| 1 | Sin token | 401 | Token requerido |
| 2 | G3 sin headers | 503 | G3 requiere X-Consumer, X-Request-Id |
| 3 | G3 timeout | 503 | Timeout en comunicacion |
| 4 | DELETE item inexistente | 404 | Validacion de items |
| 5 | Checkout vacio | 400 | Validacion de negocio |
| 6 | Usuario incorrecto | 403 | Validacion de seguridad |

**Coleccion Postman:** postman_collection.json

---

## Documentacion E4

- **Informe E4:** docs/Informe_E4_Grupo4.pdf
- **Diagrama de Arquitectura:** docs/diagrama_arquitectura.png
- **Diagrama de Secuencia:** docs/diagrama_secuencia_trazabilidad.png
- **Swagger:** https://grupo4-carrito.onrender.com/docs
- **API:** https://grupo4-carrito.onrender.com

---

## Stack Tecnologico

- **Runtime:** Node.js + Express
- **Base de Datos:** Supabase (PostgreSQL)
- **CI/CD:** GitHub Actions
- **Hosting:** Render (tier free)
- **Seguridad:** RLS policies + JWT validation

---

## Equipo E4

| Rol | Nombre | Responsabilidad |
|-----|--------|-----------------|
| **P1** | Paolo | GitHub Actions + Tests + Trazabilidad |
| **P2** | Mauricio | Integracion G2 (Autenticacion) |
| **P3** | Benjamin | Integracion G3 (Catalogo) + Mejoras G5 |
| **P4** | Felipe | Pruebas de Integracion + Diagrama + Informe E4 |
