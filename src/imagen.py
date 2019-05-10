from math import ceil
from os.path import getsize, exists, splitext, basename
from sys import exit

from PIL import Image as imgPil
from utilidad import Utilidad
from generador import Generador

class Imagen(object):

    def __init__(self, rutaVector, semilla):

        self.rutaVector = rutaVector

        self.imagenPIL = None
        self.tipo = None
        self.modo = None
        self.pixelesVector = None

        self.formatosSoportados = ["PNG", "TIFF", "TIF", "BMP", "ICO"]
        self.modosSoportados = ["L", "RGB", "RGBA"]

        self.utilidad = Utilidad()
        self.__semilla = semilla
        self.__generador = Generador(self.__semilla)

        self.__analizarImagen()

        self._ruido = False

    def establecerRuido(self, añadirRuido):
        self._ruido = añadirRuido
    
    def __analizarImagen(self):
        try:
            self.imagenPIL = imgPil.open(self.rutaVector)

            self.tipo = self.rutaVector.split(".")[-1]

            if self.tipo.upper() not in self.formatosSoportados:
                print("Error: Formato", self.tipo.upper(), "no soportado")
                exit(0)

            self.modo = "".join(self.imagenPIL.getbands())
            
            self.numeroPixelesVector = self.imagenPIL.size[0] * self.imagenPIL.size[1]
        except Exception as e:
            print(e)

    def __calcularTamañoMaximoBytes(self, numeroPixelesVector, bitUsados, numeroCanales):
        bytesMaximos = (numeroPixelesVector * bitUsados * numeroCanales) // 8
        return bytesMaximos

    def __calcularNumeroPixelesNecesarios(self, numeroBytesTotales, bitUsados, numeroCanales):
        pixelesNecesarios = ceil((numeroBytesTotales * 8) / (bitUsados * numeroCanales))
        return pixelesNecesarios
    
    def __determinarNumeroCanales(self, modo):
        if self.modo == "1": return 1
        elif self.modo == "L": return 1
        elif self.modo == "RGB": return 3
        elif self.modo == "RGBA": return 4
        else: print("Error")

    def __determinarExtension(self, formato):
        
        formato = formato.lower()

        if formato in ["jpg", "jpeg"]:
            return "jpeg"
        elif formato in ["tif", "tiff"]:
            return "tiff"
        elif formato == "png":
            return "png"
        elif formato == "bmp":
            return "bmp"
        elif formato == "ico":
            return "ico"

    def enmascarar(self, rutaSecreto):

        if self.modo == "1":
            print("Modo:", self.modo, "no es posible enmascarar")
        elif self.modo in self.modosSoportados:
            self.__enmascarar(rutaSecreto)
        else:
            print("Modo:", self.modo, "no soportado")

    def __enmascarar(self, rutaSecreto):
        
        print("\nRuta vector:", self.rutaVector)
        print("Imagen vector:", self.imagenPIL.format, self.imagenPIL.size, self.imagenPIL.mode, "\n")

        # Obtener el tamaño del archivo a ocultar
        print("Ruta archivo:", rutaSecreto)
        numeroBytesSecreto = getsize(rutaSecreto)
        print("Tamaño secreto:", numeroBytesSecreto, "Bytes")

        # Obtener el tamaño total de la cabecera con el archivo a ocultar
        numeroBytesTotalesSecreto = self.utilidad.calcularBytesTotalesSecreto(rutaSecreto)
        print("Tamaño secreto (con cabecera):", numeroBytesTotalesSecreto, "Bytes\n")

        # Obtener el numero de canales en función del modo
        numeroCanales = self.__determinarNumeroCanales(self.imagenPIL.mode)

        # Bytes máximos teoricos que se pueden enmascarar
        bytesMaximos = self.__calcularTamañoMaximoBytes(self.numeroPixelesVector, 1, numeroCanales)
        print("Tamaño límite enmascarable:", bytesMaximos, "Bytes")

        # Número de píxeles necesarios = numero bits del secreto / numero de bits que caben por pixel
        pixelesNecesarios = self.__calcularNumeroPixelesNecesarios(numeroBytesTotalesSecreto, 1, numeroCanales)
        print("Píxeles necesarios para enmascarar:", pixelesNecesarios, "\n")

        # Si la imagen vector no tiene suficientes píxeles
        if numeroBytesTotalesSecreto > bytesMaximos:
            print("Error: El archivo secreto debe ser menor de", bytesMaximos, "bytes")
            exit(0)

        # Crear los mapas de píxeles para vector
        print("Cargando imagen vector")
        pixelesVector = self.imagenPIL.load()

        # Cargar mapa de bits del secreto
        print("Cargando mapa de bits del secreto")
        mapaBitsSecreto = self.utilidad.leerBytes(rutaSecreto)

        # Crear una nueva imagen resultante y cargar su mapa de bits
        print("Creado imagen resultante")
        imagenGenerada = imgPil.new(self.imagenPIL.mode, (self.imagenPIL.size[0], self.imagenPIL.size[1]), "black")
        print("Cargando imagen resultante\n")
        pixelesGenerada = imagenGenerada.load()

        # Posiciones de píxeles aleatorias
        posiciones = self.__generador.generarListaPosicionesAleatorias(self.numeroPixelesVector)
        # print("Posiciones aleatorias imagen vector =", len(posiciones))
        print("Semilla:", self.__semilla)
        print("Generando", self.numeroPixelesVector, "posiciones aleatorias")

        # Lista de posicones modificadas y sin modificar
        posicionesMezclado = posiciones[:pixelesNecesarios]
        posicionesRuido = posiciones[pixelesNecesarios:]

        # Mezclado y ruido píxeles
        print("Modificando píxeles")
        if self._ruido: print("Añadiendo ruido")
        self.__modificarPixeles((mapaBitsSecreto, posicionesMezclado, posicionesRuido, pixelesVector, pixelesGenerada))

        # Guardamos la imagen resultante
        nombreArchivo = basename(self.rutaVector)
        nom, _ = splitext(nombreArchivo)
        nombre = nom + "_vector." + self.__determinarExtension(self.imagenPIL.format)

        # Guardamos la imagen
        imagenGenerada.save(
            nombre,
            format = self.imagenPIL.format,
            mode = self.imagenPIL.mode,
            compress_level = 9
        )
        print("\nImagen resultante:", nombre, "\n")

    def __modificarPixeles(self, argumentos):
        if self.modo == "L":
            self.__modificarPixelesL(*argumentos)
        elif self.modo == "RGB":
            self.__modificarPixelesRGB(*argumentos)
        elif self.modo == "RGBA":
            self.__modificarPixelesRGBA(*argumentos)

    def __modificarPixelesL(self, mapaBitsSecreto, posicionesMezclado, posicionesRuido, pixelesVector, pixelesGenerada):

        # Iterador sobre la cadena de bits del archivo a enmascarar
        flujoBits = iter(mapaBitsSecreto)

        # Fase de mezclado pixeles
        for numeroPixelSecreto in posicionesMezclado:

            # Transformar la posición 1D del vector aplanado a 2D
            iVector = numeroPixelSecreto // self.imagenPIL.size[0]
            jVector = numeroPixelSecreto % self.imagenPIL.size[0]

            # Convertimos de decimal a binario el pixel
            pixelVectorBinario = self.utilidad.decimalBinario(pixelesVector[jVector, iVector])

            # Fusionamos el bit menos significativo
            l = self.utilidad.fusionarLSB(pixelVectorBinario, next(flujoBits))

            # Convertimos de binario a decimal el pixel
            pixelMezcladoBinario = (l)
            pixelesGenerada[jVector, iVector] = self.utilidad.binarioDecimal(pixelMezcladoBinario)

        self.__generador.establecerSemilla(None)

        if self._ruido:
            # Fase adición ruido
            for numeroPixelVectorRestante in posicionesRuido:

                # Transformar la posición 1D del vector aplanado a 2D
                iVector = numeroPixelVectorRestante // self.imagenPIL.size[0]
                jVector = numeroPixelVectorRestante % self.imagenPIL.size[0]

                pixelVectorBinario = self.utilidad.decimalBinario(pixelesVector[jVector, iVector])

                # Mezclar pixel del vector menos significativo aleatorio
                pixelMezcladoBinario = self.utilidad.fusionarLSB(pixelVectorBinario, self.__generador.obtenerBitAleatorio())

                # Ponemos el pixel generado en la imagen resultante
                pixelesGenerada[jVector, iVector] = self.utilidad.binarioDecimal(pixelMezcladoBinario)
        else:
            for numeroPixelVectorRestante in posicionesRuido:
                # Transformar la posición 1D del vector aplanado a 2D
                iVector = numeroPixelVectorRestante // self.imagenPIL.size[0]
                jVector = numeroPixelVectorRestante % self.imagenPIL.size[0]
                pixelesGenerada[jVector, iVector] = pixelesVector[jVector, iVector]

    def __modificarPixelesRGB(self, mapaBitsSecreto, posicionesMezclado, posicionesRuido, pixelesVector, pixelesGenerada):
        
        # Iterador sobre la cadena de bits del archivo a enmascarar
        flujoBits = iter(mapaBitsSecreto)

        # Fase de mezclado pixeles
        for numeroPixelSecreto in posicionesMezclado:

            # Transformar la posición 1D del vector aplanado a 2D
            iVector = numeroPixelSecreto // self.imagenPIL.size[0]
            jVector = numeroPixelSecreto % self.imagenPIL.size[0]

            # Convertimos de decimal a binario los canales del pixel
            pixelVectorBinario = (
                self.utilidad.decimalBinario(pixelesVector[jVector, iVector][0]),
                self.utilidad.decimalBinario(pixelesVector[jVector, iVector][1]),
                self.utilidad.decimalBinario(pixelesVector[jVector, iVector][2])
            )

            # Fusionamos el bit menos significativo
            try:
                r = self.utilidad.fusionarLSB(pixelVectorBinario[0], next(flujoBits))
                g = self.utilidad.fusionarLSB(pixelVectorBinario[1], next(flujoBits))
                b = self.utilidad.fusionarLSB(pixelVectorBinario[2], next(flujoBits))
            except StopIteration:
                b = pixelVectorBinario[2]

            # Convertimos de binario los canales del pixel
            pixelesGenerada[jVector, iVector] = (
                self.utilidad.binarioDecimal(r),
                self.utilidad.binarioDecimal(g),
                self.utilidad.binarioDecimal(b),
            )

        self.__generador.establecerSemilla(None)
        
        if self._ruido:
            # Fase adición ruido
            for numeroPixelVectorRestante in posicionesRuido:

                # Tranformar la posicion 1D del vector aplanado a 2D
                iVector = numeroPixelVectorRestante // self.imagenPIL.size[0] # formulas con ANCHO
                jVector = numeroPixelVectorRestante % self.imagenPIL.size[0]

                # Fase de añadido de ruido
                # Convertir tripleta de decimal a binario
                pixelVectorBinario = (
                    self.utilidad.decimalBinario(pixelesVector[jVector, iVector][0]),
                    self.utilidad.decimalBinario(pixelesVector[jVector, iVector][1]),
                    self.utilidad.decimalBinario(pixelesVector[jVector, iVector][2])
                )

                # Mezclar pixel del vector menos significativo aleatorio
                pixelMezcladoBinario = (
                    self.utilidad.fusionarLSB(pixelVectorBinario[0], self.__generador.obtenerBitAleatorio()),
                    self.utilidad.fusionarLSB(pixelVectorBinario[1], self.__generador.obtenerBitAleatorio()),
                    self.utilidad.fusionarLSB(pixelVectorBinario[2], self.__generador.obtenerBitAleatorio())
                )

                # Ponemos el pixel generado en la imagen resultante
                pixelesGenerada[jVector, iVector] = (
                    self.utilidad.binarioDecimal(pixelMezcladoBinario[0]),
                    self.utilidad.binarioDecimal(pixelMezcladoBinario[1]),
                    self.utilidad.binarioDecimal(pixelMezcladoBinario[2]),
                )
        else:
            for numeroPixelVectorRestante in posicionesRuido:
                # Transformar la posición 1D del vector aplanado a 2D
                iVector = numeroPixelVectorRestante // self.imagenPIL.size[0]
                jVector = numeroPixelVectorRestante % self.imagenPIL.size[0]
                pixelesGenerada[jVector, iVector] = pixelesVector[jVector, iVector]

    def __modificarPixelesRGBA(self, mapaBitsSecreto, posicionesMezclado, posicionesRuido, pixelesVector, pixelesGenerada):

        # Iterador sobre la cadena de bits del archivo a enmascarar
        flujoBits = iter(mapaBitsSecreto)

        for numeroPixelSecreto in posicionesMezclado:

            # Transformar la posición 1D del vector aplanado a 2D
            iVector = numeroPixelSecreto // self.imagenPIL.size[0]
            jVector = numeroPixelSecreto % self.imagenPIL.size[0]

            # print(pixelesVector[0, 0])

            # Convertimos de decimal a binario los canales del pixel
            pixelVectorBinario = (
                self.utilidad.decimalBinario(pixelesVector[jVector, iVector][0]),
                self.utilidad.decimalBinario(pixelesVector[jVector, iVector][1]),
                self.utilidad.decimalBinario(pixelesVector[jVector, iVector][2]),
                self.utilidad.decimalBinario(pixelesVector[jVector, iVector][3])
            )

            # Fusionamos el bit menos significativo
            r = self.utilidad.fusionarLSB(pixelVectorBinario[0], next(flujoBits))
            g = self.utilidad.fusionarLSB(pixelVectorBinario[1], next(flujoBits))
            b = self.utilidad.fusionarLSB(pixelVectorBinario[2], next(flujoBits))
            a = self.utilidad.fusionarLSB(pixelVectorBinario[3], next(flujoBits))

            # Ponemos el pixel generado en la imagen resultante
            pixelesGenerada[jVector, iVector] = (
                self.utilidad.binarioDecimal(r),
                self.utilidad.binarioDecimal(g),
                self.utilidad.binarioDecimal(b),
                self.utilidad.binarioDecimal(a),
            )

        self.__generador.establecerSemilla(None)
        
        if self._ruido:
            # Fase adición ruido
            for numeroPixelVectorRestante in posicionesRuido:

                # Tranformar la posicion 1D del vector aplanado a 2D
                iVector = numeroPixelVectorRestante // self.imagenPIL.size[0] # formulas con ANCHO
                jVector = numeroPixelVectorRestante % self.imagenPIL.size[0]
                
                # Fase de añadido de ruido
                # Convertir tripleta de decimal a binario
                pixelVectorBinario = (
                    self.utilidad.decimalBinario(pixelesVector[jVector, iVector][0]),
                    self.utilidad.decimalBinario(pixelesVector[jVector, iVector][1]),
                    self.utilidad.decimalBinario(pixelesVector[jVector, iVector][2]),
                    self.utilidad.decimalBinario(pixelesVector[jVector, iVector][3])
                )

                # Mezclar pixel del vector menos significativo aleatorio
                pixelMezcladoBinario = (
                    self.utilidad.fusionarLSB(pixelVectorBinario[0], self.__generador.obtenerBitAleatorio()),
                    self.utilidad.fusionarLSB(pixelVectorBinario[1], self.__generador.obtenerBitAleatorio()),
                    self.utilidad.fusionarLSB(pixelVectorBinario[2], self.__generador.obtenerBitAleatorio()),
                    self.utilidad.fusionarLSB(pixelVectorBinario[3], self.__generador.obtenerBitAleatorio())
                )

                # Ponemos el pixel generado en la imagen resultante
                pixelesGenerada[jVector, iVector] = (
                    self.utilidad.binarioDecimal(pixelMezcladoBinario[0]),
                    self.utilidad.binarioDecimal(pixelMezcladoBinario[1]),
                    self.utilidad.binarioDecimal(pixelMezcladoBinario[2]),
                    self.utilidad.binarioDecimal(pixelMezcladoBinario[3])
                )
        else:
            for numeroPixelVectorRestante in posicionesRuido:
                # Transformar la posición 1D del vector aplanado a 2D
                iVector = numeroPixelVectorRestante // self.imagenPIL.size[0]
                jVector = numeroPixelVectorRestante % self.imagenPIL.size[0]
                pixelesGenerada[jVector, iVector] = pixelesVector[jVector, iVector]

    def extraer(self):
        if self.modo == "1":
            print("No se puede")
        elif self.modo in self.modosSoportados:
            self.__extraer()
        else:
            print("Modo:", self.modo, "no soportado")

    def __extraer(self):

        # Cargar la imagen
        print("\nRuta vector:", self.rutaVector)
        print("Imagen vector:", self.imagenPIL.format, self.imagenPIL.size, self.imagenPIL.mode)

        # Crear el mapa de pixeles del vector
        print("Cargando imagen vector\n")
        pixelesVector = self.imagenPIL.load()
        
        # Posiciones de pixeles aleatorias (Generador)
        print("Semilla:", self.__semilla)
        print("Generando", self.numeroPixelesVector, "posiciones aleatorias\n")
        posiciones = self.__generador.generarListaPosicionesAleatorias(self.numeroPixelesVector)

        # Extrar bits enmascarados en la imagen vector
        print("Extrayendo bits")
        listaBits = self.__extraerBits((posiciones, pixelesVector))

        # Convertir cadena de bits a cadena de bytes
        print("Convirtiendo a bytes")
        bytes = self.utilidad.convertirBytes(listaBits)

        print("Cabecera:", bytes[:25], "\n")

        # Escribir los bytes resultantes
        nombre = self.utilidad.escribirBytes(bytes)
        print("Generando archivo:", nombre, "\n")

    def __extraerBits(self, argumentos):
        if self.modo == "L":
            return self.__extraerBitsL(*argumentos)
        elif self.modo == "RGB":
            return self.__extraerBitsRGB(*argumentos)
        elif self.modo == "RGBA":
            return self.__extraerBitsRGBA(*argumentos)

    def __extraerBitsL(self, posiciones, pixelesVector):

        listaBits = ""
        for numeroPixelSecreto in posiciones:

            iVector = numeroPixelSecreto // self.imagenPIL.size[0]
            jVector = numeroPixelSecreto % self.imagenPIL.size[0]

            pixelVectorBinario = self.utilidad.decimalBinario(pixelesVector[jVector, iVector])
            listaBits += pixelVectorBinario[-1]

        return listaBits

    def __extraerBitsRGB(self, posiciones, pixelesVector):

        listaBits = ""
        for numeroPixelSecreto in posiciones:

            iVector = numeroPixelSecreto // self.imagenPIL.size[0]
            jVector = numeroPixelSecreto % self.imagenPIL.size[0]

            pixelVectorBinario = (
                self.utilidad.decimalBinario(pixelesVector[jVector, iVector][0]),
                self.utilidad.decimalBinario(pixelesVector[jVector, iVector][1]),
                self.utilidad.decimalBinario(pixelesVector[jVector, iVector][2])
            )
            
            listaBits += pixelVectorBinario[0][-1]
            listaBits += pixelVectorBinario[1][-1]
            listaBits += pixelVectorBinario[2][-1]

        return listaBits

    def __extraerBitsRGBA(self, posiciones, pixelesVector):

        listaBits = ""
        for numeroPixelSecreto in posiciones:

            iVector = numeroPixelSecreto // self.imagenPIL.size[0]
            jVector = numeroPixelSecreto % self.imagenPIL.size[0]

            pixelVectorBinario = (
                self.utilidad.decimalBinario(pixelesVector[jVector, iVector][0]),
                self.utilidad.decimalBinario(pixelesVector[jVector, iVector][1]),
                self.utilidad.decimalBinario(pixelesVector[jVector, iVector][2]),
                self.utilidad.decimalBinario(pixelesVector[jVector, iVector][3])
            )
            
            listaBits += pixelVectorBinario[0][-1]
            listaBits += pixelVectorBinario[1][-1]
            listaBits += pixelVectorBinario[2][-1]
            listaBits += pixelVectorBinario[3][-1]

        return listaBits
