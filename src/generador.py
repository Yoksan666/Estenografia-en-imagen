from random import seed, shuffle, getrandbits

class Generador(object):

    def __init__(self, semilla):
        self._semilla = semilla
        seed(self._semilla)

    def establecerSemilla(self, semilla):
        self._semilla = semilla
        seed(self._semilla)

    def generarListaPosicionesAleatorias(self, numeroPixeles):
        posiciones = [i for i in range(numeroPixeles)]
        shuffle(posiciones)
        return posiciones

    def obtenerBitAleatorio(self):
        return str(getrandbits(1))