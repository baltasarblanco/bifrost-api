# ADR 0001 — JWT stateless con blacklist híbrida en Redis

## Status

Accepted — 2025-04-21

## Context

Bifrost es un motor transaccional B2B que expone una API REST. Cada
request autenticado debe identificar al usuario que lo realiza, de
forma segura y con latencia mínima.

Al definir la estrategia de autenticación, evaluamos tres opciones:

1. **Sesiones server-side con cookie**: el servidor mantiene estado
   por usuario en una DB o cache. Cada request hace un lookup.
2. **JWT puro stateless**: el token contiene el claim y se valida
   sólo con criptografía. Sin lookups por request.
3. **JWT + blacklist híbrida**: JWT firmado, pero los tokens revocados
   se guardan en Redis con TTL. Cada request autenticado valida firma
   + consulta Redis.

### Requisitos que importan

- **Escalabilidad horizontal**: el servicio debe correr en N réplicas
  detrás de un load balancer sin sticky sessions.
- **Latencia**: p95 del auth check < 5 ms.
- **Revocación inmediata**: si un usuario hace logout o reportamos un
  token comprometido, el acceso debe cortarse en segundos, no en los
  30 minutos que dura el token.
- **Simplicidad operacional**: minimizar componentes nuevos en la
  infraestructura.

### Trade-off central

JWT puro es stateless y escala perfecto, pero **no se puede revocar**.
Sesiones server-side tienen revocación trivial pero cada request paga
un DB lookup, y escalar horizontalmente con sesiones requiere cache
compartido (básicamente, Redis).

## Decision

Adoptamos **JWT firmado con claim `jti` (JWT ID, RFC 7519 §4.1.7)
más una blacklist en Redis**.

Detalles:

- Cada token incluye `sub` (email), `exp` (expiración) y `jti` (UUID v4
  único por token).
- La validación de cada request ocurre en este orden:
  1. Firma criptográfica (HS256 con `JWT_SECRET_KEY` de 32+ bytes).
  2. Expiración (`exp` > now).
  3. Blacklist lookup en Redis (`EXISTS blacklist:jti:{jti}`).
- En logout, el `jti` del token actual se agrega a la blacklist con
  TTL = tiempo restante del token. Redis auto-limpia vencidos.

Es el mismo patrón que usan Auth0, Stripe y Okta: aprovechan la
escalabilidad de JWT pero reintroducen control sobre revocación
con un lookup O(1) en cache distribuido.

## Consequences

### Positivas

- **Escala horizontalmente sin sticky sessions**: cualquier réplica
  puede validar cualquier token (la blacklist vive centralizada en Redis).
- **Revocación inmediata**: logout corta acceso en el próximo request,
  no al vencer el JWT.
- **Latencia predecible**: Redis `EXISTS` es O(1), típicamente < 1 ms.
- **Memoria acotada**: la blacklist sólo guarda tokens revocados vivos.
  Con TTL dinámico = tiempo restante del token, Redis auto-limpia.

### Negativas (costos aceptados)

- **Dependencia dura de Redis**: si Redis cae, no podemos validar
  revocaciones. Mitigación: fail-open (aceptamos tokens aunque el
  lookup falle) es aceptable para esta aplicación porque el riesgo
  máximo es aceptar un token revocado durante la caída, por un tiempo
  acotado al TTL del token.
- **Ya no somos "stateless puros"**: rompemos parcialmente el principio
  de Factor VI de 12-factor. Aceptamos este costo porque la revocación
  es un requisito duro de negocio, y la alternativa (sesiones) tiene
  el mismo estado pero peor escalabilidad.
- **+1 ms de latencia por request autenticado**: comparado con JWT
  puro. Es imperceptible para el usuario pero real en agregado.

### Alternativas consideradas y descartadas

- **Sesiones server-side**: descartada. Obligaría a pagar un DB lookup
  en cada request, no solo en validación de revocación. Degradaría
  throughput y agregaría acoplamiento con la DB principal.
- **JWT con TTL corto (5 min) + refresh token**: descartada para esta
  fase. Reduce ventana de exposición de tokens robados pero no da
  revocación inmediata. Es una optimización ortogonal que podemos
  agregar después.
- **JWE (tokens encriptados)**: fuera de scope. Usamos JWS (firmado,
  no encriptado) porque el contenido del token no es sensible
  (solo email y jti).

## References

- [RFC 7519 — JSON Web Token](https://datatracker.ietf.org/doc/html/rfc7519)
- [Auth0: Refresh Token Rotation and Blacklisting](https://auth0.com/docs/secure/tokens/refresh-tokens)
- [12-Factor App: Factor VI (Processes)](https://12factor.net/processes)
- Implementación: `app/core/token_blacklist.py`
- Tests: `tests/test_logout.py`