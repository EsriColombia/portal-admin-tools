# -*- coding: cp1252 -*-
import arcpy, sys, time, os, json
import logging
import logging.handlers
from datetime import datetime
from esrico import webgis

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
        Log.info("Fecha de Ejecución:{0} Hora de Ejecucion:{1}".format(time.strftime("%d-%m-%Y"),time.strftime("%Hh%Mm%Ss")))
        Log.info("---------------------------------------------------------------------------------------------")
    elif tipo=='END' :
        Log.info("---------------------------------------------------------------------------------------------")
        Log.info("Fecha de Finalización:{0} Hora de Finalización:{1}".format(time.strftime("%d-%m-%Y"),time.strftime("%Hh%Mm%Ss")))
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
        
        
        ServerDirectoryPath= "D:/MIGRACION108/arcgissystem"
        
        ags= webgis.ArcGISServer()

        for base, dirs, files in os.walk(ServerDirectoryPath):
            if((base[-9:]=="extracted")):
                configFile = base+"/"+"serviceconfiguration.json"
                if(os.path.isfile(configFile)):
                    Log.debug(configFile)
                    with open(configFile,encoding="utf8") as json_file:
                        data = json.load(json_file)
                        ws = webgis.WebService(data,configFile)
                        ags.AddWS(ws)

                else:
                    Log.warning("No se encuentra archivo de configuración en {0} ".format(base))            

        ags.SaveListServices2CSV("D:\Reportes\ReporteSite-{}.csv".format(fecha))
        

    except:
            Log.error(str((sys.exc_info()[0])) + " " + str((sys.exc_info()[1])))
            printStartEndEjecution('END')
            Log.handlers = []
            sys.exit() 