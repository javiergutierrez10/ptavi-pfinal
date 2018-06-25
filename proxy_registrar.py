#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""
import socket
import sys
from xml.sax.handler import ContentHandler
from xml.sax import make_parser
import time
import socketserver
import random
import os


def WriteinFile(fichlog, mensaje):
    # Escribe en el fichero de registro
    gmt = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time())) + ' '
    M = mensaje.split('\r\n')
    S = ' '.join(M)
    outfile = open(fichlog, 'a')
    outfile.write(gmt + S + '\n')
    outfile.close()


class XML_PR(ContentHandler):
    "Clase de manejo XML"

    def __init__(self):

        self.misdatos = {}

    def startElement(self, name, attrs):
        # Recoge los datos contenidos en las etiquetas
        dat_atrib = {}
        server = ['name', 'ip', 'puerto']
        database = ['path', 'passwdpath']
        log = ['path']
        etiquetas = {'server': server, 'database': database, 'log':
                     log}

        if name in etiquetas:
            for atributo in etiquetas[name]:
                if attrs.get(atributo, "") != "":
                    dat_atrib[atributo] = attrs.get(atributo, "")
            self.misdatos[name] = dat_atrib

    def get_tags(self):
        # Devuelve los datos del XML
        return self.misdatos


class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    clientes = []

    def handle(self):

        self.ExpiracionClientes()
        Autorizacion = False
        """
        handle method of the server class
        (all requests will be handled by this method)
        """
        line = self.rfile.read()
        mensaje = line.decode('utf-8')
        metodo = mensaje.split(' ')[0]

        if metodo == "REGISTER":
            opcion = mensaje.split(' ')[3]
            ip_cliente = self.client_address[0]
            puerto_cliente = self.client_address[1]
            print("El cliente con IP:" + str(ip_cliente) +
                  " y Puerto:" + str(puerto_cliente) + " nos manda:", mensaje)
            comprob = mensaje.split(" ")[-1]
            expir = int(opcion)
            name_cliente = line.decode('utf-8').split(':')[1]
            name_cliente = name_cliente.split(':')[0]
            try:
                comprobar = int(comprob)
            except ValueError:
                Autorizacion = True

            registertime = time.strftime("%Y%m%d%H%M%S",
                                         time.gmtime(time.time() + 3600))
            expiratime = time.strftime("%Y%m%d%H%M%S",
                                       time.gmtime(time.time() + 3600 + expir))
            puertoesccliente = mensaje.split(':')[2]
            puertoesccliente = puertoesccliente.split(' ')[0]
            cliente = [name_cliente, {"IP": ip_cliente,
                                      "Puerto": puertoesccliente,
                                      "Expires": expir,
                                      "Expiration": expiratime,
                                      "Register": registertime}]

            if len(self.clientes) == 0 and expir != 0 and not Autorizacion:
                numero = str(random.randint(1, 999999999999999999))
                aut = 'WWW Authenticate: Digest nonce="' + numero + '"'
                self.wfile.write(b"SIP/2.0 401 Unauthorized\r\n" +
                                 bytes(aut, 'utf-8'))
                WriteinFile(FicheroLog, "SIP/2.0 401 Unauthorized")
            elif len(self.clientes) == 0 and expir != 0 and Autorizacion:
                self.clientes.append(cliente)
                self.wfile.write(b"SIP/2.0 200 OK\r\n")
            elif len(self.clientes) != 0 and expir != 0 and Autorizacion:
                self.clientes.append(cliente)
                self.wfile.write(b"SIP/2.0 200 OK\r\n")
                WriteinFile(FicheroLog, "SIP/2.0 200 OK")
            elif len(self.clientes) != 0:
                for nombre in self.clientes:
                    if nombre[0] == name_cliente and expir != 0:
                        print("El cliente ya está registrado\r\n")
                        break
                    elif nombre[0] == name_cliente and expir == 0:
                        self.wfile.write(b"SIP/2.0 200 OK\r\n")
                        self.clientes.remove(nombre)
                        break
                    elif nombre[0] != name_cliente and expir != 0:
                        numero = str(random.randint(1, 999999999999999999))
                        aut = 'WWW Authenticate: Digest nonce="' + numero + '"'
                        self.wfile.write(b"SIP/2.0 401 Unauthorized\r\n" +
                                         bytes(aut, 'utf-8'))
                        WriteinFile(FicheroLog, "SIP/2.0 401 Unauthorized")
                        break

            print(self.clientes)

        elif metodo == "INVITE":
            opcion = mensaje.split(' ')[3]
            ip_cliente = self.client_address[0]
            puerto_cliente = self.client_address[1]
            print("El cliente con IP:" + str(ip_cliente) +
                  " y Puerto:" + str(puerto_cliente) + " nos manda:", mensaje)
            comprob = mensaje.split(" ")[-1]
            user = mensaje.split(":")[1]
            user = user.split(" ")[0]
            ipultinvite = mensaje.split(" ")[5]
            puertoultinvite = mensaje.split(" ")[9]
            userinclients = False
            for cliente in self.clientes:
                if user == cliente[0]:
                    userinclients = True
                    ipinvitado = cliente[1]["IP"]
                    puertoinvitado = cliente[1]["Puerto"]
                    with socket.socket(socket.AF_INET,
                                       socket.SOCK_DGRAM) as my_socket:
                        my_socket.setsockopt(socket.SOL_SOCKET,
                                             socket.SO_REUSEADDR, 1)
                        my_socket.connect((ipinvitado, int(puertoinvitado)))
                        print("Enviando:\r\n" + mensaje)
                        my_socket.send(bytes(mensaje, 'utf-8') + b'\r\n')
                        data = my_socket.recv(1024)
                        mensajeresp = data.decode('utf-8')
                        print("Recibido:")
                        print(mensajeresp)
                        print("Enviando:")
                        print(mensajeresp)
                    self.wfile.write(bytes(mensajeresp, 'utf-8'))
                    WriteinFile(FicheroLog, mensajeresp)
                    break
            if not userinclients:
                self.wfile.write(b"SIP/2.0 404 User Not Found\r\n")
                WriteinFile(FicheroLog, "SIP/2.0 404 User Not Found")
        elif metodo == "ACK":
            ip_cliente = self.client_address[0]
            puerto_cliente = self.client_address[1]
            print("El cliente con IP:" + str(ip_cliente) +
                  " y Puerto:" + str(puerto_cliente) + " nos manda:", mensaje)

            user = mensaje.split(":")[1]
            user = user.split(" ")[0]

            userinclients = False
            for cliente in self.clientes:
                if user == cliente[0]:
                    userinclients = True
                    ipinvitado = cliente[1]["IP"]
                    puertoinvitado = cliente[1]["Puerto"]
                    with socket.socket(socket.AF_INET,
                                       socket.SOCK_DGRAM) as my_socket:
                        my_socket.setsockopt(socket.SOL_SOCKET,
                                             socket.SO_REUSEADDR, 1)
                        my_socket.connect((ipinvitado, int(puertoinvitado)))
                        print("Enviando:\r\n" + mensaje)
                        my_socket.send(bytes(mensaje, 'utf-8') + b'\r\n')
                    break
            if not userinclients:
                self.wfile.write(b"SIP/2.0 404 User Not Found\r\n")
                WriteinFile(FicheroLog, "SIP/2.0 404 User Not Found")
        elif metodo == "BYE":
            ip_cliente = self.client_address[0]
            puerto_cliente = self.client_address[1]
            print("El cliente con IP:" + str(ip_cliente) +
                  " y Puerto:" + str(puerto_cliente) + " nos manda:", mensaje)

            user = mensaje.split(":")[1]
            user = user.split(" ")[0]

            userinclients = False
            for cliente in self.clientes:
                if user == cliente[0]:
                    userinclients = True
                    ipinvitado = cliente[1]["IP"]
                    puertoinvitado = cliente[1]["Puerto"]
                    with socket.socket(socket.AF_INET,
                                       socket.SOCK_DGRAM) as my_socket:
                        my_socket.setsockopt(socket.SOL_SOCKET,
                                             socket.SO_REUSEADDR, 1)
                        my_socket.connect((ipinvitado, int(puertoinvitado)))
                        print("Enviando:\r\n" + mensaje)
                        my_socket.send(bytes(mensaje, 'utf-8') + b'\r\n')
                        self.wfile.write(b"SIP/2.0 200 OK\r\n")
                    break
            if not userinclients:
                self.wfile.write(b"SIP/2.0 404 User Not Found\r\n")
                WriteinFile(FicheroLog, "SIP/2.0 404 User Not Found")

        elif metodo != "REGISTER" and metodo != "INVITE" and metodo != "BYE":
            self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n")
            WriteinFile(FicheroLog, "SIP/2.0 405 Method Not Allowed")
        else:
            self.wfile.write(b"SIP/2.0 400 Bad Request\r\n")
            WriteinFile(FicheroLog, "SIP/2.0 400 Bad Request")
    def ExpiracionClientes(self):
        gmt = time.strftime("%Y%m%d%H%M%S", time.gmtime(time.time() + 3600))
        for nombre in self.clientes:
            if nombre[1]["Expiration"] < gmt:
                print(nombre[1]["Expiration"])
                print(gmt)
                self.clientes.remove(nombre)


if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    try:
        parser = make_parser()
        cHandler = XML_PR()
        parser.setContentHandler(cHandler)
        parser.parse(open(sys.argv[1]))
        DatosPR_XML = cHandler.get_tags()
        NAME_PR = DatosPR_XML['server']['name']
        IP_PR = DatosPR_XML['server']['ip']
        PUERTO_PR = int(DatosPR_XML['server']['puerto'])
        FicheroLog = DatosPR_XML['log']['path']
        WriteinFile(FicheroLog, "Listening...")
    except IndexError:
        sys.exit("Usage: python3 uaserver.py config")
    except FileNotFoundError:
        sys.exit("El archivo: " + sys.argv[1] + " no existe")
    serv = socketserver.UDPServer((IP_PR, PUERTO_PR), SIPRegisterHandler)

    print("Server " + NAME_PR + " listening at port " + str(PUERTO_PR))
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finishing server proxy " + NAME_PR)
