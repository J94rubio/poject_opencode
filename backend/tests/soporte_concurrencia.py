"""Soporte de las pruebas de concurrencia (tarea 5.1 de `aprobacion-reservas`).

`ejecutar_en_paralelo` lanza cada llamada en su propio hilo. Los hilos se
sincronizan con una barrera justo antes de ejecutar la llamada. La sesión de la
aplicación es por hilo (`scoped_session`) y toma su propia conexión del pool, de
modo que cada llamada usa una sesión y una conexión independientes; ambas se
liberan al terminar el hilo. Los engines los libera la fixture `app`.
"""

from threading import Barrier, Thread

from backend.app.extensions import db

ESPERA_MAXIMA = 60


def ejecutar_en_paralelo(app, llamadas):
    """Ejecuta las llamadas a la vez y devuelve sus resultados en el mismo orden.

    Si una llamada lanza una excepción, o un hilo no termina a tiempo, la
    utilidad la propaga: una prueba nunca pasa con una llamada sin resultado.
    """
    barrera = Barrier(len(llamadas), timeout=ESPERA_MAXIMA)
    resultados = [None] * len(llamadas)
    errores = []

    def _ejecutar(indice, llamada):
        try:
            with app.app_context():
                try:
                    barrera.wait()
                    resultados[indice] = llamada()
                finally:
                    db.session.remove()
        except BaseException as error:  # noqa: BLE001 (se relanza en el hilo principal)
            errores.append(error)

    hilos = [
        Thread(target=_ejecutar, args=(i, llamada), daemon=True)
        for i, llamada in enumerate(llamadas)
    ]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join(ESPERA_MAXIMA)

    if any(hilo.is_alive() for hilo in hilos):
        raise TimeoutError("Un hilo de la prueba de concurrencia no terminó a tiempo.")
    if errores:
        raise errores[0]
    return resultados
