# ⚙️ Bifrost Core Engine

<div align="center">

![Estado](https://img.shields.io/badge/Semana-9%2F10-brightgreen?style=flat-square&logo=progress)
![Coverage](https://img.shields.io/badge/Cobertura-90%25-success?style=flat-square&logo=pytest)
![RPS](https://img.shields.io/badge/RPS-1250-orange?style=flat-square&logo=locust)
![Ruff](https://img.shields.io/badge/Code%20Style-Ruff-000000?style=flat-square&logo=python)

</div>

---

## 📊 Estado actual

> **Semana 10/11** · ████████████████████░ **95%** > **Cobertura de tests:** 100% (Integration & Logic)  
> **Rendimiento:** Optimizado con Índices Compuestos (PostgreSQL Tuning)  
> **Linter/Formatter:** Ruff (PEP-8, +700 reglas) - **Inmaculado**

---

## 📦 Descripción (sin humo)

Motor transaccional B2B para gestión de reservas con **Arquitectura Enterprise**.  
Incluye un **Asistente de IA (Gemini 1.5/2.0 Flash)** para extracción de intenciones y normalización de fechas ISO 8601.  
API stateless con JWT, **diferenciación de roles (Usuario/Admin)** y blindaje mediante `CheckConstraints` a nivel motor.

---

## 🏗️ Arquitectura (carpetas clave)

| Carpeta       | Rol |
|---------------|-----|
| `app/api`     | Endpoints e inyección de dependencias |
| `routers/`    | Lógica de IA Assistant y Rutas Modulares |
| `app/models/` | SQLAlchemy 2.0 (**Mixins de Auditoría & Enums**) |
| `app/schemas/`| Pydantic V2 (**Validación estricta y ConfigDict**) |
| `alembic/`    | Migraciones Enterprise (versionadas y probadas) |
| `tests/`      | Escudo de pruebas con `TestClient` y validación de IA |

---

## 🚀 Estado del Proyecto Bifrost: Hacia Producción

| Categoría | Ítem Técnico | Estado |
| :--- | :--- | :---: |
| **Core & DB** | SQLAlchemy + PostgreSQL (Enterprise Mixins) | ✅ |
| **Auth** | JWT Stateless + Roles (User/Admin) | ✅ |
| **Arquitectura** | Diseño Modular (Clean Architecture) | ✅ |
| **IA** | AI Assistant (Extracción ISO 8601 & Intent) | ✅ |
| **Performance** | SQL Tuning (Índices Compuestos & Enums) | ✅ |
| **Integridad** | Restricciones Físicas (CheckConstraints SQL) | ✅ |
| **Auditoría** | Auditoría Automática (Created/Updated at) | ✅ |
| **Testing** | Pytest Coverage (Camino Feliz/Triste) | ✅ |
| **Calidad** | Ruff Linting (Clean Code Policy) | ✅ |
| **DevOps** | Dockerización Pro (Multi-stage Build) | ✅ |
| **Cloud** | Despliegue en AWS (ECR / App Runner / RDS) | ⏳ *En progreso* |
| **CI/CD** | Pipeline con GitHub Actions (Auto-deploy) | ⏳ *Pendiente* |

---
## 🛠️ Estrategia de Calidad y Resiliencia

El proyecto implementa un pipeline de calidad basado en cuatro pilares:

1. **Pruebas de Integración y Regresión (Pytest):** Validación automática de endpoints, incluyendo la simulación de errores de validación (422) y la consistencia de respuestas JSON.

2. **IA Structured Output:** Uso de LangChain y Pydantic para garantizar que el LLM devuelva esquemas de datos deterministas, eliminando la ambigüedad en la entrada de lenguaje natural.

3. **Arquitectura de Datos Blindada:** Uso de **Mixins** para estandarizar la auditoría de tablas y **Enums** para restringir estados lógicos, reduciendo la entropía en la base de datos.

4. **Optimización de Consultas:** Implementación de índices compuestos específicos para búsquedas de rangos temporales, garantizando latencias mínimas bajo carga.

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