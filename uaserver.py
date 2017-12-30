#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
from xml.sax.handler import ContentHandler
from xml.sax import make_parser
import os
import time
        
class XML_UA(ContentHandler):
    "Clase de manejo XML"

    def __init__(self):

        self.misdatos = {}

    def startElement(self, name, attrs):
		"Recoge los datos contenidos en las etiquetas"
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
        "Devuelve los datos del XML"
        return self.misdatos

def WriteinFile(fichlog, mensaje):
    "Escribe en el fichero de registro"
    gmt = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time())) + ' '
    M = mensaje.split('\r\n')
    S = ' '.join(M)
    outfile = open(fichlog, 'a')
    outfile.write(gmt + S + '\n')
    outfile.close()

class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """

    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
        line = self.rfile.read()
        mensaje = line.decode('utf-8')
        method = mensaje.split(' ')[0]
        methods = ["INVITE", "BYE", "ACK"]
        if method in methods:
            if method == "INVITE":
                self.wfile.write(b"SIP/2.0 100 Trying\r\n")
                self.wfile.write(b"SIP/2.0 180 Ringing\r\n")
                self.wfile.write(b"SIP/2.0 200 OK\r\n")
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

        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            print("El cliente nos manda " + line.decode('utf-8'))
            line = self.rfile.read()
            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break

if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    try:
        fichero_audio = sys.argv[3]
        if not os.path.isfile(fichero_audio):
            sys.exit("No se encuentra el fichero de audio: " + fichero_audio)
        else:
            IP = sys.argv[1]
            PUERTO = int(sys.argv[2])
            serv = socketserver.UDPServer((IP, PUERTO), EchoHandler)
    except IndexError:
        sys.exit("Usage: python3 server.py IP puerto fichero_audio")

    print("Listening...")
    serv.serve_forever()
