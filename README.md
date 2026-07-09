![CI](https://github.com/Paolo-Cypher/grupo4-carrito/actions/workflows/ci.yml/badge.svg)

# Grupo 4 - Carrito y Checkout (G4)

**E4 Integración de Servicios - Mini Marketplace Cloud**

Microservicio de Carrito y Checkout que integra autenticación (G2), catálogo de productos (G3) y servicio de pedidos (G5) con patrones de idempotencia y trazabilidad distribuida.

---

## 🚀 Estado del Proyecto E4

| Componente | Estado | Descripción |
|------------|--------|-------------|
| **G2 - Autenticación** | ✅ Funcionando | Validación de token Bearer en todos los endpoints |
| **G3 - Catálogo** | ⚠️ Implementado | Consulta de precios reales (timeout en producción) |
| **G5 - Pedidos** | ✅ Funcionando | Creación de órdenes con idempotencia |
| **Trazabilidad** | ✅ Implementado | X-Correlation-Id en todos los flujos |
| **Idempotencia** | ✅ Implementado | Header Idempotency-Key en POST /checkout |
| **CI/CD** | ✅ Configurado | GitHub Actions con pipeline verde |

---

## 📡 Endpoints

### 🔐 Autenticación Requerida
Todos los endpoints requieren:
```
Authorization: Bearer {access_token}
X-Correlation-Id: {uuid}
```

### GET /cart/{userId}
Obtiene el carrito de un usuario.

**Ejemplo:**
```bash
curl -X GET https://grupo4-carrito.onrender.com/cart/USR-11 \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "X-Correlation-Id: 550e8400-e29b-41d4-a716-446655440000"
```

**Respuesta 200 OK:**
```json
{
  "id": "uuid",
  "userId": "USR-11",
  "status": "ACTIVE",
  "items": [],
  "totalAmount": 0
}
```

**Respuesta 401 Unauthorized:**
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

**Ejemplo:**
```bash
curl -X POST https://grupo4-carrito.onrender.com/cart/USR-11/items \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "X-Correlation-Id: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "productId": "0e319c09-7aa8-4162-b0dd-7f8e6f5a610a",
    "quantity": 1
  }'
```

**Respuesta 200 OK:**
```json
{
  "id": "uuid",
  "userId": "USR-11",
  "productId": "0e319c09-7aa8-4162-b0dd-7f8e6f5a610a",
  "unitPrice": 89990,
  "quantity": 1,
  "subtotal": 89990
}
```

**Respuesta 503 Service Unavailable:**
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

**Ejemplo:**
```bash
curl -X DELETE https://grupo4-carrito.onrender.com/cart/USR-11/items/0e319c09-7aa8-4162-b0dd-7f8e6f5a610a \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "X-Correlation-Id: 550e8400-e29b-41d4-a716-446655440000"
```

**Respuesta 204 No Content:** Item eliminado exitosamente

**Respuesta 403 Forbidden:**
```json
{
  "timestamp": "2026-07-09T00:00:00.000Z",
  "status": 403,
  "code": "FORBIDDEN",
  "message": "El usuario del token no coincide con el recurso solicitado",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### POST /checkout
Procesa el checkout del carrito creando una orden en G5.

**Ejemplo:**
```bash
curl -X POST https://grupo4-carrito.onrender.com/checkout \
  -H "Authorization: Bearer eyJhbGciOi..." \
  -H "X-Correlation-Id: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Idempotency-Key: 770e8400-e29b-41d4-a716-446655440001" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "USR-11"
  }'
