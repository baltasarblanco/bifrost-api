# 🐍 Bifrost API

**Motor B2B de reservas en construcción** – Python, FastAPI, PostgreSQL, Docker

> 🧭 Progreso: Semana 2/10 · ████░░░░░░░░░░░░░░░░ 20%

---

## 📦 Descripción

Bifrost es el core de una API de reservas B2B para estudios de grabación musical.

Este proyecto nace de una filosofía pragmática: mientras experimento con infraestructura de bajo nivel en Rust 🦀, utilizo Python y FastAPI para maximizar la velocidad de iteración y mejorar el *Time-to-Market* del producto.

**Objetivo final (semana 10):**  
Sistema B2B robusto con autenticación JWT, tests >70%, orquestación completa con Docker, manejo estricto de zonas horarias (UTC) y prevención de race conditions mediante bloqueos pesimistas (`SELECT FOR UPDATE`).

---

## 🏗️ Arquitectura del Sistema

Orquestación local mediante Docker Compose aislando la API de la base de datos, con persistencia en volúmenes y gestión segura de secretos.

---

## ✅ Estado del Proyecto

| Hito | Estado | Nota |
|------|--------|------|
| CLI resiliente (`httpx`) | ✅ | Consume APIs, maneja excepciones y timeouts. |
| FastAPI + Swagger | ✅ | Endpoints base documentados automáticamente. |
| PostgreSQL + SQLAlchemy | ✅ | Motor de base de datos relacional configurado. |
| Migraciones (Alembic) | ✅ | Control de versiones del esquema de datos. |
| Infraestructura (Docker) | ✅ | Entorno 100% reproducible (Compose + Healthchecks). |
| Identidad y Seguridad | ✅ | Tabla de usuarios y hashing de contraseñas con Bcrypt. |
| Autenticación JWT | ⏳ | Próximo objetivo: Rutas protegidas y validación de tokens. |
| Reservas + Timezones | ⏳ | Lógica de negocio principal. |
| Concurrencia (Bloqueos) | ⏳ | Manejo de race conditions. |
| Pytest asíncrono | ⏳ | Cobertura >70%. |

🔥 **Estado actual:** *"Plomería" completada*. Base de datos blindada, secretos fuera del código (`.env`) y contenedores comunicándose por una red interna aislada.

---

## 🚀 Cómo ejecutar el proyecto localmente

Olvidate del *"funciona en mi máquina"*. El entorno está completamente contenerizado. Solo necesitás tener Docker instalado.

### 1. Clonar el repositorio

```bash
git clone https://github.com/baltasarblanco/bifrost-api.git
cd bifrost-api
```

### 2. Configurar variables de entorno
El proyecto usa un archivo .env para inyectar credenciales de forma segura. Existe una plantilla lista para usar:

```bash
cp .env.example .env
(Podés editar el .env si deseás cambiar el usuario o contraseña local de PostgreSQL).
```

### ###3. Levantar la infraestructura
Construimos la imagen de la API y levantamos la red junto a la base de datos:

```bash
sudo docker compose up -d --build
```
Nota: Si tu usuario está en el grupo docker, podés omitir sudo.

### 4. Construir las tablas (Migraciones)
Una vez que el contenedor de PostgreSQL esté saludable, ejecutamos Alembic para crear los esquemas:

```bash
alembic upgrade head
```

### 5. Probar la API
Ingresá a la documentación interactiva en tu navegador:
👉 http://localhost:8000/docs

## 📁 Estructura del Proyecto

```plaintext
bifrost-api/
├── alembic/            # Historial de migraciones de la DB
├── app/
│   ├── main.py         # Inicialización de FastAPI y rutas
│   ├── models.py       # Modelos relacionales de SQLAlchemy
│   ├── schemas.py      # Esquemas de validación de Pydantic V2
│   ├── security.py     # Motor criptográfico (Bcrypt / JWT)
│   └── database.py     # Motor de conexión a PostgreSQL
├── docs/               # Documentación y diagramas de arquitectura
├── .env.example        # Plantilla de secretos y configuración
├── docker-compose.yml  # Orquestación de servicios y red interna
├── Dockerfile          # Receta de construcción de la API
├── alembic.ini         # Configuración del gestor de migraciones
└── requirements.txt    # Dependencias de Python
```

## 🛠️ Stack Tecnológico

- **Lenguaje:** Python 3.12+
- **Framework Web:** FastAPI
- **Validación de Datos:** Pydantic V2
- **Base de Datos:** PostgreSQL 15
- **ORM & Migraciones:** SQLAlchemy 2.0 + Alembic
- **Seguridad:** Passlib (Bcrypt) + PyJWT
- **Infraestructura:** Docker + Docker Compose

## 📫 Créditos y contacto

Desarrollado por **Baltasar Blanco** como parte de un portafolio dual (Python pragmático + Rust de alto rendimiento).

- 📧 baltablanco9008@gmail.com
- 💼 [LinkedIn](https://linkedin.com/in/tu-perfil) *(Reemplazá por tu link real si querés)*
- 📷 @baltasar_blanco