from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# ENDPOINT 1: Ver carrito
@app.get("/cart/{userId}")
async def get_cart(userId: str):
    return {
        "id": "carrito-123",
        "userId": userId,
        "status": "ACTIVE",
        "items": [],
        "total": 0
    }

# ENDPOINT 2: Agregar producto
@app.post("/cart/{userId}/items")
async def add_item(userId: str, productId: str = None, quantity: int = 1):
    return {
        "id": "carrito-123",
        "userId": userId,
        "status": "ACTIVE",
        "items": [
            {
                "productId": productId,
                "quantity": quantity,
                "price": 14990,
                "subtotal": 14990
            }
        ],
        "total": 14990
    }

# ENDPOINT 3: Eliminar producto
@app.delete("/cart/{userId}/items/{productId}")
async def delete_item(userId: str, productId: str):
    return {"status": 204, "message": "Item eliminado"}

# ENDPOINT 4: Hacer checkout
@app.post("/checkout")
async def checkout(userId: str = None, idempotencyKey: str = None):
    return {
        "orderId": "ORD-1001",
        "status": "CREATED",
        "totalAmount": 14990
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
