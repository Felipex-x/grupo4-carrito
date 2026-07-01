const http = require("http");
const https = require("https");
const { URL } = require("url");

const express = require("express");
const { createClient } = require("@supabase/supabase-js");
require("dotenv").config();

const app = express();
app.use(express.json());

// ============================================
// INICIALIZAR SUPABASE
// ============================================

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;
const g5OrdersUrl = process.env.G5_ORDERS_URL;

if (!supabaseUrl || !supabaseKey) {
  throw new Error("SUPABASE_URL y SUPABASE_ANON_KEY son requeridos");
}

const supabase = createClient(supabaseUrl, supabaseKey);

// Ejecuta una query de supabase-js y, si devuelve error, lo lanza.
// Equivale a que supabase-py levante una excepción (atrapada como 500).
async function run(query) {
  const { data, error } = await query;
  if (error) {
    throw new Error(error.message);
  }
  return data;
}

// ============================================
// EXCEPCIÓN HTTP (equivalente a HTTPException)
// ============================================

class HttpException extends Error {
  constructor(statusCode, detail) {
    super(typeof detail === "string" ? detail : "HTTPException");
    this.statusCode = statusCode;
    this.detail = detail;
  }
}

class ValidationException extends Error {
  constructor(errors) {
    super("RequestValidationError");
    this.errors = errors;
  }
}

// ============================================
// HELPERS
// ============================================

function normalizeUserId(userId) {
  const normalized = userId ? userId.trim() : "";
  if (!normalized) {
    throw new HttpException(400, "userId es requerido");
  }
  return normalized;
}

function buildG5OrderPayload(userId, cartId, items, totalAmount, idempotencyKey) {
  return {
    userId: userId,
    cartId: cartId,
    items: items.map((item) => ({
      productId: item.product_id,
      quantity: item.quantity,
      unitPrice: item.unit_price,
      subtotal: item.subtotal,
    })),
    totalAmount: totalAmount,
    idempotencyKey: idempotencyKey,
  };
}

function createOrderInG5(payload) {
  return new Promise((resolve, reject) => {
    if (!g5OrdersUrl) {
      reject(new HttpException(500, "G5_ORDERS_URL no configurada"));
      return;
    }

    const body = Buffer.from(JSON.stringify(payload), "utf-8");
    let parsedUrl;
    try {
      parsedUrl = new URL(g5OrdersUrl);
    } catch (err) {
      reject(new HttpException(500, `No se pudo conectar con G5: ${err.message}`));
      return;
    }

    const transport = parsedUrl.protocol === "https:" ? https : http;
    const options = {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": body.length,
      },
      timeout: 10000,
    };

    const request = transport.request(parsedUrl, options, (response) => {
      let responseText = "";
      response.setEncoding("utf-8");
      response.on("data", (chunk) => {
        responseText += chunk;
      });
      response.on("end", () => {
        const statusCode = response.statusCode || 0;
        if (statusCode >= 400) {
          reject(
            new HttpException(
              500,
              `G5 respondió ${statusCode}: ${responseText || response.statusMessage}`
            )
          );
          return;
        }
        try {
          resolve(responseText ? JSON.parse(responseText) : {});
        } catch (err) {
          resolve({});
        }
      });
    });

    request.on("timeout", () => {
      request.destroy();
      reject(new HttpException(500, "No se pudo conectar con G5: timeout"));
    });

    request.on("error", (err) => {
      reject(new HttpException(500, `No se pudo conectar con G5: ${err.message}`));
    });

    request.write(body);
    request.end();
  });
}

// ============================================
// VALIDACIÓN DE BODY (equivalente a modelos Pydantic)
// ============================================

function parseAddItemRequest(body) {
  const errors = [];
  if (!body || typeof body.productId !== "string") {
    errors.push({ loc: ["body", "productId"], msg: "productId es requerido" });
  }
  let quantity = 1;
  if (body && body.quantity !== undefined) {
    quantity = body.quantity;
    if (!Number.isInteger(quantity) || quantity <= 0) {
      errors.push({ loc: ["body", "quantity"], msg: "quantity debe ser > 0" });
    }
  }
  if (errors.length > 0) {
    throw new ValidationException(errors);
  }
  return { productId: body.productId, quantity: quantity };
}

