#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""
import socket
import sys
import os
from xml.sax.handler import ContentHandler
from xml.sax import make_parser
from proxy_registrar import WriteinFile
import uaserver
import time

try:
    METHOD = sys.argv[2]
    OPCION = sys.argv[3]
    parser = make_parser()
    cHandler = uaserver.XML_UA()
    parser.setContentHandler(cHandler)
    parser.parse(open(sys.argv[1]))
    DatosUA_XML = cHandler.get_tags()
    FicheroLog = DatosUA_XML['log']['path']
    WriteinFile(FicheroLog, "Starting....")
except IndexError:
    sys.exit("Usage: uaclient.py config metodo opcion")

SIP_CLIENT = DatosUA_XML['account']['username']
PASSWORD_CLIENT = DatosUA_XML['account']['passwd']
IP_CLIENT = DatosUA_XML['uaserver']['ip']
PUERTO_CLIENT = DatosUA_XML['uaserver']['puerto']
IP_PROXY = DatosUA_XML['regproxy']['ip']
PUERTO_PROXY = int(DatosUA_XML['regproxy']['puerto'])
PUERTO_RTP = int(DatosUA_XML['rtpaudio']['puerto'])
fichero_audio = DatosUA_XML['audio']['path']
IP_SERVER = "127.0.0.1"

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((IP_PROXY, PUERTO_PROXY))

    print()
    if METHOD == "REGISTER":
        LINE = METHOD + " sip:" + SIP_CLIENT + ":" + PUERTO_CLIENT
        LINE = LINE + " SIP/2.0\r\nExpires: " + OPCION
    elif METHOD == "INVITE":
        LINE = METHOD + " sip:" + OPCION + " SIP/2.0\r\n"
        LINE = LINE + "Content-Type: application/sdp\r\n"
        V = "v=0 \r\n"
        o = "o=" + SIP_CLIENT + " " + IP_CLIENT + " \r\n"
        S = "s=misesion \r\n"
        T = "t=0 \r\n"
        M = "m=audio " + str(PUERTO_RTP) + " RTP \r\n"
        LINE = LINE + V + o + S + T + M
    elif METHOD == "BYE":
        LINE = METHOD + " sip:" + OPCION + " SIP/2.0\r\n"
        os.system("killall mp32rtp 2> /dev/null")
    else:
        LINE = METHOD + " sip:" + SIP_CLIENT + ":" + PUERTO_CLIENT
        LINE = LINE + " SIP/2.0\r\nExpires: " + OPCION
    try:
        WriteinFile(FicheroLog, "Sent to " + str(IP_PROXY) + ":"
                    + str(PUERTO_PROXY) + ": " + LINE)
        print("Enviando:\r\n" + LINE)
        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')

        data = my_socket.recv(1024)
        print("Recibido:")
        mensajeresp = data.decode('utf-8')
        print(mensajeresp)

        correcto = "SIP/2.0 100 Trying\r\n"
        correcto += "SIP/2.0 180 Ringing\r\nSIP/2.0 200 OK\r\n"
        confirmacion = mensajeresp.split("Content")[0]
        if confirmacion == correcto:
            PUERTO_RTP_INVITADO = mensajeresp.split("m=audio ")[1]
            PUERTO_RTP_INVITADO = PUERTO_RTP_INVITADO.split(" ")[0]
            LINE = "ACK sip:" + OPCION + " SIP/2.0\r\n"
            print("Enviando:\r\n" + LINE)
            my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
            os.system("./mp32rtp -i " + IP_SERVER + " -p" + 
                        PUERTO_RTP_INVITADO + " < " + fichero_audio)
            print('Starting rtp transmission...')
    except ConnectionRefusedError:
        WriteinFile(FicheroLog, "Error: No server listening at " +
                    IP_PROXY + "port " + str(PUERTO_PROXY))
        sys.exit("\r\nError: No server listening")
# Esperamos respuesta

    if METHOD == "REGISTER" and mensajeresp.split(" ")[1] == "401":
        WriteinFile(FicheroLog, "Received from " + str(IP_PROXY) + ":" +
                    str(PUERTO_PROXY) + " SIP/2.0 401 Unauthorized")

        numero = mensajeresp.split('"')[1]
        autorizacion = " \r\nAuthorization: Digest response="
        autorizacion = autorizacion + '"' + str(numero) + '"'
        LINE = LINE + autorizacion
        print("Enviando:\r\n" + LINE)
        my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
        data = my_socket.recv(1024)
        print("Recibido:")
        mensajeresp = data.decode('utf-8')
        print(mensajeresp)
    elif METHOD == "INVITE":
        data = my_socket.recv(1024)
        print("Transmisión RTP finalizada")

    print("Terminando...")
    print("Fin.")