```

**Respuesta 201 Created:**
```json
{
  "attemptId": "uuid",
  "orderId": "ORD-1001",
  "status": "CREATED",
  "message": "Orden creada exitosamente"
}
```

**Respuesta 409 Conflict (Idempotencia):**
```json
{
  "timestamp": "2026-07-09T00:00:00.000Z",
  "status": 409,
  "code": "DUPLICATED_ORDER",
  "message": "Intento duplicado, orderId existente: ORD-1001",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 🔗 Integraciones E4

### G2 - Autenticación ✅
- **URL:** https://auth-minimarket-cloud.onrender.com
- **Endpoint:** GET /auth/validate
- **Propósito:** Validar token Bearer antes de procesar requests
- **Implementación:** Middleware global `authMiddleware`
- **Estado:** ✅ Funcionando

### G3 - Catálogo ⚠️
- **URL:** https://catalog-api-cm1l.onrender.com/api/v1/products
- **Endpoint:** GET /products/{id}
- **Headers:** X-Request-Id, X-Correlation-Id, X-Consumer
- **Propósito:** Obtener precio real de productos
- **Estado:** ⚠️ Implementado (timeout en producción)

### G5 - Pedidos ✅
- **URL:** https://pedidos-g5.onrender.com/orders
- **Endpoint:** POST /orders
- **Header:** Idempotency-Key
- **Propósito:** Crear orden final con idempotencia
- **Estado:** ✅ Funcionando

---

## 🏗️ Arquitectura

```
┌─────────────┐
│  Cliente G1 │
└──────┬──────┘
       │ HTTP Requests
       ▼
┌─────────────────────────────────────┐
│  G4 - Carrito y Checkout            │
│  grupo4-carrito.onrender.com        │
│                                     │
│  GET /cart/{userId}                 │
│  POST /cart/{userId}/items          │
│  DELETE /cart/{userId}/items/{id}   │
│  POST /checkout                     │
└──┬────────────┬────────────────┬────┘
   │            │                │
   ▼            ▼                ▼
┌──────┐   ┌────────┐      ┌────────┐
│  G2  │   │   G3   │      │   G5   │
│ Auth │   │Catálogo│      │Pedidos │
└──────┘   └────────┘      └────────┘
                  │
                  ▼
            ┌──────────┐
            │ Supabase │
            │PostgreSQL│
            └──────────┘
```

**Diagrama completo:** [docs/diagrama_arquitectura.png](docs/diagrama_arquitectura.png)

---

## 🎯 Patrones Técnicos

### Idempotencia
- **Implementación:** Header `Idempotency-Key` en POST /checkout
- **Almacenamiento:** Tabla `checkout_attempts` con UNIQUE constraint
- **Comportamiento:**
  - Primera petición: 201 Created (crea orden)
  - Petición duplicada: 409 Conflict (devuelve orderId existente)
- **Beneficio:** Previene órdenes duplicadas en retries de red

### Trazabilidad
- **Header:** `X-Correlation-Id` (UUID v4)
- **Propagación:** Se propaga a G2, G3 y G5
- **Beneficio:** Permite rastrear requests en logs distribuidos
- **Ejemplo:** 550e8400-e29b-41d4-a716-446655440000

### Formato de Error Estándar
Todos los errores siguen este formato:
```json
{
  "timestamp": "2026-07-09T00:00:00.000Z",
  "status": 400,
  "code": "ERROR_CODE",
  "message": "Descripción del error",
  "correlationId": "uuid-aqui"
}
```

---

## 🧪 Pruebas de Integración

### Pruebas Exitosas
| Test | Endpoint | Status | Descripción |
|------|----------|--------|-------------|
| 1 | GET /cart/USR-11 | 200 OK | Autenticación G2 funcionando |
| 2 | POST /checkout (duplicado) | 409 Conflict | Idempotencia funcionando |
| 3 | GET G3 directo | 200 OK | G3 operativo (precio: 89990) |

### Pruebas Fallidas (Manejo de Errores)
| Test | Endpoint | Status | Descripción |
|------|----------|--------|-------------|
| 1 | Sin token | 401 | Token requerido |
| 2 | G3 responde 400 | 503 | G4 maneja error de G3 |
| 3 | G3 timeout | 503 | Timeout en comunicación |
| 4 | DELETE item inexistente | 404 | Validación de items |
| 5 | Checkout vacío | 400 | Validación de negocio |
| 6 | Usuario incorrecto | 403 | Validación de seguridad |

**Colección Postman:** [postman_collection.json](postman_collection.json)

---

## 📚 Documentación E4

- **Informe E4:** [docs/Informe_E4_Grupo4.pdf](docs/Informe_E4_Grupo4.pdf)
- **Diagrama de Arquitectura:** [docs/diagrama_arquitectura.png](docs/diagrama_arquitectura.png)
- **Swagger:** https://grupo4-carrito.onrender.com/docs
- **API:** https://grupo4-carrito.onrender.com

---

## 🛠️ Stack Tecnológico

- **Runtime:** Node.js + Express
- **Base de Datos:** Supabase (PostgreSQL)
- **CI/CD:** GitHub Actions
- **Hosting:** Render (tier free)
- **Seguridad:** RLS policies + JWT validation

---

## 👥 Equipo E4

| Rol | Nombre | Responsabilidad |
|-----|--------|-----------------|
| **P1** | Paolo | GitHub Actions + Tests + Trazabilidad |
| **P2** | Mauricio | Integración G2 (Autenticación) |
| **P3** | Benjamín | Integración G3 (Catálogo) + Mejoras G5 |
| **P4** | Felipe | Pruebas de Integración + Diagrama + Informe E4 |
