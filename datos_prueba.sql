-- Datos de prueba mínimos para validar carts, cart_items y checkout_attempts
-- Ejecutar en PostgreSQL/Supabase. Si ya existen estos UUIDs, ajustar o limpiar primero.

BEGIN;

INSERT INTO carts (id, user_id, status, created_at, updated_at)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'test-user-001',
    'ACTIVE',
    now(),
    now()
);

INSERT INTO cart_items (id, cart_id, product_id, quantity, unit_price, subtotal)
VALUES
(
    '22222222-2222-2222-2222-222222222221',
    '11111111-1111-1111-1111-111111111111',
    'product-001',
    2,
    15.50,
    31.00
),
(
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    'product-002',
    1,
    9.99,
    9.99
);

INSERT INTO checkout_attempts (id, cart_id, idempotency_key, order_id, status, created_at, updated_at)
VALUES (
    '33333333-3333-3333-3333-333333333333',
    '11111111-1111-1111-1111-111111111111',
    'idem-test-001',
    NULL,
    'PENDING',
    now(),
    now()
);

COMMIT;
