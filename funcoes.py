
import math
from os import close, write
import numpy as np
from datetime import datetime


def cria_texto_server(string_log):
    f = open("logs/Server5.txt", "a+")
    f.write(string_log)
    f.close()


def cria_texto_client(string_log):
    f = open("logs/Client5.txt", "a+")
    f.write(string_log)
    f.close()


def cria_string(comunicando, tipo_msg, tamanho_bytes, pacote_enviado="", total_pacotes=""):
    tipo_msg_int = int.from_bytes(tipo_msg, byteorder="big")
    data = datetime.now()
    data_atual = f"{data.day}/{data.month}/{data.year} {data.hour}:{data.minute}:{data.second}/"

    if pacote_enviado == "":
        string = data_atual + \
            f"{comunicando}/ " + f"{tipo_msg_int}/ " + \
            f"{tamanho_bytes}/ " + f"{total_pacotes}/ "
    else:
        string = data_atual + f"{comunicando}/ " + f"{tipo_msg_int}/ " + \
            f"{tamanho_bytes}/ " + f"{pacote_enviado}/ " + f"{total_pacotes}/ "

    return string


def cria_string_int(comunicando, tipo_msg, tamanho_bytes, pacote_enviado="", total_pacotes=""):
    data = datetime.now()
    data_atual = f"{data.day}/{data.month}/{data.year} {data.hour}:{data.minute}:{data.second}/"

    if pacote_enviado == "":
        string = data_atual + \
            f"{comunicando}/ " + f"{tipo_msg}/ " + \
            f"{tamanho_bytes}/ " + f"{total_pacotes}/ "
    else:
        string = data_atual + f"{comunicando}/ " + f"{tipo_msg}/ " + \
            f"{tamanho_bytes}/ " + f"{pacote_enviado}/ " + f"{total_pacotes}/ "

    return string


def divide_pacotes(img):
    p = 114
    lista_payload = []

    for i in range(0, len(img), p):
        payload = img[i:i+p]
        lista_payload.append(payload)

    lista_payload_bytes = []

    for i in range(len(lista_payload)):
        lista_payload_bytes.append([])

        for char in lista_payload[i]:
            lista_payload_bytes[i].append(bytes([char]))

    return lista_payload_bytes


def cria_datagrama(payload, lista_head):
    EOP = [bytes([255]), bytes([170]), bytes([255]), bytes([170])]
    lista_head_bytes = [bytes([i]) for i in lista_head]
    datagrama = lista_head_bytes + payload + EOP

    return np.asarray(datagrama)


def cria_pacotes(lista_payload):
    lista_head = [0]*10

    lista_head[0] = 3
    lista_head[1] = Id_client
    lista_head[2] = Id_server
    lista_head[3] = len(lista_payload)

    lista_pacotes = []
    contador = 0

    for payload in lista_payload:
        lista_head[4] = contador + 1
        contador += 1
        lista_head[5] = len(payload)
        lista_pacotes.append(cria_datagrama(payload, lista_head))

    return lista_pacotes


Id_client = 10
Id_server = 5
Id_pacote = 15


def cria_handshake(numero_de_pacotes):
    lista_head = [0]*10
    lista_head[0] = 1
    lista_head[1] = Id_client
    lista_head[2] = Id_server
    lista_head[3] = numero_de_pacotes
    lista_head[4] = Id_pacote
    payload = []
    datagrama = cria_datagrama(payload, lista_head)

    return datagrama


def get_current_time():
    now = datetime.now()
    tempo = now.strftime("%d/%m/%Y %H:%M:%S.%f")[:-3]

    return tempo

def cria_log_msg_recebida(received_head):
    # escrevendo no log
    envio_recebimento = 'receb'
    tamanho_total = (len(received_head))
    instante_recebimento = get_current_time()
    msg_type = received_head[0]
    string_log = f'{instante_recebimento} / {envio_recebimento} / {msg_type} / {tamanho_total}\n'

    return string_log