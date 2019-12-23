# -*- coding: utf-8 -*-
import arcpy, sys, time, os, json
import logging
import logging.handlers
from datetime import datetime
from esrico import webgis
from arcgis.gis import *

from esrico.webgis import PortaREST
from jsonschema._validators import items

class ArcGisLogHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        if record.levelno >= logging.ERROR:
            log_method = arcpy.AddError
        elif record.levelno >= logging.WARNING:
            log_method = arcpy.AddWarning
        else:
            log_method = arcpy.AddMessage
        log_method(self.format(record))

def printStartEndEjecution(tipo='START'):
    if tipo=='START':
        Log.info("---------------------------------------------------------------------------------------------")
        Log.info("Fecha de Ejecuci�n:{0} Hora de Ejecucion:{1}".format(time.strftime("%d-%m-%Y"),time.strftime("%Hh%Mm%Ss")))
        Log.info("---------------------------------------------------------------------------------------------")
    elif tipo=='END' :
        Log.info("---------------------------------------------------------------------------------------------")
        Log.info("Fecha de Finalizaci�n:{0} Hora de Finalizaci�n:{1}".format(time.strftime("%d-%m-%Y"),time.strftime("%Hh%Mm%Ss")))
        Log.info("---------------------------------------------------------------------------------------------")
        

if __name__ == '__main__':
    try:
        DebugMode = True
        depuracion ="false"
        if depuracion=='true':
            DebugMode = True
        
        if(DebugMode):
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        Log = logging.getLogger(__name__)
        
        fecha = time.strftime("%d-%m-%Y")
        hora  = time.strftime("%Hh%Mm%Ss")
        ##RUTA INSTALACI�N DE GEOPROCESO  
        __dir__ = os.path.dirname(sys.argv[0])
        nombre_logger = fecha + "-LogDev"
        filepathLogs =  os.path.join(__dir__,"Logs")
        
        if not os.path.exists(filepathLogs):
            os.makedirs(filepathLogs)
     
        
        HDLR = logging.handlers.RotatingFileHandler(os.path.join(filepathLogs,nombre_logger+".log"), maxBytes=2097152000, backupCount=50)
        formatter = logging.Formatter('%(asctime)s\t %(levelname)s\t%(message)s')
        HDLR.setFormatter(formatter)
        Log.addHandler(HDLR)
        arcgis_handler = ArcGisLogHandler()
        Log.addHandler(arcgis_handler)
        printStartEndEjecution()

        '''
            PortaREST(usernameSource, passwordSource, portalSource, usernameTarget, passwordTarget, portalTarget)
            usernameSource: Nombre de usuario del portal origen
            passwordSource: Contraseña de usuario portal de origen
            portalSource:  URL de portal de Origen
            usernameTarget: Nombre de usuario del portal destino (Opcional)
            passwordTarget: Contraseña de usuario portal destino (Opcional)
            portalTarget: URL de portal destino (Opcional)
   
        '''
        
       
        WebGISRest = PortaREST("usuario","pass@word", "https://portal.entidad.com/portal")
        WebGISRest.GenerateItemsByUserReport("D:\Reportes\portal-report-{}.csv".format(fecha))

        
                
   
        
    except:
            Log.error(str((sys.exc_info()[0])) + " " + str((sys.exc_info()[1])))
            printStartEndEjecution('END')
            Log.handlers = []
            sys.exit()  