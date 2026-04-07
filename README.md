cat > README.md << 'EOF'
# 🛡️ Project Bifrost - Core Engine

🧭 **Estado del Proyecto:** Semana 8/10 · ████████████████░░░░ 80%  
🛡️ **Calidad:** 90% Code Coverage · **Linter & Formatter:** Ruff (PEP-8 Standard).
🚀 **Performance:** +1,250 RPS (Requests Per Second) verificado con Locust.

---

### 📦 Descripción

Bifrost es el núcleo de una infraestructura B2B diseñada para la gestión de recursos críticos en entornos de alta demanda. El proyecto ha evolucionado de un prototipo de gestión a un **Motor Transaccional** robusto que garantiza la integridad de los datos mediante bloqueos pesimistas y arquitectura orientada a servicios.

**Hito alcanzado (Semana 8):** Implementación del motor de reservas con protección anti-overbooking, gestión de concurrencia mediante `SELECT FOR UPDATE` y auditoría de código con estándares industriales.

---

### 🏗️ Arquitectura de Grado Profesional

El sistema implementa una separación estricta de responsabilidades (*Separation of Concerns*):

- `app/api/` – Orquestación de endpoints, inyección de dependencias y lógica de rutas.
- `app/core/` – Seguridad criptográfica (Bcrypt), JWT y configuración centralizada.
- `app/models/` – Capa de persistencia con **SQLAlchemy 2.0** y modelos relacionales complejos.
- `app/schemas/` – Contratos de datos y validación de tipos estricta con **Pydantic V2**.
- `alembic/` – Gestión de migraciones de base de datos (Versionado de infraestructura).
- `tests/` – Suite de pruebas de integración con aislamiento total en memoria RAM.

---

### ✅ Roadmap y Estado de Avance

| Hito                     | Categoría      | Estado | Nota                                                  |
|--------------------------|----------------|--------|-------------------------------------------------------|
| Persistencia SQL         | Infra          | ✅      | SQLAlchemy 2.0 + PostgreSQL en Docker.               |
| Identidad & Hashing      | Seguridad      | ✅      | Bcrypt (Passlib) con salting automático.             |
| Autenticación JWT        | Seguridad      | ✅      | Tokens stateless para escalabilidad horizontal.      |
| Modularización           | Arquitectura   | ✅      | Clean Architecture (Core, API, Models, Schemas).     |
| Testing Suite            | Calidad        | ✅      | 90% Coverage alcanzado con Pytest.                   |
| Code Quality (Ruff)      | Calidad        | ✅      | Auditoría estática y formateo PEP-8 automático.      |
| Logic: Reservations      | Negocio        | ✅      | Motor de colisiones temporales ($O(1)$ complexity).  |
| Concurrencia (Locking)   | Negocio        | ✅      | **Pessimistic Locking** para evitar Race Conditions.  |
| Despliegue CI/CD         | DevOps         | ⏳      | GitHub Actions para validación automatizada.         |

---

### ⚡ Características Técnicas Destacadas

1. **Integridad Transaccional:** Uso de `with_for_update()` en PostgreSQL para garantizar que un recurso crítico no sea duplicado bajo condiciones de alta carga.
2. **Arquitectura Stateless:** Autenticación basada en JWT que permite al backend escalar sin necesidad de sesiones compartidas.
3. **Validación de Datos Dinámica:** Implementación de validadores en Pydantic para asegurar que la lógica de negocio (ej. fechas de fin > inicio) se cumpla antes de tocar la base de datos.
4. **Infraestructura como Código:** Contenerización completa con Docker y orquestación de migraciones con Alembic.

---

### 🛠️ Estrategia de Calidad y Resiliencia

El proyecto implementa un pipeline de calidad basado en tres pilares:

1. **Pruebas de Integración con Aislamiento (Pytest):** Se utiliza el patrón de *Dependency Injection* para sustituir la base de datos de producción por instancias efímeras en RAM durante los tests, garantizando idempotencia en cada ejecución.
2. **Auditoría Estática (Ruff):** El código es analizado por un motor escrito en Rust que verifica el cumplimiento de +700 reglas de estilo y seguridad (PEP-8, vulnerabilidades comunes, optimización de imports).
3. **Validación de Concurrencia:** Pruebas de estrés verifican que los bloqueos pesimistas (`FOR UPDATE`) gestionen correctamente las colisiones de datos sin generar *deadlocks* en el motor PostgreSQL.

## 🧪 Calidad de Código (Testing)

No aceptamos código que no pueda ser probado. La suite de tests actual garantiza la integridad del sistema en milisegundos.

### Ejecución de Tests y Cobertura

```bash
# Ejecutar todos los tests
pytest
```
```bash
# Generar reporte de cobertura detallado
pytest --cov=app tests/
```

## 🚀 Instalación y Uso Local

### 1. Entorno Virtual y Dependencias

```bash
python -m venv venv
source venv/bin/activate  # En Linux/macOS
pip install -r requirements.txt
```

### 2. Variables de Entorno
Crea un archivo .env basado en .env.example:

```bash
SECRET_KEY="tu_clave_secreta_para_jwt"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Ejecución en Desarrollo
```bash
uvicorn app.main:app --reload
```
Acceso a documentación interactiva: http://localhost:8000/docs

## 🛠️ Stack Tecnológico

- **Core:** Python 3.12+ / FastAPI.
- **Seguridad:** PyJWT / Passlib (Bcrypt).
- **Data:** SQLAlchemy 2.0 / Pydantic V2.
- **Testing:** Pytest / Pytest-Cov / HTTPX.
- **Infraestructura:** Docker / Docker Compose / PostgreSQL.

---

## 📫 Contacto e Ingeniería

Este proyecto es parte del portafolio técnico de **Baltasar Blanco**, enfocado en la construcción de sistemas distribuidos, seguros y altamente testeados.

- 💼 [LinkedIn](https://linkedin.com/in/baltasar-blanco)
- 📧 baltablanco9008@gmail.com

> *“In code we trust, the rest we test.”* 🛡️
