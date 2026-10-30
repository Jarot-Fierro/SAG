"""Equivalente a SD_Recordset de SISTEMA, usando parametros enlazados."""
import logging

import oracledb

logger = logging.getLogger('web.views')


def recordset(connection, function, parameters):
    # Nombres fijos: nunca construir identificadores desde el formulario.
    functions = {
        'areas': 'SIABI_SEG.SEG_USER_OBTINFO_INI',
        'perfil': 'SIABI_SEG.SEG_USER_OBTINFO',
    }
    name = functions[function]
    logger.debug('Ejecutando funcion Oracle %s.', name)
    with connection.cursor() as cursor:
        with cursor.callfunc(name, oracledb.DB_TYPE_CURSOR, parameters) as result:
            columns = [column[0].lower() for column in result.description]
            rows = [dict(zip(columns, row)) for row in result]
    logger.debug('Funcion %s finalizada: filas=%s.', name, len(rows))
    return rows
