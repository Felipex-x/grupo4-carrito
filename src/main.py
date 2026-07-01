import os
import json
from urllib import error as urllib_error
from urllib import request as urllib_request

from fastapi import FastAPI, HTTPException, Header, Response, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic import Field
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Inicializar Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
g5_orders_url = os.getenv("G5_ORDERS_URL")
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL y SUPABASE_ANON_KEY son requeridos")

supabase: Client = create_client(supabase_url, supabase_key)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Solicitud inválida", "errors": exc.errors()}
    )


def _normalize_user_id(user_id: str) -> str:
    normalized = user_id.strip() if user_id else ""
    if not normalized:
        raise HTTPException(status_code=400, detail="userId es requerido")
    return normalized


def _build_g5_order_payload(user_id: str, cart_id: str, items: list[dict], total_amount: float, idempotency_key: str) -> dict:
    return {
        "userId": user_id,
        "cartId": cart_id,
        "items": [
            {
                "productId": item["product_id"],
                "quantity": item["quantity"],
                "unitPrice": item["unit_price"],
                "subtotal": item["subtotal"],
            }
            for item in items
        ],
        "totalAmount": total_amount,
        "idempotencyKey": idempotency_key,
    }


def _create_order_in_g5(payload: dict) -> dict:
    if not g5_orders_url:
        raise HTTPException(status_code=500, detail="G5_ORDERS_URL no configurada")

    body = json.dumps(payload).encode("utf-8")
    request = urllib_request.Request(
        g5_orders_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib_request.urlopen(request, timeout=10) as response:
            response_text = response.read().decode("utf-8")
            return json.loads(response_text) if response_text else {}
    except urllib_error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="ignore")
        raise HTTPException(
            status_code=500,
            detail=f"G5 respondió {error.code}: {error_body or error.reason}"
        )
    except urllib_error.URLError as error:
        raise HTTPException(status_code=500, detail=f"No se pudo conectar con G5: {error.reason}")
# ============================================
# MODELOS PYDANTIC
# ============================================

class AddItemRequest(BaseModel):
    productId: str
    quantity: int = Field(default=1, gt=0)

class CheckoutRequest(BaseModel):
    userId: str

# ============================================
# ENDPOINT 1: Ver carrito
# ============================================

