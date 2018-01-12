#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socket
import socketserver
import sys
from xml.sax.handler import ContentHandler
from xml.sax import make_parser
import os
import time
from proxy_registrar import WriteinFile


class XML_UA(ContentHandler):
    "Clase de manejo XML"

    def __init__(self):

        self.misdatos = {}

    def startElement(self, name, attrs):
        # Recoge los datos contenidos en las etiquetas
        dat_atrib = {}
        account = ['username', 'passwd']
        uaserver = ['ip', 'puerto']
        rtpaudio = ['puerto']
        regproxy = ['ip', 'puerto']
        log = ['path']
        audio = ['path']
        etiquetas = {'account': account, 'uaserver': uaserver, 'rtpaudio':
                     rtpaudio, 'regproxy': regproxy, 'log': log, 'audio':
                     audio}

        if name in etiquetas:
            for atributo in etiquetas[name]:
                if attrs.get(atributo, "") != "":
                    dat_atrib[atributo] = attrs.get(atributo, "")
            self.misdatos[name] = dat_atrib

    def get_tags(self):
        # Devuelve los datos del XML
        return self.misdatos


class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """

    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
        line = self.rfile.read()
        print("Recibido:")
        mensaje = line.decode('utf-8')
        print(mensaje)
        method = mensaje.split(' ')[0]
        methods = ["INVITE", "BYE", "ACK"]
        SIP_ANFI = mensaje.split('=')[2]
        SIP_ANFI = SIP_ANFI.split(' ')[0]
        if method in methods:
            if method == "INVITE":
                LINE = "SIP/2.0 100 Trying\r\n"
                LINE = LINE + "SIP/2.0 180 Ringing\r\n"
                LINE = LINE + "SIP/2.0 200 OK\r\n"
                LINE = LINE + "Content-Type: application/sdp\r\n"
                V = "v=0 \r\n"
                o = "o=" + SIP_SERVER + " " + str(IP_SERVER) + " \r\n"
                S = "s=misesion \r\n"
                T = "t=0 \r\n"
                M = "m=audio " + str(PUERTO_SERVER) + " RTP \r\n"
                LINE = LINE + V + o + S + T + M
                self.wfile.write(bytes(LINE, 'utf-8'))
                print("Enviando:\r\n" + LINE)
            elif method == "ACK":
                aEjecutar = "mp32rtp -i 127.0.0.1 -p 23032 < " + fichero_audio
                print("Vamos a ejecutar", aEjecutar)
                os.system(aEjecutar)
            else:
                self.wfile.write(b"SIP/2.0 200 OK\r\n")
        elif method not in methods:
            self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n")
        else:
            self.wfile.write(b"SIP/2.0 400 Bad Request\r\n")


if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    try:
        parser = make_parser()
        cHandler = XML_UA()
        parser.setContentHandler(cHandler)
        parser.parse(open(sys.argv[1]))
        DatosUA_XML = cHandler.get_tags()
        SIP_SERVER = DatosUA_XML['account']['username']
        PASSWORD_SERVER = DatosUA_XML['account']['passwd']
        IP_SERVER = DatosUA_XML['uaserver']['ip']
        PUERTO_SERVER = int(DatosUA_XML['uaserver']['puerto'])
        IP_PROXY = DatosUA_XML['regproxy']['ip']
        PUERTO_PROXY = int(DatosUA_XML['regproxy']['puerto'])
        FicheroLog = DatosUA_XML['log']['path']
        WriteinFile(FicheroLog, "Listening...")

    except IndexError:
        sys.exit("Usage: python3 uaserver.py config")
    except FileNotFoundError:
        sys.exit("El archivo: " + sys.argv[1] + " no existe")
    serv = socketserver.UDPServer((IP_SERVER, PUERTO_SERVER), 		EchoHandler)

    print("Listening...")

    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finishing servidor")
