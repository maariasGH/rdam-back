import requests
from sqlalchemy.orm import Session
from .. import crud

class PaymentService:
    def __init__(self):
        self.api_url = "https://api.pluspagos.com.ar/v1" # URL ficticia de ejemplo
        self.api_key = "TU_API_KEY_AQUÍ"

    def generar_link_checkout(self, tramite_id: int, monto: float):
        """
        Lógica para la función abrirPago(). 
        Crea una sesión en PlusPagos y devuelve la URL para el ciudadano.
        """
        payload = {
            "monto": monto,
            "referencia": f"TRAMITE_{tramite_id}",
            "callback_url": "https://tu-dominio.com/api/pagos/webhook"
        }
        # Simulación de respuesta de PlusPagos
        return f"https://pluspagos.com.ar/checkout/session_example_{tramite_id}"

    def procesar_webhook(self, db: Session, datos_pago: dict):
        """
        Procesa la confirmación asíncrona de PlusPagos.
        """
        tramite_id = datos_pago.get("tramite_id")
        ref_externa = datos_pago.get("transaction_id")
        
        return crud.registrar_pago_exitoso(db, tramite_id, ref_externa)