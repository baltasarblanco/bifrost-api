import requests


def obtener_datos_objetivo():
    print("[JARVIS] Iniciando conexión con base de datos externa...")

    url = "https://jsonplaceholder.typicode.com/users/1"
    respuesta = requests.get(url)
    datos = respuesta.json()

    print(f"[JARVIS] Enlace establecido. Analizando el objetivo: {datos['name']}")
    print(f"[JARVIS] Ubicación detectada: {datos['address']['city']}")

    # Envolvemos TODO lo que depende del dato peligroso
    try:
        nivel_acceso = datos["company"]["security_clearance"]
        # Este print solo se ejecuta si la línea de arriba funciona
        print(f"[JARVIS] Nivel de acceso del objetivo: {nivel_acceso}")
    except KeyError:
        # Si falla, saltamos directo acá
        print(
            "[JARVIS] ALERTA: La armadura no está lista. Dato de seguridad inexistente."
        )


if __name__ == "__main__":
    obtener_datos_objetivo()
    # Como el error fue manejado, el programa llega hasta acá sano y salvo
    print("[JARVIS] Sincronización completada con éxito.")