function parseCheckoutRequest(body) {
  const errors = [];
  if (!body || typeof body.userId !== "string") {
    errors.push({ loc: ["body", "userId"], msg: "userId es requerido" });
  }
  if (errors.length > 0) {
    throw new ValidationException(errors);
  }
  return { userId: body.userId };
}

// ============================================
// ENDPOINT 1: Ver carrito
// ============================================

app.get("/cart/:userId", async (req, res) => {
  try {
    const userId = normalizeUserId(req.params.userId);

    // Obtener o crear carrito
    const result = await run(
      supabase
        .from("carts")
        .select("*")
        .eq("user_id", userId)
        .eq("status", "ACTIVE")
    );

    let cartId;
    if (!result || result.length === 0) {
      // Si no existe carrito activo, crear uno
      const newCart = await run(
        supabase
          .from("carts")
          .insert({ user_id: userId, status: "ACTIVE" })
          .select()
      );
      cartId = newCart[0].id;
    } else {
      cartId = result[0].id;
    }

    // Obtener items del carrito
    const items = await run(
      supabase.from("cart_items").select("*").eq("cart_id", cartId)
    );

    // Calcular total
    const totalAmount =
      items && items.length > 0
        ? items.reduce((acc, item) => acc + item.subtotal, 0)
        : 0;

    return res.status(200).json({
      id: cartId,
      userId: userId,
      status: "ACTIVE",
      items: items || [],
      totalAmount: totalAmount,
    });
  } catch (e) {
    return handleError(res, e);
  }
});

// ============================================
// ENDPOINT 2: Agregar producto
// ============================================

app.post("/cart/:userId/items", async (req, res) => {
  try {
    const userId = normalizeUserId(req.params.userId);
    const data = parseAddItemRequest(req.body);

    // Obtener carrito
    const cartData = await run(
      supabase
        .from("carts")
        .select("*")
        .eq("user_id", userId)
        .eq("status", "ACTIVE")
    );

    if (!cartData || cartData.length === 0) {
      throw new HttpException(404, "Cart not found");
    }

    const cart = cartData[0];
    const cartId = cart.id;

    // Validar que el carrito no esté CHECKED_OUT
    if (cart.status === "CHECKED_OUT") {
      throw new HttpException(
        400,
        "El carrito ya fue procesado. No se pueden agregar productos."
      );
    }

    // Insertar o actualizar item
    const subtotal = data.quantity * 14990;

    await run(
      supabase.from("cart_items").upsert(
        {
          cart_id: cartId,
          product_id: data.productId,
          quantity: data.quantity,
          unit_price: 14990,
          subtotal: subtotal,
        },
        { onConflict: "cart_id,product_id" }
      )
    );

    // Obtener carrito actualizado
    const items = await run(
      supabase.from("cart_items").select("*").eq("cart_id", cartId)
    );
    const totalAmount = items.reduce((acc, item) => acc + item.subtotal, 0);

    return res.status(200).json({
      id: cartId,
      userId: userId,
      status: cart.status,
      items: items,
      totalAmount: totalAmount,
    });
  } catch (e) {
    return handleError(res, e);
  }
});

// ============================================
// ENDPOINT 3: Eliminar producto — 204 sin body
// ============================================

app.delete("/cart/:userId/items/:productId", async (req, res) => {
  try {
    const userId = normalizeUserId(req.params.userId);
    const productId = req.params.productId;

    // Obtener carrito
    const cartData = await run(
      supabase
        .from("carts")
        .select("*")
        .eq("user_id", userId)
        .eq("status", "ACTIVE")
    );

    if (!cartData || cartData.length === 0) {
      throw new HttpException(404, "Cart not found");
    }

    const cart = cartData[0];
    const cartId = cart.id;

    const itemData = await run(
      supabase
        .from("cart_items")
        .select("*")
        .eq("cart_id", cartId)
        .eq("product_id", productId)
    );
    if (!itemData || itemData.length === 0) {
      throw new HttpException(404, "Item not found");
    }

    // Validar que el carrito no esté CHECKED_OUT
    if (cart.status === "CHECKED_OUT") {
      throw new HttpException(
        400,
        "El carrito ya fue procesado. No se pueden eliminar productos."
      );
    }

    // Eliminar item
    await run(
      supabase
        .from("cart_items")
        .delete()
        .eq("cart_id", cartId)
        .eq("product_id", productId)
    );

    return res.status(204).send();
  } catch (e) {
    return handleError(res, e);
  }
});

