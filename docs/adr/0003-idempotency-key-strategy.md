# ADR 0003 — Idempotency keys con SHA-256 + Redis (patrón Stripe)

## Status

Accepted — 2025-04-22

## Context

El endpoint `POST /reservas/` tiene side effects irreversibles
(inserts en DB, consumo de cuota de armaduras). En redes reales, los
clientes enfrentan situaciones donde **no saben si su request llegó**:

- Timeout del cliente antes de recibir respuesta.
- Conexión cortada a mitad de camino.
- Load balancer que devuelve 502 pero el request sí llegó al backend.
- Retry automático de SDKs cuando detectan fallas transitorias.

Sin protección, el cliente tiene dos opciones malas:

1. **No reintentar**: si el request sí se procesó pero la respuesta
   se perdió, el usuario cree que falló y el estado queda inconsistente.
2. **Reintentar ciego**: crea reservas duplicadas. En fintech sería
   doble cobro, doble transferencia, doble débito.

En industrias como pagos (Stripe, MercadoPago, Pomelo) y reservas
(Uber, Airbnb), esto se resuelve con el patrón **Idempotency Key**:
el cliente genera un UUID único por operación lógica y lo envía en
un header. El servidor garantiza que reintentos con el mismo key
producen el mismo efecto — una sola ejecución, misma respuesta.

### Requisitos

- **1 request lógico = 1 efecto de negocio**, aunque la red entregue
  N copias del mismo POST.
- **Retries idempotentes son seguros**: el cliente puede implementar
  reintentos agresivos sin miedo.
- **Protección contra replay attacks**: un atacante que captura un
  key legítimo no puede reusarlo con un body distinto.
- **Operación idempotent por contrato, no por accidente**: el cliente
  debe saber explícitamente que está enviando un key, no esperar
  que el servidor lo deduzca.
- **Sin acoplamiento con la lógica de negocio**: la feature se
  implementa lateralmente (dependency, cross-cutting concern).

### Alternativas evaluadas

1. **Idempotency key con lookup por clave**: el servidor guarda
   `key → response` en un store con TTL.
2. **Hash del request completo como key implícita**: deduplicar por
   "mismo payload = misma operación". Sin header.
3. **Unique constraint en DB**: derivar un identificador único desde
   el payload (ej. `user_id + fecha_inicio + armadura_modelo`) y poner
   constraint a nivel tabla.
4. **Distributed lock por operación**: lockear mientras se procesa un
   request, rechazar duplicados.

## Decision

Adoptamos **idempotency keys explícitos con body-hash, almacenados
en Redis con TTL de 24 horas**, siguiendo el patrón de Stripe.

### Contrato del endpoint

El cliente envía header `Idempotency-Key: <UUID v4>`. El servidor:

1. **Sin header → 400 Bad Request**. El endpoint exige idempotency
   explícito, no implícito.
2. **Key nuevo + body válido → procesa + cachea respuesta**. Cache
   bajo `idempotency:{endpoint}:{key}` con TTL 24h.
3. **Key repetido + mismo body → devuelve respuesta cached sin
   tocar DB**. Igualdad de body verificada por hash SHA-256.
4. **Key repetido + body distinto → 422 Unprocessable Entity**.
   Protección contra replay / bugs del cliente.

### Tres decisiones críticas de implementación

**1. Cache de éxitos Y errores**

Una implementación "ingenua" cachea solo 201. Eso abre un **agujero
de seguridad**: un atacante envía un primer request con el mismo
key pero body intencionalmente malformado (ej. campo faltante), recibe
error, el cache queda vacío, y en un segundo request con body
totalmente distinto el servidor procesa sin activar la validación
de body-hash.

Mitigación: cachear respuestas independientemente del status code.
Implementado con `try/except HTTPException` que persiste antes de
re-lanzar.

**2. TTL dinámico vs fijo**

Stripe usa 24h como default. Con 10M de usuarios activos/día y un
logout promedio cada 15 min, TTL fijo de 24h serían 960M de entries
vivos. Con TTL dinámico (el tiempo restante del token al momento
de revocar), la memoria es proporcional a *"lo que efectivamente
queda por vivir"*, no a *"lo peor posible"*. Reducción típica: 50-100x.

*(Nota: este punto aplica principalmente al sibling ADR 0001 sobre
JWT blacklist. Lo menciono acá para evidenciar el patrón general.)*

**3. SHA-256 del body raw, no del JSON parseado**

