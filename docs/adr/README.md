# Architecture Decision Records

Este directorio contiene las decisiones arquitectónicas significativas
del Proyecto Bifrost, documentadas siguiendo el formato
[Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).

Cada ADR captura:
- **Contexto**: el problema que estamos resolviendo.
- **Decisión**: qué elegimos hacer.
- **Consecuencias**: los trade-offs aceptados (bueno y malo).

## Índice

| # | Título | Estado |
|---|--------|--------|
| [0001](./0001-jwt-stateless-con-blacklist-hibrida.md) | JWT stateless con blacklist híbrida en Redis | Accepted |
| [0002](./0002-pessimistic-locking-para-reservas.md) | Pessimistic locking (`SELECT FOR UPDATE`) para reservas | Accepted |
| [0003](./0003-idempotency-key-strategy.md) | Idempotency keys con SHA-256 + Redis (patrón Stripe) | Accepted |

## ¿Cómo leer un ADR?

1. Empezá por el **Contexto**: entendés qué problema se estaba resolviendo.
2. Leé la **Decisión**: la elección en sí.
3. **Consequences** es la sección más importante — muestra que quien
   escribió el ADR pensó en lo que estaba aceptando, no solo en lo que
   estaba ganando.

## ¿Cuándo escribir un ADR?

Cuando una decisión:
- Es difícil de revertir.
- Tiene impacto en múltiples componentes.
- Un nuevo dev del equipo debería entender el "por qué" antes de tocar el código.
- Se tomó evaluando alternativas reales (no default obvio).