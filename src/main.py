from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# ALMACENAMIENTO EN MEMORIA (para el mock)
# En producción sería una base de datos
carts = {}
checkout_attempts = {}  # Aquí guardamos los intentos para idempotencia

# ENDPOINT 1: Ver carrito
@app.get("/cart/{userId}")
async def get_cart(userId: str):
    if userId not in carts:
        carts[userId] = {
            "id": f"carrito-{userId}",
            "userId": userId,
            "status": "ACTIVE",
            "items": [],
            "total": 0
        }
    return carts[userId]

# ENDPOINT 2: Agregar producto
@app.post("/cart/{userId}/items")
async def add_item(userId: str, productId: str = None, quantity: int = 1):
    if userId not in carts:
        carts[userId] = {
            "id": f"carrito-{userId}",
            "userId": userId,
            "status": "ACTIVE",
            "items": [],
            "total": 0
        }
    
    # Simular agregar item
    new_item = {
        "productId": productId,
        "quantity": quantity,
        "price": 14990,
        "subtotal": quantity * 14990
    }
    
    carts[userId]["items"].append(new_item)
    carts[userId]["total"] = sum(item["subtotal"] for item in carts[userId]["items"])
    
    return carts[userId]

# ENDPOINT 3: Eliminar producto
@app.delete("/cart/{userId}/items/{productId}")
async def delete_item(userId: str, productId: str):
    if userId not in carts:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    carts[userId]["items"] = [
        item for item in carts[userId]["items"] 
        if item["productId"] != productId
    ]
    carts[userId]["total"] = sum(item["subtotal"] for item in carts[userId]["items"])
    
    return {"status": 204, "message": "Item eliminado"}

# ENDPOINT 4: Checkout (EL IMPORTANTE)
@app.post("/checkout", status_code=201)  # ← AQUÍ VA EL 201
async def checkout(userId: str = None, idempotencyKey: str = None):
    
    # VALIDACIÓN 1: Verificar que tenemos los datos
    if not userId or not idempotencyKey:
        raise HTTPException(status_code=400, detail="userId y idempotencyKey requeridos")
    
    # VALIDACIÓN 2: IDEMPOTENCIA - Revisar si ya procesamos este UUID
    if idempotencyKey in checkout_attempts:
        # Ya existe este intento
        existing = checkout_attempts[idempotencyKey]
        
        # Si fue exitoso, devolvemos 409 (Conflict)
        if existing["status"] == "SUCCESS":
            raise HTTPException(
                status_code=409, 
                detail={
                    "message": "Intento duplicado",
                    "orderId": existing["orderId"],
                    "status": "DUPLICATED_ORDER"
                }
            )
    
    # VALIDACIÓN 3: Verificar que el carrito existe y tiene items
    if userId not in carts or len(carts[userId]["items"]) == 0:
        raise HTTPException(status_code=400, detail="Carrito vacío")
    
    # CREAR NUEVO INTENTO
    orderId = f"ORD-{len(checkout_attempts) + 1001}"
    
    checkout_attempts[idempotencyKey] = {
        "orderId": orderId,
        "status": "SUCCESS",
        "totalAmount": carts[userId]["total"]
    }
    
    # MARCAR CARRITO COMO CHECKED_OUT
    carts[userId]["status"] = "CHECKED_OUT"
    
    # DEVOLVER RESPUESTA 201 CREATED
    return {
        "orderId": orderId,
        "status": "CREATED",
        "totalAmount": carts[userId]["total"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)