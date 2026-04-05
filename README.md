# Bifrost API

> *API comercial en construcción – Python, FastAPI, SQLite, Pytest*  
> 🧭 **Estado actual:** Semana 1 de 10 · CLI funcional, próximo hito: FastAPI

---

## 📦 Descripción

Bifrost es una API de reservas para estudios de grabación musical.  
Este proyecto es mi **portafolio de producto táctico** en Python, siguiendo un plan de 10 semanas con restricción de 18h/semana.

**Objetivo final (semana 10):**  
Sistema B2B con autenticación JWT, tests >70%, contenerización Docker, manejo de zonas horarias y bloqueos pesimistas (`SELECT FOR UPDATE`).

---

## ✅ Estado actual (semana 1)

| Hito | Estado | Nota |
|------|--------|------|
| Script CLI con `httpx` | ✅ | Consume API pública, maneja excepciones, logs |
| FastAPI + Swagger | ⏳ | Próximo paso |
| Persistencia | ⏳ | SQLite en semana 3 |
| Tests | ⏳ | Pytest en semana 6 |

> 🔥 **Último entregable:** CLI resiliente que consume `https://jsonplaceholder.typicode.com/posts` con timeouts y logs.

---

## 🚀 Cómo ejecutar el proyecto (ahora mismo)

### 1. Clonar y entrar
```bash
git clone https://github.com/baltasarblanco/bifrost-api.git
cd bifrost-api
```
### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
# o .\venv\Scripts\activate (Windows)
```
### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```
### 4. Ejecutar el script CLI (lo que funciona hoy)
```bash
python cli.py
```
Verás una lista de posts desde una API pública.

## 📁 Estructura actual (simple)
```text
bifrost-api/
├── cli.py              # Script CLI funcional
├── requirements.txt    # Dependencias (httpx, pytest, etc.)
├── tests/              # (próximamente)
└── README.md
```

## 🗺️ Roadmap (semanas restantes)

| Semana | Entregable |
|--------|------------|
| 2 | FastAPI + Pydantic (en memoria) |
| 3 | SQLite persistente |
| 4 | PostgreSQL + SQLAlchemy + Alembic |
| 5 | JWT authentication (fastapi-users) |
| 6 | Pytest asíncrono + cobertura >70% |
| 7 | Docker + docker‑compose + Makefile |
| 8-9 | Lógica de reservas + timezones |
| 10 | `SELECT FOR UPDATE` (bloqueo pesimista) |

## 🛠️ Tecnologías (actuales y planificadas)
Lenguaje: Python 3.12+

Cliente HTTP: httpx (asíncrono)

Web framework: FastAPI (próximamente)

Validación: Pydantic V2

Base de datos: SQLite → PostgreSQL

ORM: SQLAlchemy 2.0 + Alembic

Tests: Pytest + pytest-asyncio

Contenerización: Docker + Compose

Calidad: Ruff (linter)

## 📫 Créditos y contacto
Desarrollado por Baltasar Blanco como parte de su portafolio dual (Python táctico + Rust bare‑metal).

📧 baltablanco9008@gmail.com
📷 @baltasar_blanco