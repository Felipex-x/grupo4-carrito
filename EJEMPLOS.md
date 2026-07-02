# Ejemplos de Requests y Respuestas Reales

## GET /cart/{userId}

### Request Exitoso
```http
GET /cart/Juan
```

**Response 200** (si el carrito ya existe con items):
```json
{
  "id": "3ca18d75-1d89-4944-a9e6-371c6454c9f7",
  "userId": "Juan",
  "status": "ACTIVE",
  "items": [
    {
      "cart_id": "3ca18d75-1d89-4944-a9e6-371c6454c9f7",
      "product_id": "P-100",
      "quantity": 1,
      "unit_price": 14990,
      "subtotal": 14990
    }
  ],
  "totalAmount": 14990
}
```

**Nota:** Si el carrito no existe, se **crea automáticamente** y devuelve 200 con `items: []`. Este endpoint nunca devuelve 404.


#POST /cart/{userId}/items
Request

```http
POST /cart/Juan/items
Content-Type: application/json

{
  "productId": "P-100",
  "quantity": 1
}
```


#Response 200
json 
{
  "userId": "Juan",
  "items": [
    {
      "productId": "P-100",
      "name": "Caña XYZ",
      "price": 14990,
      "quantity": 1
    }
  ],
  "totalAmount": 14990,
  "status": "ACTIVE"
}


"Response 400 - Body inválido" 
http 
POST /cart/Juan/items
Content-Type: application/json

{
  "productId": "P-100"
}

json 
{
  "detail": "productId y quantity requeridos"
}

DELETE /cart/{userId}/items/{productId}
Request Exitoso
http 
DELETE /cart/Juan/items/P-100

# Response 204
(No content)
Response 404 - Item no encontrado
http 
DELETE /cart/Juan/items/P-999

json 
{
  "detail": "Item no encontrado en el carrito"
}


#POST /checkout
Request Exitoso

http
POST /checkout
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "userId": "Juan"
}

#Response 201
json
{
  "orderId": "ORD-12345",
  "status": "CREATED",
  "totalAmount": 14990
}

#Response 409 - Idempotency-Key duplicada

```http
POST /checkout
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "userId": "Juan"
}
```

```json
{
  "detail": {
    "message": "Intento duplicado",
    "orderId": "ORD-1001",
    "status": "DUPLICATED_ORDER"
  }
}
```


#Response 400 - Faltan campos
http 
POST /checkout
Content-Type: application/json

{}

json 
{
  "detail": "userId y idempotencyKey requeridos"
}

#Response 404 - Carrito no encontrado
http 
POST /checkout
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440001
Content-Type: application/json

{
  "userId": "UsuarioInexistente"
}

json 
{
  "detail": "Carrito no encontrado"
}



## Códigos de Estado HTTP

La API utiliza los siguientes códigos de estado HTTP según el estándar:

| Código | Significado | Ejemplo |
|--------|-------------|---------|
| 200 | OK - Request exitoso | GET /cart, POST /items |
| 201 | Created - Recurso creado | POST /checkout |
| 204 | No Content - Eliminación exitosa | DELETE /items |
| 400 | Bad Request - Datos inválidos | Body sin campos requeridos |
| 404 | Not Found - Recurso no existe | Carrito o item no encontrado |
| 409 | Conflict - Idempotencia | Checkout duplicado |
| 500 | Internal Server Error | Error de base de datos |
