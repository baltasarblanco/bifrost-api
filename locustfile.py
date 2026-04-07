from locust import HttpUser, task, between

class UsuarioBifrost(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def chequear_telemetria(self):
        self.client.get("/")

    @task(2)
    def listar_armaduras(self):
        self.client.get("/armaduras/")

    @task(1)
    def intentar_ruta_privada(self):
        with self.client.get("/ruta-privada", catch_response=True) as response:
            if response.status_code == 401:
                response.success()
            else:
                response.failure("¡La seguridad falló! Entró sin token.")
