cat > README.md << 'EOF'
# 🐍 Bifrost APIMotor

**B2B de gestión de activos y reservas** – Desarrollado con Python, FastAPI y PostgreSQL.

🧭 **Estado del Proyecto:** Semana 6/10 · ████████████░░░░░░░░ 60%  
🛡️ **Calidad:** 90% Code Coverage · Tests automatizados verificados.

---

### 📦 Descripción

Bifrost es el core de una infraestructura B2B diseñada para la gestión de recursos críticos en estudios de grabación. El proyecto prioriza la seguridad stateless, el aislamiento de datos y la resiliencia.

A diferencia de prototipos básicos, Bifrost implementa una arquitectura modular inspirada en Clean Architecture, separando la lógica de negocio, los esquemas de validación y los mecanismos de seguridad.

**Hito alcanzado (Semana 6):** Implementación completa de seguridad criptográfica y suite de tests de integración con bases de datos aisladas en memoria.

---

### 🏗️ Arquitectura Modular

El proyecto ha evolucionado de un monolito simple a una estructura de paquetes profesional:

- `app/api/` – Orquestación de endpoints y gestión de dependencias (inyección de dependencias de FastAPI).
- `app/core/` – Motor de seguridad, configuración global y lógica de tokens JWT.
- `app/models/` – Definición de esquemas relacionales (SQLAlchemy 2.0).
- `app/schemas/` – Contratos de datos y validación estricta (Pydantic V2).
- `tests/` – Suite de pruebas automatizadas con aislamiento mediante SQLite `:memory:`.

---

### ✅ Roadmap y Estado de Avance

| Hito                     | Categoría      | Estado | Nota                                                  |
|--------------------------|----------------|--------|-------------------------------------------------------|
| Persistencia SQL         | Infra          | ✅      | SQLAlchemy 2.0 + PostgreSQL/SQLite.                  |
| Identidad & Hashing      | Seguridad      | ✅      | Bcrypt (Passlib) con salting automático.             |
| Autenticación JWT        | Seguridad      | ✅      | Tokens stateless con expiración configurable.        |
| Modularización           | Arquitectura   | ✅      | Separación de concerns (Core, API, Schemas).         |
| Testing Suite            | Calidad        | ✅      | 90% Coverage alcanzado con Pytest.                   |
| Aislamiento de Tests     | Calidad        | ✅      | Overrides de dependencias y DB en RAM.               |
| Logic: Reservations      | Negocio        | ⏳      | Gestión de slots y prevención de overbooking.        |
| Concurrencia             | Negocio        | ⏳      | Bloqueos pesimistas para Race Conditions.            |
| Despliegue CI/CD         | DevOps         | ⏳      | GitHub Actions para validación de tests.             |

También como lista de tareas (GitHub style):

- [x] Persistencia SQL
- [x] Identidad & Hashing
- [x] Autenticación JWT
- [x] Modularización
- [x] Testing Suite
- [x] Aislamiento de Tests
- [ ] Logic: Reservations
- [ ] Concurrencia
- [ ] Despliegue CI/CD

---

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
