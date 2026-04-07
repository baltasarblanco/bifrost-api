# ⚙️ Bifrost Core Engine

<div align="center">

![Estado](https://img.shields.io/badge/Semana-8%2F10-blue?style=flat-square&logo=progress)
![Coverage](https://img.shields.io/badge/Cobertura-90%25-success?style=flat-square&logo=pytest)
![RPS](https://img.shields.io/badge/RPS-1250-orange?style=flat-square&logo=locust)
![Ruff](https://img.shields.io/badge/Code%20Style-Ruff-000000?style=flat-square&logo=python)

</div>

---

## 📊 Estado actual

> **Semana 8/10** · ████████████████░░░░ **80%**  
> **Cobertura de tests:** 90% (`pytest --cov`)  
> **Rendimiento:** 1250 RPS (Locust, 8 vCPUs / 16GB RAM)  
> **Linter/Formatter:** Ruff (PEP-8, +700 reglas)

---

## 📦 Descripción (sin humo)

Motor transaccional B2B para gestión de reservas con protección anti‑overbooking mediante `SELECT FOR UPDATE`.  
API stateless con JWT. Separación estricta de responsabilidades.

---

## 🏗️ Arquitectura (carpetas clave)

| Carpeta       | Rol |
|---------------|-----|
| `app/api`     | Endpoints, inyección de dependencias |
| `app/core`    | Seguridad, JWT, configuración |
| `app/models`  | SQLAlchemy 2.0 (modelos relacionales) |
| `app/schemas` | Pydantic V2 (validación de datos) |
| `alembic`     | Migraciones de base de datos |
| `tests`       | Tests de integración con DB en memoria RAM |

---

## ✅ Hitos cumplidos / pendientes

| Ítem                                      | Estado |
|-------------------------------------------|--------|
| SQLAlchemy + PostgreSQL                   | ✅     |
| Bcrypt hashing (salting automático)       | ✅     |
| JWT stateless                             | ✅     |
| Arquitectura modular (Clean Architecture) | ✅     |
| Pytest coverage 90%                       | ✅     |
| Ruff linting & formatting                 | ✅     |
| Motor de reservas (colisiones O(1))       | ✅     |
| Pessimistic locking (`FOR UPDATE`)        | ✅     |
| CI/CD con GitHub Actions                  | ⏳     |

---

## 🛠️ Estrategia de Calidad y Resiliencia

El proyecto implementa un pipeline de calidad basado en tres pilares:

1. **Pruebas de Integración con Aislamiento (Pytest):**  
   Se utiliza el patrón de *Dependency Injection* para sustituir la base de datos de producción por instancias efímeras en RAM durante los tests, garantizando idempotencia en cada ejecución.

2. **Auditoría Estática (Ruff):**  
   El código es analizado por un motor escrito en Rust que verifica el cumplimiento de +700 reglas de estilo y seguridad (PEP-8, vulnerabilidades comunes, optimización de imports).

3. **Validación de Concurrencia:**  
   Pruebas de estrés verifican que los bloqueos pesimistas (`FOR UPDATE`) gestionen correctamente las colisiones de datos sin generar *deadlocks* en el motor PostgreSQL.

---

## 🧪 Métricas y pruebas (lo que importa)

### Tests y cobertura

```bash
pytest                           # todos los tests
pytest --cov=app --cov-report=term tests/
```

## 📊 Pruebas de estrés (Locust)

```bash
locust -f locustfile.py --host=http://localhost:8000
```

Resultado verificado: 1250 RPS sostenidos en hardware de desarrollo (8 vCPUs, 16GB RAM). Sin errores de concurrencia.

### Concurrencia y bloqueos

Los tests lanzan reservas simultáneas para validar que `SELECT FOR UPDATE` evita overbooking.  
No se detectaron deadlocks en PostgreSQL 15.

### Calidad estática (Ruff)

```bash
ruff check .        # análisis estático (+700 reglas)
ruff format .       # formateo automático PEP-8
```

Configuración en pyproject.toml.

## 🚀 Instalación y uso local

### 1. Entorno virtual

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Variables de entorno (.env)

```bash
SECRET_KEY=clave_aleatoria_sin_frase_hecha
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Levantar PostgreSQL con Docker

```bash
docker run --name bifrost-db -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:15
alembic upgrade head
```

### 4. Ejecutar API
```bash
uvicorn app.main:app --reload
```

Documentación interactiva: http://localhost:8000/docs

## 🛠️ Stack técnico (versiones reales)

- Python 3.12
- FastAPI 0.115+
- SQLAlchemy 2.0
- Pydantic 2.5+
- PyJWT + Passlib (bcrypt)
- Pytest + pytest-cov + httpx
- Ruff 0.6+
- Locust 2.31+
- Docker + PostgreSQL 15

---

## 📫 Contacto

**Baltasar Blanco** – [baltablanco9008@gmail.com](mailto:baltablanco9008@gmail.com)  
💼 [LinkedIn](https://linkedin.com/in/baltasarblanco)

> *Código que no se puede probar no se acepta.*