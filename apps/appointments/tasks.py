import time
from celery import shared_task

@shared_task
def send_appointment_confirmation(appointment_id):
    """
    Simula el envío de un correo de confirmación de manera asíncrona.
    """
    # Simulamos el tiempo de red para enviar un email sin bloquear la API principal.
    time.sleep(2)
    print(f"[CELERY] ✉️ Correo de confirmación enviado exitosamente para la cita {appointment_id}")
    return True
