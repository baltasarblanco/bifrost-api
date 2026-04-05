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
