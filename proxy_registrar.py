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

def WriteinFile(fichlog, mensaje):
    #Escribe en el fichero de registro
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
		#Recoge los datos contenidos en las etiquetas
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
        #Devuelve los datos del XML
        return self.misdatos
    
class SIPRegisterHandler(socketserver.DatagramRequestHandler):

    """
    Echo server class
    """
    clientes = {}

    def handle(self):

        Borrar_Cliente = False
        Autorizacion = False
        """
        handle method of the server class
        (all requests will be handled by this method)
        """
        line = self.rfile.read()
        mensaje = line.decode('utf-8')
        expires = int(mensaje.split(' ')[3])
        ip_cliente = self.client_address[0]
        puerto_cliente = self.client_address[1]
        print("El cliente con IP:" + str(ip_cliente) + " y Puerto:" + str(puerto_cliente) + " nos manda", mensaje)
        comprob = mensaje.split(" ")[-1]
        if line.decode('utf-8').split(' ')[0] == "REGISTER":
            name_cliente = line.decode('utf-8').split(' ')[1]
            try:
            	comprobar = int(comprob)
            except ValueError:
            	Autorizacion = True
            if len(self.clientes) == 0 and expires != 0 and not Autorizacion:
                numero = str(random.randint(1,999999999999999999))
                self.wfile.write(b"SIP/2.0 401 Unauthorized\r\nWWW Authenticate: Digest nonce=" + bytes('"' + numero + '"','utf-8'))
            elif len(self.clientes) == 0 and expires != 0 and Autorizacion:
            	self.clientes[name_cliente] = ip_cliente
            elif len(self.clientes) != 0:
                for nombre in self.clientes:
                    if name_cliente == nombre and expires != 0:
                        print("El cliente ya está registrado\r\n")
                        break
                    elif name_cliente == nombre and expires == 0:
                        Borrar_Cliente = True
                        break
                    elif name_cliente != nombre and expires != 0:
                        self.wfile.write(b"SIP/2.0 401 Unauthorized\r\n\r\n")  
                        break

        if Borrar_Cliente is True:
            del self.clientes[name_cliente]

        print(self.clientes)
          
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
	serv = socketserver.UDPServer((IP_PR, PUERTO_PR), 		SIPRegisterHandler)
	
	print("Server " + NAME_PR + " listening at port " + str(PUERTO_PR))
	try:      
		serv.serve_forever()
	except KeyboardInterrupt:
		print("Finishing server proxy " + NAME_PR)
