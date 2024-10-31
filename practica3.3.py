
from tkinter import *
import random
import time
import threading
import os

# Listas y variables globales
personas = ['Jose', 'Carolina', 'Carlos', 'Juan']
operaciones = ['+', '-', '*', '/']
bloqueados = []  # Lista para procesos bloqueados con temporizador
espera = []  # Procesos en espera
ejecucion = None  # Proceso en ejecución
terminados = []  # Procesos terminados
excedentes = []  # Cola temporal para procesos esperando lugar en espera
lock = threading.Lock()  # Asegurar sincronización de pantalla

# Banderas de control
banderaI = False
banderaR = False
banderaB = False  # Bandera para procesos bloqueados
bloqueo_en_proceso = False  # Control de temporizadores de bloqueo

def res(num1, num2, operacion):
    if operacion == '+':
        return num1 + num2
    elif operacion == '-':
        return num1 - num2
    elif operacion == '*':
        return num1 * num2
    elif operacion == '/':
        return num1 / num2 if num2 != 0 else 'Inf'

def actualizar_reloj():
    tiempo_actual = time.strftime('%H:%M:%S')
    Reloj.config(text=f"Reloj Global: {tiempo_actual}")
    Reloj.after(1000, actualizar_reloj)

def actualizar_pantalla():
    with lock:
        # Limpiar ventanas de texto
        v1T.delete("1.0", END)
        v2.delete("1.0", END)
        v3.delete("1.0", END)
        bloqueadosT.delete("1.0", END)

        # Determina el espacio disponible para procesos en espera
        max_procesos = 7 - (1 if ejecucion else 0) - len(bloqueados)

        # Mostrar hasta max_procesos en espera
        for proceso in espera[:max_procesos]:
            proceso_id, pers, operacion, TME, tme_restante, _, _ = proceso
            v1T.insert(END, f'{proceso_id}. {pers}\n')
            v1T.insert(END, f'Operación: {operacion}\n')
            v1T.insert(END, f'TME: {TME}, TMRE: {tme_restante}\n\n')
            

        # Mostrar proceso en ejecución si existe
        if ejecucion:
            proceso_id, pers, operacion, TME, tme_restante, tmy_executed, resultado = ejecucion
            v2.insert(END, f'{proceso_id}. {pers}\n')
            v2.insert(END, f'Operación: {operacion}\n')
            v2.insert(END, f'TME: {TME}\nTMRE: {tme_restante}\nTMYE: {tmy_executed}\n')

        # Mostrar procesos bloqueados, máximo len(bloqueados)
        bloqueadosT.insert(END, "Procesos Bloqueados:\n")
        for proceso in bloqueados:
            proceso_id, pers, operacion, TME, tme_restante, tmy_executed, resultado, tiempo_bloqueo = proceso
            bloqueadosT.insert(END, f'{proceso_id}. {pers} - {operacion} - Bloqueo: {tiempo_bloqueo}\n')
            print(bloqueados)

        # Mostrar todos los procesos terminados
        for proceso in terminados:
            proceso_id, pers, operacion, TME, resultado = proceso
            v3.insert(END, f'{proceso_id}. {pers} - {operacion} = {resultado}\nTERMINADO\n\n')

    # Forzar actualización de la pantalla sin bloquear la interfaz
    w.update_idletasks()


def gestionar_procesos(numProcesos):
    global ejecucion, banderaR, banderaB
    actualizar_reloj()

    # Generar los procesos en espera inicialmente
    for i in range(numProcesos):
        pers = random.choice(personas)
        opera = random.choice(operaciones)
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        operacion = f'{num1}{opera}{num2}'
        resultado = res(num1, num2, opera)
        TME = random.randint(5, 13)
        if len(espera) + len(bloqueados) + (1 if ejecucion else 0) < 100:
            espera.append((i + 1, pers, operacion, TME, TME, 0, resultado))
        else:
            excedentes.append((i + 1, pers, operacion, TME, TME, 0, resultado))

    while espera or ejecucion or bloqueados or excedentes:
        if bloqueados and not bloqueo_en_proceso:
            threading.Thread(target=actualizar_temporizadores_bloqueo).start()

        # Solo toma un nuevo proceso de espera si ejecucion está vacío
        if not ejecucion and espera:
            ejecucion = espera.pop(0)  # Extrae solo el primer proceso en espera

        # Ejecutar el proceso actual si existe
        if ejecucion and len(ejecucion) == 7:
            proceso_id, pers, operacion, TME, tme_restante, tmy_executed, resultado = ejecucion
            while tme_restante > 0:
                tme_restante -= 1
                tmy_executed += 1
                ejecucion = (proceso_id, pers, operacion, TME, tme_restante, tmy_executed, resultado)
                time.sleep(1)
                actualizar_pantalla()

                # Manejo de procesos bloqueados y errores
                if banderaB:
                    banderaB = False
                    bloqueados.append((*ejecucion, 7))  # Añadir con tiempo de bloqueo
                    ejecucion = None
                    actualizar_pantalla()
                    break

                if banderaR:
                    banderaR = False
                    terminados.append((proceso_id, pers, operacion, TME, "ERROR"))
                    ejecucion = None
                    break

            # Si el proceso se completó sin interrupción ni error
            if tme_restante == 0 and not banderaR:
                terminados.append((proceso_id, pers, operacion, TME, resultado))
                ejecucion = None
        
        actualizar_pantalla()


