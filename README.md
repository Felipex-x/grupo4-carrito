# grupo4-carrito
Mock del carrito - E2
# Grupo 4 - Carrito y Checkout (E2)

## Descripción
Mock funcional del carrito para E2. Simula 4 endpoints del carrito sin conectar a BD.

## Instalación

### Local
```bash
git clone https://github.com/Paolo-Cypher/grupo4-carrito.git
cd grupo4-carrito
pip install -r requirements.txt
python -m uvicorn src.main:app --reload

Accede en: http://localhost:8000

Servidor (Render)
URL: https://grupo4-carrito.onrender.com/cart/juan

Swagger:

URL: https://grupo4-carrito.onrender.com/docs

Endpoints

1. GET /cart/{userId}

Obtiene el carrito del usuario

Request:

GET /cart/Juan

Response:
{
    "id": "carrito-123",
    "userId": "Juan",
    "status": "ACTIVE",
    "items": [],
    "total": 0
}

2. POST /cart/{userId}/items

Agrega un producto al carrito

Request:

POST /cart/Juan/items

{
    "productId": "P-100",
    "quantity": 1
}

Response:

{
    "id": "carrito-123",
    "userId": "Juan",
    "status": "ACTIVE",
    "items": [
        {
            "productId": "P-100",
            "quantity": 1,
            "price": 14990,
            "subtotal": 14990
        }
    ],
    "total": 14990
}

3. DELETE /cart/{userId}/items/{productId}

Elimina un producto del carrito

Request:

DELETE /cart/Juan/items/P-100

Response:

{
    "status": 204,
    "message": "Item eliminado"
}

4. POST /checkout

Crea un pedido (IMPORTANTE: incluir Idempotency-Key)

Request:

POST /checkout

Headers:

Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000

Body:

{
    "userId": "Juan"
}

Response:

{
    "orderId": "ORD-1001",
    "status": "CREATED",
    "totalAmount": 14990
}

Pruebas con Postman

    Importa: postman_collection.json

    Selecciona ambiente: "E2"

    Ejecuta tests: Click "Run"

    Debes ver 5 tests verdes



Modelo de Datos

Ver: docs/modelo_datos.sql y docs/modelo_documentacion.txt

Postman

Ver: postman_collection.json.json