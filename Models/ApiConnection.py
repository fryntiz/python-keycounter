#!/usr/bin/python3
# -*- encoding: utf-8 -*-

# @author     Raúl Caro Pastorino
# @email      dev@fryntiz.es
# @web        https://fryntiz.es
# @gitlab     https://gitlab.com/fryntiz
# @github     https://github.com/fryntiz
# @twitter    https://twitter.com/fryntiz
# @telegram   https://t.me/fryntiz

# Create Date: 2020
# Project Name:
# Description:
#
# Dependencies:
#
# Revision 0.01 - File Created
# Additional Comments:

# @copyright  Copyright © 2020 Raúl Caro Pastorino
# @license    https://wwww.gnu.org/licenses/gpl.txt

# Copyright (C) 2020  Raúl Caro Pastorino
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

# Guía de estilos aplicada: PEP8

#######################################
# #           Descripción           # #
#######################################
##
# # Conexión a la API.
##

#######################################
# #       Importar Librerías        # #
#######################################

import datetime

## Cargo archivos de configuración desde .env
from dotenv import load_dotenv
load_dotenv(override=True)
import os
import json
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time

from dotenv import load_dotenv


#######################################
# #             Variables           # #
#######################################
sleep = time.sleep

#######################################
# #             Funciones           # #
#######################################

# Cargo archivos de configuración desde .env sobreescribiendo variables locales.
load_dotenv(override=True)

class ApiConnection:
    has_debug = os.getenv("DEBUG") == "True"

    # Configuración API para el volcado de datos.
    API_URL = os.getenv("API_URL")
    API_TOKEN = os.getenv("API_TOKEN")

    # Configuración para identificar el dispositivo que envía los datos.
    PC_NAME = os.getenv("PC_NAME")
    PC_ID = os.getenv("PC_ID")

    def requests_retry_session(
            retries=3,
            backoff_factor=0.3,
            status_forcelist=(500, 502, 504),
            session=None,
    ):
        """
        Crea una sesión para reintentar envío HTTP cuando falla.
        :param backoff_factor:
        :param status_forcelist:
        :param session:
        :return:
        """
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        return session

    def send(self, path, datas_json):
        '''
        Envía la petición a la API.
        :param path: Directorio dentro de la api (ex: /keycounter/add-json)
        '''

        url = self.API_URL
        token = self.API_TOKEN
        full_url = url + path

        data = {
            'data': datas_json,
            'info': 'Enviado desde ' + self.PC_NAME
        }

        headers = {
            'Content-type': 'application/json',
            'Accept': 'text/plain',
            'Authorization': 'Bearer ' + str(token),
        }

        try:
            req = self.requests_retry_session().post(
                full_url,
                data=json.dumps(data),
                headers=headers,
                timeout=30
            )

            if self.has_debug:
                print('Respuesta de API: ', req.status_code)
            #print('Recibido: ', req.text)

            # Guardado correctamente 201, con errores 200, mal 500
            if int(req.status_code) == 201:
                return True
            elif int(req.status_code) == 200:
                if self.has_debug:
                    print('Al guardar en la API algunos elementos tuvieron error.')
                return True
            else:
                return False
        except Exception as e:
            if self.has_debug:
                print('Ha fallado la petición http :', e.__class__.__name__)
                #print('Ha fallado la petición http :', e)
            sleep(5)

            return False

    def parse_to_json(self, rows, columns):
        """
        Convierte los datos recibidos en JSON
        :param rows: Tuplas con todas las entradas desde la DB.
        :param columns: Nombre de las columnas en orden respecto a tuplas.
        :return: Devuelve el objeto json
        """

        result = []

        # Compongo el objeto json que será devuelto.
        for row in rows:
            tupla = {
                'device_id': self.PC_ID,
                'device_name': self.PC_NAME
            }

            # Por cada tupla creo la pareja de clave: valor
            for iteracion in range(len(columns)):
                cell = str(row[iteracion])

                if columns[iteracion] != 'id':
                    tupla.update({columns[iteracion]: cell})

            result.append(tupla)

        return json.dumps(
            result,
            default=None,
            ensure_ascii=False,
            sort_keys=True,
            indent=4,
        )

    def upload(self, name, path, datas, columns):
        """
        Recibe la ruta dentro de la API y los datos a enviar para procesar la
        subida atacando la API.
        :param path: Ruta dentro de la api
        :param datas: Datos a enviar
        """
        if datas:
            if self.has_debug:
                print('Subiendo datos para: ' + name + ', ruta de api: ' + path)

            datas_json = self.parse_to_json(datas, columns)

            #if self.has_debug:
                #print('Datos formateados en JSON:', datas_json)

            result_send = self.send(path, datas_json)

            return result_send