@app.get("/cart/{userId}")
async def get_cart(userId: str):
    try:
        userId = _normalize_user_id(userId)

        # Obtener o crear carrito
        result = supabase.table("carts").select("*").eq("user_id", userId).eq("status", "ACTIVE").execute()
        
        if not result.data:
            # Si no existe carrito activo, crear uno
            new_cart = supabase.table("carts").insert({
                "user_id": userId,
                "status": "ACTIVE"
            }).execute()
            cart_id = new_cart.data[0]["id"]
        else:
            cart_id = result.data[0]["id"]
        
        # Obtener items del carrito
        items_result = supabase.table("cart_items").select("*").eq("cart_id", cart_id).execute()
        
        # Calcular total
        total_amount = sum(item["subtotal"] for item in items_result.data) if items_result.data else 0
        
        return {
            "id": cart_id,
            "userId": userId,
            "status": "ACTIVE",
            "items": items_result.data or [],
            "totalAmount": total_amount
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================================
# ENDPOINT 2: Agregar producto
# ============================================

@app.post("/cart/{userId}/items")
async def add_item(userId: str, data: AddItemRequest):
    try:
        userId = _normalize_user_id(userId)

        # Obtener carrito
        cart_result = supabase.table("carts").select("*").eq("user_id", userId).eq("status", "ACTIVE").execute()
        
        if not cart_result.data:
            raise HTTPException(status_code=404, detail="Cart not found")
        
        cart = cart_result.data[0]
        cart_id = cart["id"]
        
        # Validar que el carrito no esté CHECKED_OUT
        if cart["status"] == "CHECKED_OUT":
            raise HTTPException(status_code=400, detail="El carrito ya fue procesado. No se pueden agregar productos.")
        
        # Insertar o actualizar item
        subtotal = data.quantity * 14990
        
        supabase.table("cart_items").upsert({
            "cart_id": cart_id,
            "product_id": data.productId,
            "quantity": data.quantity,
            "unit_price": 14990,
            "subtotal": subtotal
        }, on_conflict="cart_id,product_id").execute()
        
        # Obtener carrito actualizado
        items_result = supabase.table("cart_items").select("*").eq("cart_id", cart_id).execute()
        total_amount = sum(item["subtotal"] for item in items_result.data)
        
        return {
            "id": cart_id,
            "userId": userId,
            "status": cart["status"],
            "items": items_result.data,
            "totalAmount": total_amount
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================================
# ENDPOINT 3: Eliminar producto
# ============================================

@app.delete("/cart/{userId}/items/{productId}", status_code=204)
async def delete_item(userId: str, productId: str):
    try:
        userId = _normalize_user_id(userId)

        # Obtener carrito
        cart_result = supabase.table("carts").select("*").eq("user_id", userId).eq("status", "ACTIVE").execute()
        
        if not cart_result.data:
            raise HTTPException(status_code=404, detail="Cart not found")
        
        cart = cart_result.data[0]
        cart_id = cart["id"]
        
        item_result = supabase.table("cart_items").select("*").eq("cart_id", cart_id).eq("product_id", productId).execute()
        if not item_result.data:
            raise HTTPException(status_code=404, detail="Item not found")

        # Validar que el carrito no esté CHECKED_OUT
        if cart["status"] == "CHECKED_OUT":
            raise HTTPException(status_code=400, detail="El carrito ya fue procesado. No se pueden eliminar productos.")
        
        # Eliminar item
        supabase.table("cart_items").delete().eq("cart_id", cart_id).eq("product_id", productId).execute()
        
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================================
# ENDPOINT 4: Checkout
# ============================================

@app.post("/checkout", status_code=201)
async def checkout(
    data: CheckoutRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    try:
        userId = _normalize_user_id(data.userId)
        idempotencyKey = idempotency_key
        
        if not userId or not idempotencyKey:
            raise HTTPException(status_code=400, detail="userId y Idempotency-Key requeridos")
        
        # Verificar si ya existe este intento de checkout (idempotencia)
        existing = supabase.table("checkout_attempts").select("*").eq("idempotency_key", idempotencyKey).execute()
        
        if existing.data:
            current_attempt = existing.data[0]
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Intento duplicado",
                    "orderId": current_attempt.get("order_id"),
                    "status": "DUPLICATED_ORDER"
                }
            )
        
        # Obtener carrito
        cart_result = supabase.table("carts").select("*").eq("user_id", userId).eq("status", "ACTIVE").execute()
        
        if not cart_result.data:
            raise HTTPException(status_code=404, detail="Cart not found")
        
        cart = cart_result.data[0]
        cart_id = cart["id"]
        
        # Verificar que el carrito tenga items
        items_result = supabase.table("cart_items").select("*").eq("cart_id", cart_id).execute()
        if not items_result.data:
            raise HTTPException(status_code=400, detail="Carrito vacío")
        
        total_amount = sum(item["subtotal"] for item in items_result.data)
        
        # Registrar intento antes de llamar a G5
        supabase.table("checkout_attempts").insert({
            "cart_id": cart_id,
            "idempotency_key": idempotencyKey,
            "status": "PENDING"
        }).execute()
        
        # Marcar carrito como CHECKED_OUT
        supabase.table("carts").update({"status": "CHECKED_OUT"}).eq("id", cart_id).execute()

        g5_payload = _build_g5_order_payload(userId, cart_id, items_result.data, total_amount, idempotencyKey)
        g5_response = _create_order_in_g5(g5_payload)
        orderId = g5_response.get("orderId") or g5_response.get("order_id")

        if not orderId:
            supabase.table("carts").update({"status": "ACTIVE"}).eq("id", cart_id).execute()
            supabase.table("checkout_attempts").update({"status": "FAILED"}).eq("cart_id", cart_id).eq("idempotency_key", idempotencyKey).execute()
            raise HTTPException(status_code=500, detail="G5 no devolvió orderId")

        supabase.table("checkout_attempts").update({
            "order_id": orderId,
            "status": "SUCCESS"
        }).eq("cart_id", cart_id).eq("idempotency_key", idempotencyKey).execute()
        
        return {
            "orderId": orderId,
            "status": "CREATED",
            "totalAmount": total_amount
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================================
# EJECUTAR SERVIDOR
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)