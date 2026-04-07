from locust import HttpUser, task, between

class UsuarioBifrost(HttpUser):
    # Simula el tiempo que tarda un humano real en leer la pantalla (entre 1 y 3 segundos)
    wait_time = between(1, 3)

    @task(3) # El peso "3" significa que esta tarea se ejecuta el triple de veces
    def chequear_telemetria(self):
        """Simula a un usuario entrando a la página principal"""
        self.client.get("/")

    @task(2)
    def listar_armaduras(self):
        """Simula a un usuario consultando la base de datos de armaduras"""
        self.client.get("/armaduras/")

    @task(1)
    def intentar_ruta_privada(self):
        """Simula a un usuario (sin token) intentando forzar la puerta VIP"""
        # Esperamos que esto devuelva un 401 Unauthorized, lo cual es un éxito de seguridad
        with self.client.get("/ruta-privada", catch_response=True) as response:
            if response.status_code == 401:
                response.success()
            else:
                response.failure("¡La seguridad falló! Entró sin token.")