// ============================================
// ENDPOINT 4: Checkout — Idempotency-Key en HEADER
// ============================================

app.post("/checkout", async (req, res) => {
  try {
    const data = parseCheckoutRequest(req.body);
    const userId = normalizeUserId(data.userId);
    const idempotencyKey = req.get("Idempotency-Key");

    if (!userId || !idempotencyKey) {
      throw new HttpException(400, "userId y Idempotency-Key requeridos");
    }

    // Verificar si ya existe este intento de checkout (idempotencia)
    const existing = await run(
      supabase
        .from("checkout_attempts")
        .select("*")
        .eq("idempotency_key", idempotencyKey)
    );

    if (existing && existing.length > 0) {
      const currentAttempt = existing[0];
      throw new HttpException(409, {
        message: "Intento duplicado",
        orderId: currentAttempt.order_id ?? null,
        status: "DUPLICATED_ORDER",
      });
    }

    // Obtener carrito
    const cartData = await run(
      supabase
        .from("carts")
        .select("*")
        .eq("user_id", userId)
        .eq("status", "ACTIVE")
    );

    if (!cartData || cartData.length === 0) {
      throw new HttpException(404, "Cart not found");
    }

    const cart = cartData[0];
    const cartId = cart.id;

    // Verificar que el carrito tenga items
    const items = await run(
      supabase.from("cart_items").select("*").eq("cart_id", cartId)
    );
    if (!items || items.length === 0) {
      throw new HttpException(400, "Carrito vacío");
    }

    const totalAmount = items.reduce((acc, item) => acc + item.subtotal, 0);

    // Registrar intento antes de llamar a G5
    await run(
      supabase.from("checkout_attempts").insert({
        cart_id: cartId,
        idempotency_key: idempotencyKey,
        status: "PENDING",
      })
    );

    // Marcar carrito como CHECKED_OUT
    await run(
      supabase.from("carts").update({ status: "CHECKED_OUT" }).eq("id", cartId)
    );

    const g5Payload = buildG5OrderPayload(
      userId,
      cartId,
      items,
      totalAmount,
      idempotencyKey
    );
    const g5Response = await createOrderInG5(g5Payload);
    const orderId = g5Response.orderId || g5Response.order_id;

    if (!orderId) {
      await run(
        supabase.from("carts").update({ status: "ACTIVE" }).eq("id", cartId)
      );
      await run(
        supabase
          .from("checkout_attempts")
          .update({ status: "FAILED" })
          .eq("cart_id", cartId)
          .eq("idempotency_key", idempotencyKey)
      );
      throw new HttpException(500, "G5 no devolvió orderId");
    }

    await run(
      supabase
        .from("checkout_attempts")
        .update({ order_id: orderId, status: "SUCCESS" })
        .eq("cart_id", cartId)
        .eq("idempotency_key", idempotencyKey)
    );

    return res.status(201).json({
      orderId: orderId,
      status: "CREATED",
      totalAmount: totalAmount,
    });
  } catch (e) {
    return handleError(res, e);
  }
});

// ============================================
// MANEJO DE ERRORES CENTRALIZADO
// ============================================

function handleError(res, e) {
  if (e instanceof ValidationException) {
    return res
      .status(400)
      .json({ detail: "Solicitud inválida", errors: e.errors });
  }
  if (e instanceof HttpException) {
    return res.status(e.statusCode).json({ detail: e.detail });
  }
  // Cualquier otro error → 500
  return res.status(500).json({ detail: `Error: ${e.message}` });
}

// ============================================
// EJECUTAR SERVIDOR
// ============================================

const PORT = process.env.PORT || 8000;
app.listen(PORT, "0.0.0.0", () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;