interrumpidos = []  # Lista temporal para procesos interrumpidos

def INTERRUMPIR():
    global banderaI, ejecucion
    if ejecucion:
        interrumpidos.append(ejecucion[0])  # Mueve el proceso en ejecución a interrumpidos
        ejecucion.pop(0)
        print("Proceso interrumpido agregado a interrumpidos:", interrumpidos[-1])  # Mensaje de depuración
        ejecucion = None  # Limpia ejecucion para permitir que gestionar_procesos continúe
        banderaI = False  # Restablece la bandera
        actualizar_pantalla()  # Refleja el cambio en la interfaz



def ROMPER():
    global banderaR
    banderaR = True

def BLOQUEAR():
    global banderaB
    banderaB = True

def actualizar_temporizadores_bloqueo():
    global bloqueados, espera, bloqueo_en_proceso
    bloqueo_en_proceso = True
    while bloqueados:
        time.sleep(1)
        for i in range(len(bloqueados) - 1, -1, -1):
            proceso = bloqueados[i]
            if len(proceso) == 8:  # Ve que tenga 8 elementos
                proceso_id, pers, operacion, TME, tme_restante, tmy_executed, resultado, tiempo_bloqueo = proceso
                if tiempo_bloqueo > 0:
                    bloqueados[i] = (proceso_id, pers, operacion, TME, tme_restante, tmy_executed, resultado, tiempo_bloqueo - 1)
                    print(bloqueados)
                else:
                    # Calcula el índice para insertar desde 5 hasta 1, dependiendo del tamaño de `bloqueados`
                    indice_insercion = max(1, 6 - len(bloqueados))  # Asegura que esté entre 1 y 5
                    espera.insert(indice_insercion, bloqueados.pop(i)[:7])  # Inserta en la posición calculada
                    actualizar_pantalla()  # Actualiza la pantalla después de cada cambio
                    print(bloqueados)

                        

    bloqueo_en_proceso = False
