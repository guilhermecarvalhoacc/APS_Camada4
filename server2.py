from enlace import *
import time
import os
import numpy as np
from funcoes import *

serialName = "/dev/ttyVirtualS0"
string_log = ""
com2 = enlace(serialName)
com2.enable()

server_id = 5
client_id = 10
pacote_id = 15
lista_payloads_recebidos = []
n_last_package_received = 0


def sinal_para_desligar():
    payload = []
    header = [0]*10
    header[0] = 5
    header[1] = Id_client
    header[2] = Id_server
    pacote = cria_datagrama(payload, header)
    com2.sendData(pacote)


def desconectar():
    time.sleep(1)
    com2.disable()
    os._exit(os.EX_OK)
    print(f'Conexão encerrada')

def salvar_log():
    return None


def recebe_header():
    r_header, len_r_header = com2.getData(10)

    return r_header, len_r_header


def recebe_handshake():
    terminou_handshake = False
    global string_log

    while not terminou_handshake:
        header, tamanho_header = com2.getData(14)
        header = list(header)
        string_log += cria_log_msg_recebida(header)
        total_pacotes_para_receber = header[3]
        print(f'header handshaeke: {header} ')

        if header[2] == server_id:
            if header[0] == 1:
                payload = []
                header = [0]*10
                header[0] = 2
                header[1] = client_id
                header[2] = server_id
                # pacote = cria_datagrama(payload, header)
                # com2.sendData(pacote)
                # terminou_handshake = True
                # lista_hs = [int.from_bytes(i, 'big') for i in pacote]
                # instante_envio = get_current_time()
                # msg_type = lista_hs[0]
                # tamanho_msg_total = len(pacote)
                # envio_recebimento = 'envio'
                # string_log += f'{instante_envio} / {envio_recebimento} / {msg_type} / {tamanho_msg_total}\n'
                # print(f'handshake enviado pro client')
            elif header[0] == 5:
                print("ENTROU NO ERRO ")
                cria_texto_server(string_log)
                desconectar()

        else:
            print(f'id errado do hanshake')

    return total_pacotes_para_receber


def recebe_imagem(quantidade_pacotes):
    global lista_payloads_recebidos
    global n_last_package_received
    numero_pacote_atual = 0
    global string_log

    while numero_pacote_atual < quantidade_pacotes:
        init_timer1 = time.time()
        init_timer2 = time.time()

        while com2.rx.getBufferLen() == 0:
            delta_timer1 = init_timer1 - time.time()
            delta_timer2 = init_timer2 - time.time()

            if delta_timer2 >= 20:
                print(f'passou 20 segundos, desligando...')
                payload = []

                header = [0]*10
                header[0] = 5
                header[1] = Id_client
                header[2] = Id_server
                pacote = cria_datagrama(payload, header)
                com2.sendData(pacote)
                lista_hs = [int.from_bytes(i, 'big') for i in pacote]
                instante_envio = get_current_time()
                msg_type = lista_hs[0]
                tamanho_msg_total = len(pacote)
                envio_recebimento = 'envio'
                string_log += f'{instante_envio} / {envio_recebimento} / {msg_type} / {tamanho_msg_total}\n'

            if delta_timer1 >= 5:
                print(
                    f'5 segundos sem resposta, enviando de novo...')
                #timer2 = time.time()

        # header received
        received_head = com2.getData(10)[0]
        received_head = list(received_head)
        print(f'header recebido: {received_head}', end='')
        # get payload and eop
        tamanho_pacote = 4
        msg_type = received_head[0]
        quantidade_pacotes = received_head[3]
        numero_pacote_atual = received_head[4]

        if msg_type == 3:
            payload_size = received_head[5]
            tamanho_pacote += payload_size

        if msg_type == 5:
            print(f'Código 5 - desligar...')
            desconectar()

        pacote_recebido, len_pacote_recebido = com2.getData(
            tamanho_pacote)
        string_log += f'{get_current_time()} / {"receb"} / {msg_type} / {tamanho_pacote + len(received_head)} / {numero_pacote_atual} / {quantidade_pacotes} \n'
        payload_recebido = pacote_recebido[:-4]
        eop_recebido = pacote_recebido[-4:]
        eop_certo = eop_recebido == b'\xff\xaa\xff\xaa'
        é_o_proximo = n_last_package_received + 1 == numero_pacote_atual

        # verifica eop e se é o proximo
        print(
            f'Received package [{numero_pacote_atual} / {quantidade_pacotes}]')
        pacote_deu_certo = eop_certo and é_o_proximo

        print(f'Pacote certo?  [{pacote_deu_certo}]', end=" | ")

        build_response(pacote_deu_certo, numero_pacote_atual, payload_recebido)

    print(f'Received all packages')
    # juntar os payloads em uma imagem
    juntar_imagem(lista_payloads_recebidos)


def juntar_imagem(lista_payloads_recebidos):
    imagem_recebida = b''.join(lista_payloads_recebidos)

    with open('img_recebida.png', 'wb') as file:
        file.write(imagem_recebida)

    print(f'salvando imagem\n')


def build_response(pacote_deu_certo, numero_pacote_atual, payload_recebido):
    global n_last_package_received
    global string_log
    payload = []
    lista_head = [0]*10

    if pacote_deu_certo:  # create type4  msg representing that the package was received successfully
        lista_payloads_recebidos.append(payload_recebido)
        print(f'package [{numero_pacote_atual}] received correctly')
        n_last_package_received = numero_pacote_atual
        lista_head[0] = 4  # mensagem to tipo 1 - handshake
        lista_head[1] = Id_client
        lista_head[2] = Id_server
        lista_head[7] = n_last_package_received
    else:
        print(
            f'package [{numero_pacote_atual}] had some error, requesting again..')
        lista_head[0] = 6  # mensagem to tipo 6 - solicitando reenvio
        lista_head[1] = Id_client
        lista_head[2] = Id_server
        lista_head[6] = n_last_package_received + 1

    pacote1 = cria_datagrama(payload, lista_head)
    # to simulate error (sem resposta do servidor)

    lista_hs = [int.from_bytes(i, 'big') for i in pacote1]
    instante_envio = get_current_time()
    msg_type = lista_hs[0]
    tamanho_msg_total = len(pacote1)
    envio_recebimento = 'envio'
    string_log += f'{instante_envio} / {envio_recebimento} / {msg_type} / {tamanho_msg_total}\n'

    com2.sendData(pacote1)


def main():
    print('server inicializado')
    # f = open(imageW, 'wb')
    # f.write(rxBuffer)

    total_pacotes_receber = recebe_handshake()

    print('terminou handshake, iniciando recepcao de pacotes')
    recebe_imagem(total_pacotes_receber)

    # Encerra comunicação
    print("-------------------------")
    print("Comunicação encerrada")
    print("-------------------------")
    cria_texto_server(string_log)
    com2.disable()


if __name__ == "__main__":
    main()
