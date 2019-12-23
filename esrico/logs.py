# -*- coding: cp1252 -*-
import json,sys, os,time
import logging
import datetime

from prompt_toolkit.key_binding.bindings.named_commands import self_insert
from datetime import date
from dateutil.rrule import rrule, DAILY
from xml.dom import minidom
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET



Log=logging.getLogger('__main__')
header = "AÑO|MES|DIA|HORA|MINUTO|SEGUNDO|TIPO|CODE|TARGET|METHOS_NAME|MACHINE|MENSAJE\n"
class Logs:
    @property
    def PathBase(self):
        return self.x|
    @property
    def ReportFile(self):
        return self._ReportFile
    
    def __init__(self, aPath, reportFile):
        Log.info("Inicializando Path:{0} File:{1}".format(aPath, reportFile))
        self._PathBase=aPath
        self._ReportFile=reportFile
                
    def GenerateReport(self):
        try:
            Log.info("Llamando GenerateReport");
            Log.info("Archivo: {0}".format(self._ReportFile));
            summaryFile = open(self._ReportFile, "w")
            summaryFile.write(header)
            fileName = self.ReportFile
            for base, dirs, files in os.walk(self._PathBase):
                for adir in dirs:
                    Log.info("adir:{0}".format(adir))
                
                
                Log.info("base:{0}".format(base))
                
                for fileName in files:
                    fullPath = os.path.join(base, fileName)
                    
                    if os.path.isfile(fullPath):
                        basename, extension = os.path.splitext(fullPath)
                        #print fullPath
                        if extension == ".log":
                            Log.info("fullPath:{0}".format(fullPath))
                            aFile = open(fullPath,"r")
                            data = aFile.read()
                            aFile.close()
                            data=data.replace('<?xml version="1.0" encoding="utf-8" ?>','')
                            xmldoc = parseString( '<logs>' +data + '</logs>')
                            itemlist = xmldoc.getElementsByTagName('Msg')
                            
                            #for child in ET.fromstring(xml):
                            for s in itemlist :
                                #Log.info("Item:\n{0}".format(s))
                            #for s in ET.fromstring('<logs>' +data + '</logs>') :
                                atime =  s.attributes['time'].value.split(',')
                                #Log.info("Item:\n{0}".format(atime))
                                
                                tipo= s.attributes['type'].value
                                cod= s.attributes['code'].value
                                target= s.attributes['target'].value
                                
                                machine= s.attributes['machine'].value
                                try:
                                    methodName= s.attributes['methodName'].value
                                except:
                                    methodName=""
                                try:
                                    msg= s.childNodes[0].nodeValue.replace('\n','')
                                except:
                                    msg=''
                                
                                
                               
                                
                                aRegTime=time.strptime(atime[0],'%Y-%m-%dT%H:%M:%S')
                                aRegTimeLocal=time.localtime(time.mktime(aRegTime))
                                line="{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}".format(aRegTimeLocal.tm_year,aRegTimeLocal.tm_mon,aRegTimeLocal.tm_mday,aRegTimeLocal.tm_hour,aRegTimeLocal.tm_min,aRegTimeLocal.tm_sec,tipo,cod,target,methodName,machine,msg)
                                Log.warning(line)
                                summaryFile.write(line+"\n")
            summaryFile.close()
        except:
            Log.error(str((sys.exc_info()[0])) + " " + str((sys.exc_info()[1])))