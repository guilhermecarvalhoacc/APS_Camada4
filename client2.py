import os
from enlace import *
import time
from funcoes import *

string_log = ""


serialName = "/dev/ttyVirtualS1"
path_img = 'img/boneco.png'

com1 = enlace(serialName)
com1.enable()


def sinal_para_desligar():
    payload = []
    header = [0]*10
    header[0] = 5
    header[1] = Id_client
    header[2] = Id_server
    pacote = cria_datagrama(payload, header)
    com1.sendData(pacote)


def desconectar():
    time.sleep(1)
    com1.disable()
    os._exit(os.EX_OK)
    print(f'Conexão encerrada')


def envia_handshake(pacote_hanshake):
    global string_log
    terminou_hs = False
    lista_hs = [int.from_bytes(i, 'big') for i in pacote_hanshake]
    instante_envio = get_current_time()
    msg_type = lista_hs[0]
    tamanho_msg_total = len(pacote_hanshake)
    envio_recebimento = 'envio'
    string_log += f'{instante_envio} / {envio_recebimento} / {msg_type} / {tamanho_msg_total}\n'
    print(f'string log: {string_log}')
    com1.sendData(pacote_hanshake)
    init_timer1 = time.time()
    init_timer2 = time.time()

    while not terminou_hs:
        while com1.rx.getBufferLen() == 0:
            timer1 = time.time() - init_timer1
            timer2 = time.time() - init_timer2

            if timer2 > 20:
                print(f'passou 20 segundo, desligando tudo')
                sinal_para_desligar()
                desconectar()

            elif timer1 > 5:
                enviar_novamente = input(
                    'nao recebi resposta do server, enviar handshake novamente? sim/nao? ')

                if enviar_novamente == 'sim':
                    # enviar handshake novamente
                    instante_envio = get_current_time()
                    string_log += f'{instante_envio} / {envio_recebimento} / {msg_type} / {tamanho_msg_total}\n'
                    com1.sendData(pacote_hanshake)
                    print(f'string log: {string_log}')

                    init_timer1 = time.time()
                else:
                    # shutdown
                    print('fazer funcao pra encerar, pq ele nao quer enviar de novo')

        header, tamanho_header = com1.getData(14)
        header = list(header)
        string_log += cria_log_msg_recebida(header)

        if header[0] == 2:
            terminou_hs = True
            print(f'Server pode receber os pacotes\n')
        else:
            print(f'Problema no hanshake')


def cria_log_msg_recebida(received_head):
    # escrevendo no log
    envio_recebimento = 'receb'
    tamanho_total = (len(received_head))
    instante_recebimento = get_current_time()
    msg_type = received_head[0]
    string_log = f'{instante_recebimento} / {envio_recebimento} / {msg_type} / {tamanho_total}\n'

    return string_log


def recebe_confirmacao_recebimento(pacote_enviar, last_sent_pkg, lista_pacotes):
    global string_log
    msg_type = ''
    last_successful_msg = ''

    timer1 = time.time()
    timer2 = time.time()

    while msg_type != 4 or last_successful_msg != last_sent_pkg:

        # loop até ter algo no buffer

        while com1.rx.getBufferLen() == 0:
            current_time = time.time()
            elapsed_timer1 = current_time - timer1
            elapsed_timer2 = current_time - timer2

            if elapsed_timer1 >= 20:
                print(
                    f'Tempo máximo excedido, avisando server desligamento...')

                sinal_para_desligar()
                time.sleep(1)
                desconectar()

            if elapsed_timer2 >= 5:
                print(f'5 segundos sem resposta, enviando novamente...')
                com1.sendData(pacote_enviar)
                string_log += cria_log_envio(pacote_enviar)
                timer2 = time.time()

        # header received
        received_head = com1.getData(14)[0]
        received_head = list(received_head)
        string_log += cria_log_msg_recebida(received_head)


        print(f'header recebido: {received_head}', end='')
        # get payload and eop

        msg_type = received_head[0]
        last_successful_msg = received_head[7]

        print(
            f'Tipo msg: {msg_type} | última com sucesso: {last_successful_msg}')

        if msg_type == 4:
            print(
                f'Server recebeu corretamente o pacote. Enviando o próximo')

        elif msg_type == 6:
            required_pkg = received_head[6] - 1
            print(
                f'Server nao recebeu corretamente. Solicitou o {required_pkg}...')
            pacote = lista_pacotes[required_pkg]
            com1.sendData(pacote)
            string_log += cria_log_envio(pacote)
            timer2 = time.time()


def salvar_log(self):
    with open('logs/log_client1.txt', 'a') as fd:
        fd.write(self.str_log)


def simulate_error(index_package, lista_pacotes, pacote):
    pacote_certo = pacote
    pacote = lista_pacotes[index_package+1]
    com1.sendData(pacote)
    package = pacote_certo
    print(f'simulando erro com pacote indice errado')


def main():
    global string_log
    try:
        # carrega img
        imagem = open(path_img, 'rb').read()
        # separa os payloads
        lista_payload = divide_pacotes(imagem)
        # criando pacotes com head, payload e eop
        lista_pacotes = cria_pacotes(lista_payload)

        # envia handshake
        handshake = cria_handshake(len(lista_payload))
        envia_handshake(handshake)

        # começar a enviar os pacotes
        init_timer1 = time.time()

        for i in range(len(lista_pacotes)):
            delta_time = time.time() - init_timer1
            last_sent_pkg = i + 1
            pacote_enviar = lista_pacotes[i]
            com1.sendData(pacote_enviar)
            str_log = cria_log_envio(pacote_enviar)
            string_log += str_log

            recebe_confirmacao_recebimento(
                pacote_enviar, last_sent_pkg, lista_pacotes)

        time.sleep(1)
        # Encerra comunicação
        print("-------------------------")
        print("Comunicação encerrada")
        print("-------------------------")
        cria_texto_client(string_log)
        com1.disable()

    except Exception as erro:
        print("ops! :-\\")
        print(erro)
        com1.disable()


def cria_log_envio(pacote_enviar_bytes):
    send_or_receive = 'envio'
    head_binario = list(pacote_enviar_bytes)[:10]
    head_int = [int.from_bytes(byte, 'big') for byte in head_binario]

    msg_type = head_int[0]
    total_pacotes = head_int[3]
    pacote_atual = head_int[4]

    str_event = f'{get_current_time()} / {send_or_receive} / {msg_type} / {len(pacote_enviar_bytes)} / {pacote_atual} / {total_pacotes} \n'

    return str_event


main()
