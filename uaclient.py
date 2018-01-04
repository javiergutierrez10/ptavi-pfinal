#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor
"""
import socket
import sys
from xml.sax.handler import ContentHandler
from xml.sax import make_parser
from uaserver import WriteinFile
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

# Contenido que vamos a enviar
#LINE = METHOD + " sip:" + SIPNAME_SERVER + "@" + IP_SERVER + " SIP/2.0\r\n"

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
	my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	my_socket.connect((IP_PROXY, PUERTO_PROXY))

	print()
	if METHOD == "REGISTER":
		LINE = METHOD + " sip:" + SIP_CLIENT + ":" + PUERTO_CLIENT + 			" SIP/2.0\r\nExpires: " + OPCION
	
	WriteinFile(FicheroLog, "Sent to " + str(IP_PROXY) + ":" + str(PUERTO_PROXY) + ": " + LINE)
	print("Enviando: " + LINE)
	my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')

	data = my_socket.recv(1024)

	print("Recibido:", data.decode('utf-8'))

	if METHOD == "INVITE":
		LINE = "ACK sip:" + SIPNAME_SERVER + "@" + IP_SERVER + " SIP/2.0\r\n"
	
	my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
	print("Enviando: " + LINE)

	print("Terminando...")
	print("Fin.")
