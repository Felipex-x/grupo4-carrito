```markdown
# Ejemplos de Uso - API de Carrito y Checkout

Este archivo documenta el comportamiento real de la API conectada a Supabase PostgreSQL, incluyendo casos de éxito y manejo de errores según el estándar HTTP.

**URL Base del servicio:** `https://grupo4-carrito.onrender.com`

---

## Flujo Completo de Carrito y Checkout

### 1. Ver carrito vacío (o crear uno nuevo)

**Request:**
```http
GET https://grupo4-carrito.onrender.com/cart/Juan
```

**Response 200:**
```json
{
  "id": "3ca18d75-1d89-4944-a9e6-371c6454c9f7",
  "userId": "Juan",
  "status": "ACTIVE",
  "items": [],
  "totalAmount": 0
}
```

**Response 404 - Carrito no encontrado:**
```json
{
  "detail": "Carrito no encontrado"
}
```

---

### 2. Agregar producto al carrito

**Request:**
```http
POST https://grupo4-carrito.onrender.com/cart/Juan/items
Content-Type: application/json

{
  "productId": "P-100",
  "name": "Caña XYZ",
  "price": 14990,
  "quantity": 1
}
```

**Response 200:**
```json
{
  "id": "3ca18d75-1d89-4944-a9e6-371c6454c9f7",
  "userId": "Juan",
  "status": "ACTIVE",
  "items": [
    {
      "productId": "P-100",
      "name": "Caña XYZ",
      "quantity": 1,
      "unitPrice": 14990,
      "subtotal": 14990
    }
  ],
  "totalAmount": 14990
}
```

**Response 400 - Body inválido (falta quantity):**
```json
{
  "detail": "productId y quantity requeridos"
}
```

---

### 3. Agregar otro producto al carrito

**Request:**
```http
POST https://grupo4-carrito.onrender.com/cart/Juan/items
Content-Type: application/json

{
  "productId": "P-205",
  "name": "Vino Tinto",
  "price": 19990,
  "quantity": 1
}
```

**Response 200:**
```json
{
  "id": "3ca18d75-1d89-4944-a9e6-371c6454c9f7",
  "userId": "Juan",
  "status": "ACTIVE",
  "items": [
    {
      "productId": "P-100",
      "name": "Caña XYZ",
      "quantity": 1,
      "unitPrice": 14990,
      "subtotal": 14990
    },
    {
      "productId": "P-205",
      "name": "Vino Tinto",
      "quantity": 1,
      "unitPrice": 19990,
      "subtotal": 19990
    }
  ],
  "totalAmount": 34980
}
```

---

### 4. Ver carrito con productos

**Request:**
```http
GET https://grupo4-carrito.onrender.com/cart/Juan
```

**Response 200:**
```json
{
  "id": "3ca18d75-1d89-4944-a9e6-371c6454c9f7",
  "userId": "Juan",
  "status": "ACTIVE",
  "items": [
    {
      "productId": "P-100",
      "name": "Caña XYZ",
      "quantity": 1,
      "unitPrice": 14990,
      "subtotal": 14990
    },
    {
      "productId": "P-205",
      "name": "Vino Tinto",
      "quantity": 1,
      "unitPrice": 19990,
      "subtotal": 19990
    }
  ],
  "totalAmount": 34980
}
```

---

### 5. Eliminar producto del carrito

**Request:**
```http
DELETE https://grupo4-carrito.onrender.com/cart/Juan/items/P-100
```

**Response 204:**
```
No Content (sin body)
```

**Response 404 - Item no encontrado:**
```json
{
  "detail": "Item no encontrado en el carrito"
}
```

---

### 6. Hacer checkout

**Request:**
```http
POST https://grupo4-carrito.onrender.com/checkout
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "userId": "Juan"
}
```

**Response 201:**
```json
{
  "orderId": "ORD-1001",
  "status": "CREATED",
  "totalAmount": 14990
}
```

**Response 400 - Faltan campos:**
```json
{
  "detail": "userId y idempotencyKey requeridos"
}
```

**Response 404 - Carrito no encontrado:**
```json
{
  "detail": "Carrito no encontrado"
}
```

---

### 7. Intentar checkout duplicado (MISMO Idempotency-Key)

**Request:**
```http
POST https://grupo4-carrito.onrender.com/checkout
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "userId": "Juan"
}
```

**Response 409:**
```json
{
  "detail": "Duplicate Idempotency-Key",
  "orderId": "ORD-1001"
}
```

**Nota:** El sistema detecta que ya existe una orden con ese `Idempotency-Key` y devuelve la orden original en lugar de crear un duplicado. Esto implementa el patrón de idempotencia.

---

## Resumen de Códigos de Estado HTTP

| Código | Significado | Ejemplo |
|--------|-------------|---------|
| 200 | OK - Request exitoso | GET /cart, POST /items |
| 201 | Created - Recurso creado | POST /checkout |
| 204 | No Content - Eliminación exitosa | DELETE /items |
| 400 | Bad Request - Datos inválidos | Body sin campos requeridos |
| 404 | Not Found - Recurso no existe | Carrito o item no encontrado |
| 409 | Conflict - Idempotencia | Checkout duplicado |
| 500 | Internal Server Error | Error de base de datos |

---

## Ejecución de Pruebas Automatizadas

La colección de Postman se encuentra exportada en el repositorio: `postman_collection.json`

### Cómo ejecutar:

1. Importar `postman_collection.json` en Postman
2. Configurar ambiente "E2" con:
   - `BASE_URL`: `https://grupo4-carrito.onrender.com`
3. Click derecho en "Grupo 4 Carrito" → "Run collection"
4. Seleccionar ambiente "E2"
5. Deben pasar 8 tests

### Resultados esperados:

| Endpoint | Status | Test |
|----------|--------|------|
| GET /cart/Juan | 200 | ✅ Status is 200, Response has items |
| POST /cart/Juan/items | 200 | ✅ Status is 200, Response has items |
| POST /checkout (primero) | 201 | ✅ Status is 201, Response has orderId |
| POST /checkout (duplicado) | 409 | ✅ Status is 409 for duplicate |
| DELETE /cart/Juan/items/P-100 | 204 | ✅ Status is 204 |
```