def obtener(cadena="ropa.txt"):
    global terminados
    with open(cadena, 'w') as archivo:
        archivo.write("__________________________ Procesos Terminados ___________________________\n")

        tiempo_acumulado = 0  # Llevar el tiempo de finalización acumulativo
        tabla_filas = []  # Lista para almacenar las filas de la tabla

        # Variable para almacenar el tiempo de finalización del primer proceso
        tiempo_finalizacion_primero = None

        for i, proceso in enumerate(terminados):
            proceso_id, pers, operacion, TME, resultado = proceso
            
            # Tiempo solicitado
            tiempo_solicitado = int(TME)

            # Para el primer proceso, el tiempo de llegada es 0; para los siguientes, es el tiempo de finalización del primer proceso
            if i == 0:
                tiempo_llegada = 0
            elif i == 1:
                tiempo_llegada = 0
            elif i == 2:
                tiempo_llegada = 0
            elif i == 3:
                tiempo_llegada = 0
            elif i == 4:
                tiempo_llegada = 0
            elif i == 5:
                tiempo_llegada = 0
            elif i == 6:
                tiempo_llegada = 0
            elif i == 7:
                tiempo_llegada = tiempo_finalizacion_primero
            elif i == 8:
                tiempo_llegada = tiempo_finalizacion_seguns

            # Tiempo de espera es el tiempo que el proceso espera desde su llegada hasta que puede iniciar
            tiempo_espera = max(0, tiempo_acumulado - tiempo_llegada)

            # Tiempo de servicio es el tiempo solicitado
            tiempo_servicio = tiempo_solicitado

            # Tiempo de retorno es el tiempo total que el proceso permanece en el sistema (espera + servicio)
            tiempo_retorno = tiempo_espera + tiempo_servicio

            # Tiempo de finalización es cuando el proceso termina
            tiempo_finalizacion = tiempo_llegada + tiempo_retorno

            # Guardar el tiempo de finalización del primer proceso para los siguientes
            if i == 0:
                tiempo_finalizacion_primero = tiempo_finalizacion
            if i == 1:
                tiempo_finalizacion_seguns = tiempo_finalizacion


            # Actualizar tiempo acumulado para el siguiente proceso
            tiempo_acumulado = tiempo_finalizacion

            # Crear fila de la tabla
            fila = (proceso_id, tiempo_solicitado, tiempo_llegada, tiempo_espera, tiempo_servicio, tiempo_retorno, tiempo_finalizacion)
            tabla_filas.append(fila)

            # Escribir detalles de cada proceso en el archivo
            archivo.write(f"{proceso_id}. {pers}\n")
            archivo.write(f"{operacion} = {resultado}\n")
            archivo.write(f"Tiempo solicitado: {tiempo_solicitado}\n")
            archivo.write(f"Tiempo de llegada: {tiempo_llegada}\n")
            archivo.write(f"Tiempo de espera: {tiempo_espera}\n")
            archivo.write(f"Tiempo de servicio: {tiempo_servicio}\n")
            archivo.write(f"Tiempo de retorno: {tiempo_retorno}\n")
            archivo.write(f"Tiempo de finalizacion: {tiempo_finalizacion}\n")
            archivo.write("------------------------------------------------------\n")

        # Escribir encabezado de la tabla
        archivo.write("_____________________________________________________________________________\n")
        archivo.write("                             Tabla de tiempos                                \n")
        archivo.write("_____________________________________________________________________________\n")
        archivo.write("| N  | Solicitado | Llegada | Espera | Servicio | Retorno | Finalizacion |\n")
        archivo.write("|----|------------|---------|--------|----------|---------|--------------|\n")

        # Escribir todas las filas en formato de tabla
        for fila in tabla_filas:
            proceso_id, tiempo_solicitado, tiempo_llegada, tiempo_espera, tiempo_servicio, tiempo_retorno, tiempo_finalizacion = fila
            archivo.write(f"| {proceso_id:<3}| {tiempo_solicitado:<10}| {tiempo_llegada:<7}| {tiempo_espera:<6}| {tiempo_servicio:<8}| {tiempo_retorno:<7}| {tiempo_finalizacion:<12}|\n")

        archivo.write("_____________________________________________________________________________\n")

    print(f"Archivo {cadena} generado con éxito.")


def numProcesos():
    try:
        procesos = int(prT.get())
        threading.Thread(target=gestionar_procesos, args=(procesos,)).start()
    except ValueError:
        print("Ingresa un número válido")

# Configuración de la ventana principal
w = Tk()
w.geometry("600x500")
w.title("Simulación de Procesos")

pr = Label(w, text="# Procesos")
pr.place(x=10, y=5)
prT = Entry(w)
prT.place(x=75, y=5)

v1 = Label(w, text="EN ESPERA")
v1.place(x=60, y=35)

# Ajuste en la configuración de la ventana "EN ESPERA"
v1T = Text(w, height=25, width=20)  # Hacer la ventana más grande
v1T.place(x=15, y=60)




gen = Button(w, text="Generar", command=numProcesos)
gen.place(x=170, y=3)

v2T = Label(w, text="EJECUCIÓN")
v2T.place(x=245, y=110)
v2 = Text(w, height=6, width=20)
v2.place(x=210, y=135)

v3 = Text(w, height=15, width=20)
v3.place(x=405, y=60)
v3T = Label(w, text="TERMINADOS")
v3T.place(x=450, y=35)

Reloj = Label(w, text="Reloj Global")
Reloj.place(x=454, y=2)

InterrumpirB = Button(w, text="INTERRUMPIR", command=BLOQUEAR)
InterrumpirB.place(x=200, y=320)

RomperB = Button(w, text="ERROR", command=ROMPER)
RomperB.place(x=300, y=320)

BloquearB = Button(w, text="BLOQUEAR", command=BLOQUEAR)
BloquearB.place(x=240, y=350)

bloqueadosT = Text(w, height=5, width=40)
bloqueadosT.place(x=200, y=380)
bloqueadosT.insert(END, "No hay procesos bloqueados.\n")

ResB = Button(w, text="OBTENER RESULTADOS", command=obtener)
ResB.place(x=420, y=320)

w.mainloop()