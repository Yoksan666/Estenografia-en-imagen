import os.path
from sys import exit

class Utilidad(object):

    def __init__(self):
        self._delimitador = b":"
    
    def decimalBinario(self, canal):
        return "{0:08b}".format(canal)

    def binarioDecimal(self, canal):
        return int(canal, 2)

    def fusionarLSB(self, canal, bit):
        # Mezcla en el byte del canal el bit menos significativo
        return canal[:7] + bit

    def calcularBytesTotalesSecreto(self, rutaSecreto):

        # Numero de bytes de carga
        numeroBytesCarga = os.path.getsize(rutaSecreto)

        # Numero de bytes de cabecera
        nombreArchivo = os.path.basename(rutaSecreto)
        nombre, extension = os.path.splitext(nombreArchivo)
        
        # sin el "." de la extensión
        cabecera = (nombre + ":" + extension[1:] + ":" + str(numeroBytesCarga) + ":").encode()
        numeroBytesCabecera = len(cabecera)

        return (numeroBytesCabecera + numeroBytesCarga)

    def leerBytes(self, ruta):
        # Lee los bytes de un archivo, añade rutas y devuelve una cadena de bits

        # Nombre y extensión del archivo
        nombreArchivo = os.path.basename(ruta)
        nombre, extension = os.path.splitext(nombreArchivo)

        # Bytes del archivo
        tamañoBytes = os.path.getsize(ruta)

        # Abrir archivo en modo binario
        with open(ruta, "rb") as archivo:

            # Crear lista de cadenas de 8 bits de la cabecera
            cabecera = list((nombre + ":" + extension[1:] + ":" + str(tamañoBytes) + ":").encode())
            cabeceraListaBits = [self.decimalBinario(entero) for entero in cabecera]

            # Crear lista de cadenas de 8 bits de la carga
            cargaBytes = archivo.read()
            cargaListaEnteros = list(cargaBytes)
            cargaListaBits = [self.decimalBinario(entero) for entero in cargaListaEnteros]

        # Concatenar la cabecera y la carga, y unirlas en una sola cadena de bits
        return "".join(cabeceraListaBits + cargaListaBits)

    def convertirBytes(self, listaBits):
        # Convierte lista de cadenas de 8 bits en una sola cadena de bytes 

        # Agrupar la cadena de bits en lista de grupos de 8 bits
        bitsAgrupados = [listaBits[i:i+8] for i in range(0, len(listaBits), 8)]

        listaBytes = []

        for bit in bitsAgrupados:
            entero = self.binarioDecimal(bit)
            listaBytes.append(entero.to_bytes(1, byteorder="little"))

        return b"".join(listaBytes)

    def escribirBytes(self, bytes):
        # Escribe una cadena de bytes leida previamente, extrayendo la informacion del formato

        # Formato fichero extraído
        # | nombre | extension | tamaño | carga | --- |
        # Ej: gato:jpg:2257:\x01 ...... \x00

        try:
            # Extraer nombre archivo
            i = bytes.find(self._delimitador)
            nombre = bytes[:i].decode()

            bytes = bytes[i+1:]

            # Extraer la extension del archivo
            i = bytes.find(self._delimitador)
            extension = bytes[:i].decode()

            bytes = bytes[i+1:]

            # Extraer el tamaño
            i = bytes.find(self._delimitador)
            tamaño = bytes[:i].decode()

            bytes = bytes[i+1:]

            # Extraer carga útil
            carga = bytes[:int(tamaño)]

            # Guardamos el archivo
            nombreArchivo = nombre + "_oculto." + extension
            with open(nombreArchivo, "wb") as archivo:
                archivo.write(carga)

            return nombreArchivo
            
        except UnicodeDecodeError:
            print("Error: formato incompatible")
            exit(1)
