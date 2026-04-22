# ADR 0002 — Pessimistic locking (`SELECT FOR UPDATE`) para reservas

## Status

Accepted — 2025-04-21

## Context

El endpoint `POST /reservas/` crea reservas sobre recursos finitos
(armaduras). El riesgo central es el **overbooking**: dos requests
concurrentes que reservan el mismo recurso para rangos de tiempo
solapados antes de que ninguno haya commiteado.

Este es el escenario clásico de **write-skew**: cada transacción lee
datos consistentes en su snapshot, decide que su escritura es segura,
y commitea — pero la unión de ambos commits viola el invariante de
negocio (*"una armadura no puede estar reservada dos veces al mismo
tiempo"*).

Ejemplo concreto:

```
Tiempo   Request A (Mark 85, 10:00-12:00)    Request B (Mark 85, 11:00-13:00)
------   --------------------------------    --------------------------------
t=0      SELECT WHERE modelo='Mark 85'
t=1      -> 0 colisiones                     SELECT WHERE modelo='Mark 85'
t=2                                          -> 0 colisiones
t=3      INSERT reserva 10-12
t=4      COMMIT                              INSERT reserva 11-13
t=5                                          COMMIT
                                             <- overbooking: 11-12 doble
```

Sin sincronización entre A y B, ambos ven "no hay colisión" en su
snapshot aislado y ambos insertan. Resultado: cliente doble-reservado,
llamada furiosa al soporte, refund, y potencialmente demanda legal
si el contexto es fintech.

### Requisitos

- **Cero overbooking bajo concurrencia alta**: en el stress test con
  Locust a 1700 RPS, 0 colisiones detectadas post-test.
- **Latencia p95 del endpoint < 150 ms** incluyendo el lock.
- **Compatibilidad con Postgres 15** (nuestra DB).
- **Simplicidad**: evitar componentes nuevos (Redis locks, etc.) si
  la DB ya ofrece la primitiva.

### Alternativas evaluadas

1. **Optimistic concurrency control (OCC)**: cada reserva incluye una
   columna `version`. Al commitear, se verifica que la versión sigue
   siendo la leída. Si cambió, se rechaza con 409 y el cliente reintenta.

2. **Pessimistic locking con `SELECT ... FOR UPDATE`**: al leer la fila
   de `armaduras`, Postgres pone un row-level lock que bloquea otras
   transacciones hasta el commit/rollback.

3. **Application-level distributed lock en Redis** (Redlock): usar
   `SET NX PX` antes de la transacción.

4. **Advisory locks de Postgres** (`pg_advisory_lock`): locks
   lightweight por nombre, fuera del MVCC.

## Decision

Adoptamos **pessimistic locking con `SELECT ... FOR UPDATE`** sobre
la fila de `armaduras` antes de detectar colisiones e insertar la
reserva.

Implementación en `app/api/endpoints.py`:

```python
armadura = db.query(models.ArmaduraDB).filter(
    models.ArmaduraDB.modelo == reserva_in.armadura_modelo
).with_for_update().first()
```

El lock se mantiene durante toda la transacción. Otros `SELECT FOR
UPDATE` sobre la misma fila se quedan esperando; `SELECT` normales
(ej. `GET /armaduras/disponibles`) siguen leyendo sin bloquearse
gracias al MVCC de Postgres.

## Consequences

### Positivas

- **Garantía fuerte de unicidad**: serializa el acceso al recurso
  contendido. Imposible overbooking por diseño, no por probabilidad.
- **Una sola primitiva, ya provista por Postgres**: no agregamos Redis
  locks, consenso distribuido, ni libs de concurrency. Menor superficie
  de bugs y de operación.
- **Integrado con MVCC**: los lectores normales (endpoints `GET`) no se
  bloquean. Solo competimos contra otros writers sobre la misma armadura.
- **Validado empíricamente**: el stress test Locust (1700 RPS sostenidos,
  10 minutos, scenario de reserva concurrente) reportó 0 overbookings.

### Negativas (costos aceptados)

- **Throughput limitado por armadura**: si 1000 requests compiten por
  la Mark 85 al mismo segundo, se serializan. No es problema para
  nuestro dominio (cada armadura reserva minutos/horas, no
  microsegundos), pero sería fatal en un sistema tipo banco.
- **Riesgo de deadlocks si la lógica crece**: si en el futuro una
  transacción lockea múltiples armaduras en distinto orden, podemos
  entrar en deadlock. Mitigación: orden de locks consistente (siempre
  por `modelo ASC`), timeout en la DB (`statement_timeout`).
- **Coupling fuerte con Postgres**: `SELECT FOR UPDATE` con semántica
  idéntica existe en MySQL/Oracle, pero cambiar a una DB sin soporte
  (ej. algún NoSQL) requeriría reescribir esta capa.
- **`nowait=True` descarta requests en vez de encolar**: ya lo configuramos
  así adrede — preferimos fallar rápido con 409 que mantener clientes
  esperando 30s en un lock. Trade-off válido para fintech UX.

### Alternativas descartadas

- **OCC (optimistic)**: descartada. Funciona bien cuando las colisiones
  son raras (< 1% de los writes), pero en nuestro caso el recurso
  contendido (una armadura popular en un rango popular) hace que las
  colisiones sean frecuentes. OCC nos dejaría reintentando sin parar
  en esos casos, y la UX de *"tuviste que reintentar 5 veces"* es peor
  que *"esperaste 30 ms en un lock"*.
- **Redis Redlock**: descartada. Agrega un componente distribuido donde
  Postgres ya ofrece la primitiva. Además, Redlock tiene problemas de
  corrección bajo network partitions documentados por Martin Kleppmann
  ("How to do distributed locking", 2016) — no vale la pena el riesgo
  para este caso.
- **Advisory locks**: descartada. Son lightweight pero operan fuera
  del MVCC y requieren gestión manual del lifecycle. Más complejidad
  que `SELECT FOR UPDATE` sin ventaja clara para nuestro caso.

## Validación empírica

El test de race condition corre con `locustfile.py`:

```
Concurrent users:  500
RPS sostenido:     1700
Duración:          10 min
Reservas creadas:  147.832
Overbookings:      0
p95 latency:       87 ms
```

Ver `locustfile.py` y el test `tests/test_reservas_concurrencia.py`.

## References

- [PostgreSQL Docs: Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html)
- [Martin Kleppmann: How to do distributed locking](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)
- [Write-skew anomaly — Designing Data-Intensive Applications, Ch.7](https://dataintensive.net/)
- Implementación: `app/api/endpoints.py`, función `crear_reserva`
- Stress test: `locustfile.py`