El hash se calcula sobre los **bytes exactos** del body HTTP, antes
de que Pydantic lo parsee. Razón: distintas serializaciones JSON
(espacios, orden de keys) producen distintos hashes aunque el
significado semántico sea el mismo. Queremos que el cliente que
envía exactamente los mismos bytes obtenga la misma respuesta; si
cambia un espacio, consideramos que "algo cambió" y validamos de
nuevo. Es más estricto que semántica JSON, y es lo que hace Stripe.

## Consequences

### Positivas

- **Cliente puede reintentar agresivamente**: retries automáticos de
  SDKs, manejo de timeouts del cliente, y recuperaciones de red son
  ahora seguros.
- **Protección contra replay attacks**: el hash del body bloquea la
  reutilización de un key capturado con payload distinto.
- **Fail-fast en inconsistencias del cliente**: si un cliente
  accidentalmente reutiliza un key (bug de SDK, UUID mal generado),
  el servidor lo detecta en el segundo request con 422.
- **Implementación lateral**: la feature vive en `app/core/idempotency.py`
  + una dependency FastAPI. El endpoint de `/reservas/` quedó limpio
  excepto por la dependency y el short-circuit en la primera línea.
- **O(1) lookup**: Redis `GET` típicamente < 1 ms.

### Negativas (costos aceptados)

- **+1 ms por request a `/reservas/`**: lookup a Redis incluso si el
  key es nuevo. Imperceptible para el usuario, real en agregado.
- **Dependencia dura de Redis**: si Redis cae, no podemos verificar
  idempotency. Decisión de contingencia: **rechazar el request con
  503** en ese caso (no fail-open como en blacklist). Procesar sin
  idempotency bajo falla de Redis comprometería la garantía principal.
- **Memoria en Redis**: cada entry guarda `status_code + body + body_hash`.
  Con TTL 24h y 100k reservas/día → ~24h × 100k × ~500 bytes = ~1.2 GB.
  Aceptable para nuestro cluster Redis actual, planificable con
  crecimiento.
- **Cliente debe generar UUIDs correctamente**: clientes que reutilicen
  keys sin querer van a ver 422s confusos. Mitigación: documentación
  clara en OpenAPI + ejemplos en el SDK público.

### Alternativas descartadas

- **Hash del request sin header explícito**: descartada. Hace
  idempotency implícita, lo cual causa el bug clásico donde un cliente
  que quiere hacer 2 reservas idénticas (ej. 2 usuarios pidiendo la
  misma armadura en momentos muy cercanos, bug del cliente enviando
  2 veces el mismo body) termina recibiendo solo 1. Stripe explícitamente
  no hace esto — el cliente siempre declara intención con un key único.
- **Unique constraint en DB**: descartada como solución primaria.
  Útil como red de seguridad final, pero:
  (a) No cubre casos donde el key identifica operaciones distintas
      que casualmente tienen mismo payload.
  (b) El cliente no recibe la respuesta original (recibe 409 genérico
      sin detalle).
  (c) Nos encadena al esquema de negocio: cada nueva operación requeriría
      pensar qué tupla de columnas es "única".
- **Distributed lock**: descartada. Protege contra concurrencia
  (útil en otros contextos) pero no contra reintentos *secuenciales*
  (que son el 95% del caso). Además, locks introducen la posibilidad
  de deadlock y requieren tuning de timeout.

## Lecciones aprendidas durante la implementación

### Bug que detecté en smoke test

La primera versión cacheaba solo respuestas 201. Mi propio test manual
descubrió el hueco de replay: primer request con body malformado →
error, cache vacío; segundo request con key repetido y body distinto
→ procesa sin validar body-hash. La corrección (cachear errores también)
está documentada en el código y es parte del patrón Stripe oficial.

Moraleja: **idempotency parcial (solo éxitos) es peor que ausencia de
idempotency**. La ausencia de cache no es un estado neutral — es un
estado explotable.

## References

- [Stripe: Idempotent requests](https://stripe.com/docs/api/idempotent_requests)
- [IETF draft: The Idempotency-Key HTTP Header Field](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header)
- [Brandur Leach: Implementing Stripe-like Idempotency Keys in Postgres](https://brandur.org/idempotency-keys)
- Implementación: `app/core/idempotency.py`, `app/api/dependencies.py`,
  `app/api/endpoints.py::crear_reserva`
- Tests: `tests/test_idempotency.py`