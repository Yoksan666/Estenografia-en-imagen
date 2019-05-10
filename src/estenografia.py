import argparse
from os.path import exists
from imagen import Imagen

def validarArchivo(parser, arg):
    if not exists(arg): parser.error("El archivo %s no existe" % arg)
    else: return arg

def main():

    # Parser de primer nivel
    parser = argparse.ArgumentParser(
        prog = "esteno.py",
        description="Herramienta de estenografía, sobre una imagen se oculta un archivo"
    )

    # Añadimos lista de subparsers
    subparsers = parser.add_subparsers(dest="comando")

    # Parser para el comando enmascarar
    parserEnmascarar = subparsers.add_parser("enmascarar", help="Enmascarar archivo secreto en una imagen vector")
    parserEnmascarar.add_argument("-v", "--vector", type=lambda x:validarArchivo(parser, x), required=True, help="Ruta de la imagen vector")
    parserEnmascarar.add_argument("-a", "--archivo", type=lambda x:validarArchivo(parser, x), help="Ruta del archivo secreto")
    parserEnmascarar.add_argument("-s","--semilla", type=int, default=10, help="Semilla de inicialiazción del generador")
    parserEnmascarar.add_argument("--ruido", default=False, action='store_true', help="Añadir ruido a los píxeles no modificados")

    # Parser para el comando extraer
    parserExtraer = subparsers.add_parser("extraer", help="Extraer archivo secreto de una imagen vector")
    parserExtraer.add_argument("-v", "--vector", type=lambda x:validarArchivo(parser, x), required=True, help="Ruta de la imagen vector")
    parserExtraer.add_argument("-s","--semilla", type=int, default=10, help="Semilla de inicialiazción del generador")

    # Obtener parámetros
    args = parser.parse_args()

    # Crear imagen estenográfica
    imagen = Imagen(args.vector, args.semilla)

    if args.comando == "enmascarar":
        imagen.establecerRuido(args.ruido)
        imagen.enmascarar(args.archivo)

    elif args.comando == "extraer":
        imagen.extraer()

if __name__ == "__main__":
	main()
