# -*- coding: utf-8 -*-
import sys, os,ssl
import json
import shutil
import uuid 
#import six
import logging
import urllib
import tempfile
import time


import io
import binascii
from datetime import datetime, timedelta

#import json
#import argparse

#from arcgis.gis import *
from arcgis.gis import *
from prompt_toolkit.key_binding.bindings.named_commands import self_insert


from PIL import Image
#import cStringIO as StringIO
from io import StringIO
from functools import wraps



Log=logging.getLogger('__main__')


def retry(exceptions, tries=4, delay=3, backoff=2, logger=None):
    """
    Retry calling the decorated function using an exponential backoff.

    Args:
        exceptions: The exception to check. may be a tuple of
            exceptions to check.
        tries: Number of times to try (not retry) before giving up.
        delay: Initial delay between retries in seconds.
        backoff: Backoff multiplier (e.g. value of 2 will double the delay
            each retry).
        logger: Logger to use. If None, print.
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    msg = '{}, Retrying in {} seconds...'.format(e, mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry

class PortaREST:
    CSVHEADERITEMS = "ID|OWNER|USERNAME|FULLNAME|USERTYPE|E-MAIL|LAST_LOGIN_DIA|LAST_LOGIN_MES|LAST_LOGIN_ANIO|STORAGE_USAGE|ROLE|LEVEL|DISABLED|CREATED|MODIFIED|TITLE|TYPE|TYPE_KEYWORDS|URL|ACCESS|NUM_VIEWS|SCORE_COMPLETENESS|SIZE\n"
    LINE_ITEMS = ""
    
    @property
    def PortalID(self):
        return self._portalID
    @PortalID.setter
    def PortalID(self, value):
        self._portalID=value
    @property
    def PortalSourceURL(self):
        return self._portalSourceURL
    @PortalSourceURL.setter
    def PortalSourceURL(self, value):
        self._portalSourceURL=value
    @property
    def UsernameSource(self):
        return self._usernameSource
    @UsernameSource.setter
    def UsernameSource(self, value):
        self._usernameSource=value
    @property
    def PortalSourceToken(self):
        return self._portalSourceToken
    @PortalSourceToken.setter
    def PortalSourceToken(self, value):
        self._portalSourceToken=value
    @property
    def PortalTargetURL(self):
        return self._portalTargetURL
    @PortalTargetURL.setter
    def PortalTargetURL(self, value):
        self._portalTargetURL=value
    @property
    def UsernameTarget(self):
        return self._usernameTarget
    @UsernameTarget.setter
    def UsernameTarget(self, value):
        self._usernameTarget=value
    @property
    def PortalTargetToken(self):
        return self._portalTargetToken
    @PortalTargetToken.setter
    def PortalTargetToken(self, value):
        self._portalTargetToken=value
    
    def __init__(self,usernameSource,passwordSource,portalSource,usernameTarget=None,passwordTarget=None,portalTarget=None):
        c = self.CSVHEADERITEMS.split("|")
        x = range(len(c))

        for i in x:
            if (len(c)==i+1):
                self.LINE_ITEMS=self.LINE_ITEMS+"{"+str((i))+"}"
            else:
                self.LINE_ITEMS=self.LINE_ITEMS+"{"+str((i))+"}|"

                
        self.PortalSourceURL=portalSource
        self.PortalSourceToken=self.__generateToken(usernameSource, passwordSource, portalSource)

        self.UsernameSource=usernameSource
        if(portalTarget!=None):
            self.UsernameTarget=usernameTarget
            self.PortalTargetURL=portalTarget
            self.PortalTargetToken=self.__generateToken(usernameTarget, passwordTarget, portalTarget)
            print("Certificado Generado:{}".format(self.PortalTargetToken))
        
        
        
    
    def __generateToken(self,username, password, portalUrl):
        
        print("........__generateToken")
        print("{0},{1},{2}".format(username, password, portalUrl))
        
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            # Legacy Python that doesn't verify HTTPS certificates by default
            pass
        else:
            # Handle target environment that doesn't support HTTPS verification
            ssl._create_default_https_context = _create_unverified_https_context
        
        
        parameters = urllib.parse.urlencode({'username' : username,
                                       'password' : password,
                                       'client' : 'referer',
                                       'referer': portalUrl,
                                       'expiration': 60,
                                       'f' : 'json'}).encode("utf-8")
        req = urllib.request.Request(portalUrl+ '/sharing/rest/generateToken?')
        response = urllib.request.urlopen(req,parameters).read()
        
                                  
        try:
            jsonResponse = json.loads(response)
            if 'token' in jsonResponse:
                return jsonResponse['token']
            elif 'error' in jsonResponse:
                Log.error(jsonResponse['error']['message'])
                for detail in jsonResponse['error']['details']:
                    Log.error(detail)
        except ValueError:
            Log.error("Se ha presentado un error")
            Log.error(ValueError)

    def searchPortal(self,portal, query=None, totalResults=None, sortField='numviews', sortOrder='desc', token=None):
        '''
        Search the portal using the specified query and search parameters.
        Optionally provide a token to return results visible to that user.
        '''
        # Default results are returned by highest
        # number of views in descending order.
        allResults = []
        if not totalResults or totalResults > 100:
            numResults = 100
        else:
            numResults = totalResults
        results = self.__search__(portal, query, numResults, sortField, sortOrder, 0,token)
        if not 'error' in results.keys():
            if not totalResults:
                totalResults = results['total'] # Return all of the results.)
            allResults.extend(results['results'])
            
            while (results['nextStart'] > 0 and
                   results['nextStart'] < totalResults):
                # Do some math to ensure it only
                # returns the total results requested.
                numResults = min(totalResults - results['nextStart'] + 1, 100)
                go=True
                while (go):
                    results = self.__search__(portal=portal, query=query,
                                         numResults=numResults, sortField=sortField,
                                         sortOrder=sortOrder, token=token,
                                         start=results['nextStart'])
                    print ()
                    if(results!=-1):
                        print ("Entra a results != -1")
                        go=False
                    else:
                        go=True
                        print ("Entra a results = -1")
                        
                        
                allResults.extend(results['results'])
            return allResults
        else:
            Log.error("-->")
            Log.error(results['error']['message'])
            return results

    @retry(urllib.error.URLError, tries=4, delay=3, backoff=2)
    def __search__(self,portal, query=None, numResults=100, sortField='numviews',sortOrder='desc', start=0, token=None):
        try:
            '''Retrieve a single page of search results.'''
            parameters = urllib.parse.urlencode({
                'q': query,
                'num': numResults,
                'sortField': sortField,
                'sortOrder': sortOrder,
                'f': 'json',
                'start': start,
                'token': self.PortalSourceToken         
            }).encode("utf-8")
            
            
            request = urllib.request.Request( portal + '/sharing/rest/search?')
            results = json.loads(urllib.request.urlopen(request,parameters).read())
            return results
        except:
            Log.error("----Otro")
            Log.error(str((sys.exc_info()[0])) + " " + str((sys.exc_info()[1])))
            return -1
        

        
    def getPortalSelf (self):
        parameters = urllib.parse.urlencode({'token': self.PortalSourceToken, 'f': 'json'}).encode("utf-8")
        request= urllib.request.Request(self.PortalSourceURL + '/sharing/rest/portals/self' + '?')
        selfPortal = json.loads(urllib.request.urlopen(request,parameters).read())
        self.PortalID= selfPortal["id"]
        return selfPortal
    
    def GenerateItemsByUserReport(self,aFile):
        Log.debug("Ingresando a ItemsByUserReport")
        try:
            self.getPortalSelf()
            csvFile = open(aFile, "w")
            csvFile.write(self.CSVHEADERITEMS)
            
            go=True
            nextStart=1
            while go:
                users = self.getUsers(nextStart)
                if(users["nextStart"]==-1):
                    go=False
                else: 
                    go=True
                nextStart=users["nextStart"]
                
                for u in users["users"]:
                    Log.info("Procesando usuario {0}".format(u["username"]))
                    
                    #destUser = self.getUserContent( u['username'],"Source")
                    #print("query = {}".format("owner:"+u["username"]))
                    #destUser = self.searchPortal(self.PortalSourceURL, "owner:"+u["username"], 500, token=self.PortalSourceToken)
                    if (u["username"]!="eroa_portal"):
                   
                        destUser = self.searchPortal(self.PortalSourceURL,"owner:"+ '"' + u["username"]+'"', 1000000000, token=self.PortalSourceToken)
                        print ("---------destUser----------------")
                        print(len(destUser))
                        if (len(destUser)>0):
                            #print(self.LINE_ITEMS)
                            #print(destUser)
                            for i in destUser:
                                print(i['id'])
                                aTitle=""
                                if(i['title']!=None):
                                    aTitle=i['title'].encode()
                                    
                                
                                line = self.LINE_ITEMS.format(
                                    i['id'],
                                    i['owner'],
                                    u['username'],
                                    u['fullName'],
                                    u['userType'],
                                    u['email'],
                                    datetime.fromtimestamp(u['lastLogin'] / 1e3).day,
                                    datetime.fromtimestamp(u['lastLogin'] / 1e3).month,
                                    datetime.fromtimestamp(u['lastLogin'] / 1e3).year,
                                    u['storageUsage'],
                                    u['role'],
                                    u['level'],
                                    u['disabled'],
                                    datetime.fromtimestamp(i['created']/1e3),
                                    datetime.fromtimestamp(i['modified']/1e3),
                                    aTitle,
                                    i['type'],
                                    i['typeKeywords'],
                                    i['url'],
                                    i['access'],
                                    i['numViews'],
                                    i['scoreCompleteness'],
                                    i['size'])
                                csvFile.write(line+"\n")
                        else:
                            print( u['username'])
                            print( u['username'])
                            print( u['username'])
                            print( u['username'])
                            print( u['lastLogin'])
                            
                            dia=""
                            mes=""
                            anio=""
                            if (u['lastLogin']!=-1):
                                dia = datetime.fromtimestamp(u['lastLogin'] / 1e3).day
                                mes= datetime.fromtimestamp(u['lastLogin'] / 1e3).month
                                anio = datetime.fromtimestamp(u['lastLogin'] / 1e3).year
                            
                        
                            
                            line = self.LINE_ITEMS.format(
                                "Sin Contenido",
                                None,
                                u['username'],
                                u['fullName'],
                                u['userType'],
                                u['email'],
                                dia,
                                mes,
                                anio,
                                u['storageUsage'],
                                u['role'],
                                u['level'],
                                u['disabled'],
                                None,
                                None,
                                None,
                                None,
                                None,
                                None,
                                None,
                                None,
                                None,
                                None)
                            csvFile.write(line+"\n")
                            
                            
            csvFile.close()
        except:
            Log.error(str((sys.exc_info()[0])) + " " + str((sys.exc_info()[1])))



    
        
        
          
    def getUsers(self,nextStart):
        #sharing/rest/portals/fa019fbbfbb845d08cc9f0acde6dd8af/users
        parameters = urllib.parse.urlencode({
            'token': self.PortalSourceToken,
            'start': nextStart,
             'f': 'json'
        }).encode("utf-8")
        request= urllib.request.Request(self.PortalSourceURL + '/sharing/rest/portals/'+ self.PortalID +'/users'+ '?')
        users = json.loads(urllib.request.urlopen(request,parameters).read())
        return users
        
    def getUserContent(self,userContent,aType='Source'):
        if (aType=="Source"):
            print("userContent:{0}\n self.PortalSourceURL:{1}\n self.PortalSourceToken:{2}\n".format(userContent, self.PortalSourceURL ,self.PortalSourceToken))
            return self.__getUserContent(userContent, self.PortalSourceURL ,self.PortalSourceToken)
        else:
            return self.__getUserContent(userContent, self.PortalTargetURL ,self.PortalTargetToken)
        
        
    def __getUserContent(self,username, portalUrl, token):
        ''''''
     
        parameters = urllib.parse.urlencode({'token': token, 'f': 'json'}).encode("utf-8")
        #request = (portalUrl + '/sharing/rest/content/users/' + username +'?' + parameters)
        request = urllib.request.Request(portalUrl + '/sharing/rest/content/users/' + username +'?')
        content = json.loads(urllib.request.urlopen(request,parameters).read())
        return content
    
        
    
    def getItemDescription(self,itemId):
        print("--- getItemDescription --------")
        print("--- getItemDescription itemId: {}--------".format(itemId))
        '''Returns the description for a Portal for ArcGIS item.'''
        print("--- getItemDescription -------- 1")
        parameters = urllib.parse.urlencode({'token' : self.PortalSourceToken,'f' : 'json'}).encode("utf-8")
        print("--- getItemDescription -------- 2")
        request = urllib.request.Request(self.PortalSourceURL + "/sharing/rest/content/items/" + itemId + "?")
        print("--- getItemDescription -------- 3")
        print("--- getItemDescription URL: {}--------".format(self.PortalSourceURL + "/sharing/rest/content/items/" + itemId + "?" ))
        #response = urllib.request.urlopen(portalUrl + "/sharing/rest/content/items/" + itemId + "?" + parameters).read()
        print("--- getItemDescription -------- 4")
        response = urllib.request.urlopen(request,parameters).read()
        print("--- getItemDescription -------- 5")
        return response
    
    def getItemData(self,itemId, portalUrl, token):
        '''Returns the description for a Portal for ArcGIS item.'''
        parameters = urllib.parse.urlencode({'token' : token,
                                       'f' : 'json'}).encode("utf-8")
                                       
        request = urllib.request.Request(portalUrl + "/sharing/rest/content/items/" +  itemId + "/data?" + parameters)                               
        #response = urllib.request.urlopen(portalUrl + "/sharing/rest/content/items/" +  itemId + "/data?" + parameters).read()
        response = urllib.request.urlopen(request).read()
        return response
    
    def addItem(self,username, folder, description, data, portalUrl, token,
                    thumbnailUrl=''):
        '''Creates a new item in a user's content.'''
        parameters = urllib.parse.urlencode({'item': json.loads(description)['title'],
                                       'text': data,
                                       'overwrite': 'false',
                                       'thumbnailurl': thumbnailUrl,
                                       'token' : token,
                                       'f' : 'json'}).encode("utf-8")
        postParameters = (urllib.parse.urlencode(json.loads(description)).encode("utf-8").replace('None', '') + '&' + parameters)
        request = urllib.request.Request(portalUrl + '/sharing/rest/content/users/' +  username + '/' + folder + '/addItem?', postParameters)
        #response = urllib.request.urlopen(portalUrl + '/sharing/rest/content/users/' +  username + '/' + folder + '/addItem?', postParameters).read()
        response = urllib.request.urlopen(request).read()
        return response    
    
    def copyItem(self,itemId, destinationOwner, destinationFolder, sourcePortal, sourceToken, destinationPortal=None, destinationToken=None):
        '''
        Copies an item into a user's account in the specified folder.
        Use '/' as the destination folder when moving content into root.
        '''
        # This function defaults to copying into the same Portal
        # and with the same token permissions as the source account.
        # If the destination is a different Portal then specify that Portal url
        # and include a token with permissions on that instance.
        if not destinationPortal:
            destinationPortal = sourcePortal
        if not destinationToken:
            destinationToken = sourceToken
        description = self.getItemDescription(itemId, sourcePortal, sourceToken)
        data = self.getItemData(itemId, sourcePortal, sourceToken)
        thumbnail = json.loads(description)['thumbnail']
        if thumbnail:
            thumbnailUrl = (sourcePortal + '/sharing/rest/content/items/' + itemId + '/info/' + thumbnail + '?token=' + sourceToken)
        else:
            thumbnailUrl = ''
        status = self.addItem(destinationOwner, destinationFolder, description, data, destinationPortal, destinationToken, thumbnailUrl)
        return json.loads(status)


    

class PortalEnterprise:
    GROUP_COPY_PROPERTIES = ['title', 'description', 'tags', 'snippet', 'phone',
                         'access', 'isInvitationOnly','isViewOnly','owner','sortField','sortOrder']
    
    @property
    def SourcePortal(self):
        return self._sourcePortal
    
    @SourcePortal.setter
    def SourcePortal(self, value):
        self._sourcePortal = value
    
    @property
    def TargetAdminUserName(self):
        return self._targetAdminUserName
    
    @TargetAdminUserName.setter
    def TargetAdminUserName(self, value):
        self._targetAdminUserName = value
        
    @property
    def SourceGroups(self):
        return self._sourceGroups
    
    @SourceGroups.setter
    def SourceGroups(self, value):
        self._sourceGroups = value
    
    @property
    def TargetPortal(self):
        return self._targetPortal
    @TargetPortal.setter
    def TargetPortal(self, value):
        self._targetPortal = value
        
    @property
    def LstUsers(self):
        return self._lstUsers
    @LstUsers.setter
    def LstUsers(self, value):
        self._lstUsers=value
    @property
    def SystemUsers(self):
        return self._systemUsers
    @SystemUsers.setter
    def SystemUsers(self, value):
        self._systemUsers=value
    @property
    def SystemGroups(self):
        return self._systemGroups
    @SystemGroups.setter
    def SystemGroups(self, value):
        self._systemGroups=value  
    
    def __init__(self,usernameSource,passwordSource,portalSource,usernameTarget=None,passwordTarget=None,portalTarget=None):
        self.SourcePortal=GIS(portalSource, usernameSource, passwordSource,verify_cert=False)
        self.SystemUsers=['system_publisher', 'esri_nav', 'esri_livingatlas', 'esri_boundaries', 'esri_demographics']
        
        if(usernameTarget!=None):
            self.TargetAdminUserName=usernameTarget
            self.TargetPortal=GIS(portalTarget, usernameTarget, passwordTarget,verify_cert=False)
        self.SetSourceGroups()
        
    #def GetGroupsByUser(self,username):
    #    return [g for g in self.SourceGroups if g.owner == username]
    def GetGroupsByUser(self,username):
        return  self.SourcePortal.groups.search("!owner:esri_* & !Basemaps & owner:{}".format(username) )
            
        
    def SetSourceGroups(self):
        self.SourceGroups=self.SourcePortal.groups.search("!owner:esri_* & !Basemaps")
#        for g in self.SourceGroups:
#             print("Titulo:{}".format(g.title))
#             print("\tOwner:{}".format(g.owner))
#             print("\tThumbnail:{}".format(g.thumbnail))
#             print("\taccess:{}".format(g.access))
#             print("\tcreated{}".format(g.created))
#             print("\tdescription:{}".format(g.description))
#             print("\tid:{}".format(g.id))
#             print("\tisInvitationOnly:{}".format(g.isInvitationOnly))
#             print("\tisViewOnly:{}".format(g.isViewOnly))
#             print("\tmodified:{}".format(g.modified))
#             print("\tphone:{}".format(g.phone))
#             print("\tsnippet:{}".format(g.snippet))
#             print("\tsortField:{}".format(g.sortField))
#             print("\tsortOrder:{}".format(g.sortOrder))
#             print("\ttags:{}".format(g.tags))
 
    def SetUsersToClone(self,querySentence=None,excludeSystem=True):
        __dir__ = os.path.dirname(sys.argv[0])
        
        
        tempFilesPath =  os.path.join(__dir__,"TempFiles")
        if not os.path.exists(tempFilesPath):
            os.makedirs(tempFilesPath)
        
        print("-----------------------------")
        print(__dir__)
        print("-----------------------------")

        
        users = self.SourcePortal.users.search(query=querySentence,max_users=500,exclude_system=excludeSystem)
        l=[]
        for u in users:
            fileTempName = str("F{}.jpg".format(uuid.uuid1()))
            tempFilePath =  os.path.join(tempFilesPath,fileTempName)
            response = u.get_thumbnail()
            f = open(tempFilePath, 'wb')
            f.write(response)
            
            
           
            usrPortal=PortalUser(
                u.username, 
                u.firstName, 
                u.lastName, 
                u.email, 
                u.description, 
                u.role, 
                u.provider, 
                u.idpUsername, 
                u.level,
                u.fullName,
                access=u.access,
                preferredView=u.preferredView,
                tags=u.tags,
                culture=u.culture,
                region=u.region,
                thumbnail_link=tempFilePath,
                itemsContent=u.items,
                folders=u.folders
                
                )

            l.append(usrPortal)
  
        self.LstUsers=l
        f.close()
        
     
    

    def AddSystemUser(self,value):
        self.SystemUsers.append(value)
        
    def CopyUser(self, user, password):
        Log.info("Ingresando a CopyUser")
        try:
            firstname = user.Firstname
            lastname = user.Lastname
        except:
            fullName = user.FullName
            firstname = fullName.split()[0]
            try:
                lastname = fullName.split()[1]
            except:
                lastname = ' '
     
        try:
            testuser = self.TargetPortal.users.get(user.Username)
            Log.info("Verificando la existencia del usuario: {0}".format(user.Username))
            if not testuser is None:
                Log.info("\tUsername {} already exists in Target Portal; skipping user creation.\n".format(user.Username))
                return testuser
            Log.info("El usuario: {0} No existe, procediendo a la creacion".format(user.Username))
            Log.info("user.username:{}".format(user.Username))
            Log.info("password:{}".format(password))
            Log.info("firstname:{}".format(firstname))
            Log.info("lastname:{}".format(lastname))
            Log.info("user.email:{}".format(user.Email))
            Log.info("user.description:{}".format(user.Description))
            Log.info("user.role:{}".format(user.Role))
            Log.info("user.provider:{}".format(user.Provider))
            Log.info("user.idpUsername:{}".format(user.IdpUsername))
            Log.info("user.level:{}".format(user.Level))

            
            
            Log.info("=========================================================================")
            target_user = self.TargetPortal.users.create(
                username=user.Username, 
                password=password, 
                firstname=firstname, 
                lastname=lastname,
                email=user.Email, 
                description =user.Description, 
                role =user.Role,
                level=user.Level, 
                provider =user.Provider, 
                user_type="creator"
                )
            
            
            
            
            Log.info("Ingresando a Actualizar")
            
            Log.info("user.Access:{0}".format(user.Access))
            Log.info("user.PreferredView:{0}".format(user.PreferredView))
            Log.info("user.Description:{0}".format(user.Description))
            Log.info("user.Tags:{0}".format(user.Tags))
            Log.info("user.Thumbnail_link:{0}".format(user.Thumbnail_link))
            Log.info("user.Culture:{0}".format(user.Culture))
            Log.info("user.Region:{0}".format(user.Region))
            
            
          
            
            
            target_user.update(user.Access, user.PreferredView,
                               user.Description, user.Tags, thumbnail = user.Thumbnail_link,
                               culture=user.Culture, region=user.Region)
            Log.info("Ingresando a Actualizar---2")
            Log.info("Ingresando a Actualizar---3 user.Role:{0}".format(user.Role))
            
            #Seccion que consulta los grupos del usuario en el Portal Source
            gs=self.GetGroupsByUser(user.Username)
            for g in gs:
                print("Procesando grupos: {}".format(g.title))
                with tempfile.TemporaryDirectory() as temp_dir:
                    try:
                        target_group = {}

                        for property_name in self.GROUP_COPY_PROPERTIES:
                            target_group[property_name] = g[property_name]
            
                        if g['access'] == 'org' and self.TargetPortal.properties['portalMode'] == 'singletenant':
                            #cloning from ArcGIS Online to ArcGIS Enterprise
                            target_group['access'] = 'public'
            
                        elif g['access'] == 'public' and self.SourcePortal.properties['portalMode'] == 'singletenant' and self.TargetPortal.properties['portalMode'] == 'multitenant'  and 'id' in self.TargetPortal.properties:
                                #cloning from ArcGIS Enterprise to ArcGIS Online org
                                target_group['access'] = 'org'
            
                        # Download the thumbnail (if one exists)
                        if 'thumbnail' in g:
                            target_group['thumbnail'] = g.download_thumbnail(temp_dir)
                        
                        
                        print(target_group)
                        # Create the group in the target portal
                        copied_group = self.TargetPortal.groups.create_from_dict(target_group)
                        
                        #TODO: Asignar Miembros
                        # Reassign all groups to correct owners, add users, and find shared items
                        members = g.get_members()
                        if not members['owner'] == self.TargetAdminUserName:
                            copied_group.reassign_to(members['owner'])
#                         if members['users']:
#                             copied_group.add_users(members['users'])
                        
                       
                        
                        
                        
                    except:
                        Log.error("Error creando Grupo" + g['title'])
                
                
            #Items
            
            carpetas = user.Folders()
            print("-------------------------------------------") 
            print(carpetas) 
            
            
            
#             if 'role' in user and not user.Role == 'org_user':
#                 Log.info("Ingresando a Actualizar---2")
#                 target_user.update_role(user.Role)
     
            return target_user
     
        except:
            Log.error("No se puede crear el usuario "+ user.Username)
            Log.error( str((sys.exc_info()[0])) + " " + str((sys.exc_info()[1])))
            return None
         
    def CopyGroup(self, group):
        ''' Copy group to the target portal.'''
        GROUP_COPY_PROPERTIES = ['title', 'description', 'tags', 'snippet', 'phone', 'access', 'isInvitationOnly']
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a new groups with the subset of properties we want to
            # copy to the target portal. Handle switching between org and
            # public access when going from an org in a multitenant portal
            # and a single tenant portal
            target_group = {}
     
            for property_name in GROUP_COPY_PROPERTIES:
                target_group[property_name] = group[property_name]
     
            if target_group['access'] == 'org' and self.TargetPortal.properties['portalMode'] == 'singletenant':
                target_group['access'] = 'public'
            elif target_group['access'] == 'public' and self.SourcePortal.properties['portalMode'] == 'singletenant' \
                 and self.TargetPortal.properties['portalMode'] == 'multitenant' and 'id' in self.TargetPortal.properties: # is org
                target_group['access'] = 'org'
     
            # Handle the thumbnail (if one exists)
            thumbnail_file = None
            if 'thumbnail' in group:
                target_group['thumbnail'] = group.download_thumbnail(temp_dir)
     
            # Create the group in the target portal
            copied_group = self.TargetPortal.groups.create_from_dict(target_group)
     
            # Reassign all groups to correct owners, add users, and find shared items
            members = group.get_members()
            copied_group.reassign_to(members['owner'])
            if members['users']:
                copied_group.add_users(members['users'])
     
            # remove the admin user copying this group from the copied group if that
            #   username is not part of the group in the Source Portal
            if not self.TargetPortal.users.me.username in members['users']:
                copied_group.remove_users(self.TargetPortal.users.me.username)
     
            return copied_group
         
    
    
    def CloneUsers(self):

        self.AddSystemUser(self.SourcePortal.users.me.username)

        for user in self.LstUsers:

            
            
            #SECCION PARA LA CREACION DE USUARIOS
            Log.info("--------------------------------------------------------------------")
            Log.info("\t\t Iniciando proceso de creacion de usuario {}".format(user.Username)) 
            Log.info("--------------------------------------------------------------------")
            if not user.Username in self.SystemUsers:
                Log.info('Copying {}...'.format(user.Username))
                Log.info('Copying user.provider {}...'.format(user.Provider))
                Log.info('Copying user.roleId {}...'.format(user.Role))
                Log.info('Copying user.provider {}...'.format(user.Provider))
                
                if user.Provider == 'arcgis':
                    Log.info("Ingresando a user.provider == arcgis")
                    self.CopyUser(user, 'TestPassword@123')
                elif user.Provider == 'enterprise':  # web tier authenticated users
                    Log.info("Ingresandi a user.provider == enterprise")
                    self.CopyUser(user, 'NoPwdUsed')
            
            print("Iniciando la verficicacion de las capetras")
            print (user.Username)
            
            
        
        
        

#         # Get all users from the Source Portal; set max_users to make sure you get all users
#         sourceusers = self.SourcePortal.users.search(max_users=500)
#         # Create a list of "system" Portal users that we will ignore during copy
#         systemusers = ['system_publisher', 'esri_nav', 'esri_livingatlas', 'esri_boundaries', 'esri_demographics', str(self.SourcePortal.users.me.username)]
#          
#         for user in sourceusers:
#             if not user.username in systemusers:
#                 print('Copying {}...'.format(user.username))
#                 if user.provider == 'arcgis':
#                     self.copy_user(user, 'TestPassword@123')
#                 elif user.provider == 'enterprise':  # web tier authenticated users
#                     self.copy_user(user, 'NoPwdUsed')
#                      
#                      
#         # Get list of groups from the Source Portal and also from Target Portal (for cleanup purposes)
#         sourcegroups = self.SourcePortal.groups.search()
#         targetgroups = self.TargetPortal.groups.search()
#          
#         # Create a list of "system" Portal Groups that we will ignore during copy
#         systemgroups = ['Navigator Maps', 'Featured Maps and Apps']
#          
#         # Let's make sure in our Target Portal, existing Groups don't already exist.
#         #   This is useful in testing and cleaning up Groups before trying again.
#         #   The assumption is this script is copying to a new, clean Portal.
#         for tg in targetgroups:
#             for sg in sourcegroups:
#                 if sg.title == tg.title and (not tg.owner in systemusers) and (not tg.title in systemgroups):
#                     Log.info("Limpiando grupo {} en el portal destino...".format(tg.title))
#                     tg.delete()
#                     break
#          
#         for grp in sourcegroups:
#             if not grp.title in systemgroups:
#                 Log.debug('Copiando Grupo {}...'.format(grp.title))
#                 tgt_group = self.copy_group(grp)

class PortalUser:
    @property
    def Access(self):
        return self._access
    @Access.setter
    def Access(self, value):
        self._access=value
    @property
    def PreferredView(self):
        return self._preferredView
    @PreferredView.setter
    def PreferredView(self, value):
        self._preferredView=value
    @property
    def Tags(self):
        return self._tags
    @Tags.setter
    def Tags(self, value):
        self._tags=value
    @property
    def Culture(self):
        return self._culture
    @Culture.setter
    def Culture(self, value):
        self._culture=value
    @property
    def Region(self):
        return self._region
    @Region.setter
    def Region(self, value):
        self._region=value
    @property
    def Thumbnail_link(self):
        return self._thumbnail_link
    @Thumbnail_link.setter
    def Thumbnail_link(self, value):
        self._thumbnail_link=value
    @property
    def Username(self):
        return self._username
    @Username.setter
    def Username(self, value):
        self._username=value
    @property
    def Type(self):
        return self._type
    @Type.setter
    def Type(self, value):
        self._type=value
    @property
    def Firstname(self):
        return self._firstname
    @Firstname.setter
    def Firstname(self, value):
        self._firstname=value
    @property
    def Fullname(self):
        return self._fullname
    @Fullname.setter
    def Fullname(self, value):
        self._fullname=value
    @property
    def Lastname(self):
        return self._lastname
    @Lastname.setter
    def Lastname(self, value):
        self._lastname=value
    @property
    def Email(self):
        return self._email
    @Email.setter
    def Email(self, value):
        self._email=value
    @property
    def Description(self):
        return self._description
    @Description.setter
    def Description(self, value):
        self._description=value
    @property
    def Role(self):
        return self._role
    @Role.setter
    def Role(self, value):
        self._role=value
    @property
    def Provider(self):
        return self._provider
    @Provider.setter
    def Provider(self, value):
        self._provider=value
    @property
    def IdpUsername(self):
        return self._idpUsername
    @IdpUsername.setter
    def IdpUsername(self, value):
        self._idpUsername=value
    @property
    def Level(self):
        return self._level
    @Level.setter
    def Level(self, value):
        self._level=value
    @property
    def Items(self):
        return self._items
    @Items.setter
    def Items(self, value):
        self._items=value
    @property
    def Folders(self):
        return self._folders
    @Folders.setter
    def Folders(self, value):
        self._folders=value

    def __init__(self,username, 
                firstname, 
                lastname, 
                email, 
                description,
                role, 
                provider,
                idpUsername,
                level,
                fullname,
                access,
                preferredView,
                tags,
                culture,
                region,
                thumbnail_link,
                atype=None,
                itemsContent=None,
                folders=None):
        self.Username=username
        self.Firstname=firstname
        self.Lastname=lastname
        self.Email=email
        self.Description=description
        self.Role=role
        self.Provider=provider
        self.IdpUsername=idpUsername
        self.Level=level
        self.Fullname=fullname
        self.Type=atype
        self.Access=access
        self.PreferredView=preferredView
        self.Tags=tags
        self.Culture=culture
        self.Region=region
        self.Thumbnail_link=thumbnail_link
        self.Items=itemsContent
        self.Folders=folders
        

        
class ArcGISServer:
    CSVHEADER = "FOLDER_NAME|SERVICE_NAME|DESCRIPTION|TYPE|MIN_INSTANCES|MAX_INSTANCES|CAPABILITIES|PROP_filePath|PROP_outputDir|PROP_virtualOutputDir|PROP_supportedImageReturnTypes|PROP_maxRecordCount|PROP_maxSampleSize|PROP_exportTilesAllowed|PROP_maxExportTilesCount|PROP_cacheDir|PROP_useLocalCacheDir|PROP_maxImageHeight|PROP_maxBufferCount|PROP_maxImageWidth|PROP_enableDynamicLayers|PROP_dynamicDataWorkspaces|PROP_disableIdentifyRelates|PROP_schemaLockingEnabled|PROP_maxDomainCodeCount|PROP_isCached|PROP_cacheOnDemand|PROP_ignoreCache|PROP_clientCachingAllowed|PROP_antialiasingMode|PROP_textAntialiasingMode|PROP_minScale|PROP_maxScale|PROP_portalURL|PROP_userName|PROP_virtualCacheDir|PROP_connectionString|PROP_maximumRecords|PROP_jobsDirectory|PROP_showMessages|PROP_executionType|PROP_toolbox|PROP_jobsVirtualDirectory|PROP_resultMapServer\n"
    LINE = ""
    @property
    def ListServices(self):
        return self._listServices
    @ListServices.setter
    def ListServices(self, value):
        self._listServices = value
    def __init__(self):
        self.ListServices=[]
        c = self.CSVHEADER.split("|")
        x = range(len(c))

        for i in x:
            if (len(c)==i+1):
                self.LINE=self.LINE+"{"+str((i))+"}"
            else:
                self.LINE=self.LINE+"{"+str((i))+"}|"
            
            
        
    def AddWS(self, ws):
        Log.info("Adicionando Servicio")
        self.ListServices.append(ws)
        
    def SaveListServices2CSV(self,aFile):
        try:
            Log.debug("Ingresando a SaveListServices2CSV")
            csvFile = open(aFile, "w")
            csvFile.write(self.CSVHEADER)
            
            print(self.LINE)
            for s in self.ListServices:
                line = self.LINE.format(
                                        s.FolderName,
                                        s.ServiceName,
                                        s.Description.replace("\n","").replace("|",""),
                                        s.Type,
                                        s.MinInstancesPerNode,
                                        s.MaxInstancesPerNode,
                                        s.Capabilities,
                                        s.Properties.get("filePath"),
                                        s.Properties.get("outputDir"),
                                        s.Properties.get("virtualOutputDir"),
                                        s.Properties.get("supportedImageReturnTypes"),
                                        s.Properties.get("maxRecordCount"),
                                        s.Properties.get("maxSampleSize"),
                                        s.Properties.get("exportTilesAllowed"),
                                        s.Properties.get("maxExportTilesCount"),
                                        s.Properties.get("cacheDir"),
                                        s.Properties.get("useLocalCacheDir"),
                                        s.Properties.get("maxImageHeight"),
                                        s.Properties.get("maxBufferCount"),
                                        s.Properties.get("maxImageWidth"),
                                        s.Properties.get("enableDynamicLayers"),
                                        s.Properties.get("dynamicDataWorkspaces"),
                                        s.Properties.get("disableIdentifyRelates"),
                                        s.Properties.get("schemaLockingEnabled"),
                                        s.Properties.get("maxDomainCodeCount"),
                                        s.Properties.get("isCached"),
                                        s.Properties.get("cacheOnDemand"),
                                        s.Properties.get("ignoreCache"),
                                        s.Properties.get("clientCachingAllowed"),
                                        s.Properties.get("antialiasingMode"),
                                        s.Properties.get("textAntialiasingMode"),
                                        s.Properties.get("minScale"),
                                        s.Properties.get("maxScale"),    
                                        s.Properties.get("portalURL"),
                                        s.Properties.get("userName"),
                                        s.Properties.get("virtualCacheDir"),
                                        s.Properties.get("connectionString"),
                                        s.Properties.get("maximumRecords"),
                                        s.Properties.get("jobsDirectory"),
                                        s.Properties.get("showMessages"),
                                        s.Properties.get("executionType"),
                                        s.Properties.get("toolbox"),
                                        s.Properties.get("jobsVirtualDirectory"),
                                        s.Properties.get("resultMapServer")
                                        
                                        )
                csvFile.write(line+"\n")
            csvFile.close()
        except:
            Log.error(str((sys.exc_info()[0])) + " " + str((sys.exc_info()[1])))
    
      

    def ExportConfigFiles(self,destFolder):
        if(not os.path.isdir(destFolder)):
            os.mkdir(destFolder)
        
        for s in self.ListServices:
            print(s.ConfigFileOrig)
            print(s.ConfigFileOrig.split("\\")[-3])
            
            origFolder=(s.ConfigFileOrig.split("extracted")[0]+"extracted").replace("\\","/")
            createFolder = "{0}-{1}".format(s.FolderName,
                                                        s.ConfigFileOrig.split("\\")[-3])
            print ("origFolder:"+origFolder)
            
#             print("createFolder:{}".format(createFolder))
            destPath = os.path.join(destFolder,createFolder)
#             if(not os.path.isdir(destPath)):
#                 os.mkdir(destPath)
            print("destPath:"+destPath)
            shutil.copytree(origFolder,destPath)
        
            

class WebService:
    @property
    def FolderName(self):
        return self._folderName
    @FolderName.setter
    def FolderName(self, value):
        self._folderName = value
    @property
    def ServiceName(self):
        return self._serviceName
    @ServiceName.setter
    def ServiceName(self, value):
        self._serviceName = value
    @property
    def Type(self):
        return self._type
    @Type.setter
    def Type(self, value):
        self._type = value
    @property
    def Capabilities(self):
        return self._capabilities
    @Capabilities.setter
    def Capabilities(self, value):
        self._capabilities = value
    @property
    def MinInstancesPerNode(self):
        return self._minInstancesPerNode
    @MinInstancesPerNode.setter
    def MinInstancesPerNode(self, value):
        self._minInstancesPerNode = value
    @property
    def MaxInstancesPerNode(self):
        return self._maxInstancesPerNode
    @MaxInstancesPerNode.setter
    def MaxInstancesPerNode(self, value):
        self._maxInstancesPerNode = value
    @property
    def Extensions(self):
        return self._extensions
    @Extensions.setter
    def Extensions(self, value):
        self._extensions = value
    @property
    def Provider(self):
        return self._provider
    @Provider.setter
    def Provider(self, value):
        self._provider = value
    @property
    def Properties(self):
        return self._properties
    @Properties.setter
    def Properties(self, value):
        self._properties = value
    
    @property
    def Description(self):
        return self._description
    @Description.setter
    def Description(self, value):
        self._description = value
        
    @property
    def ConfigFileOrig(self):
        return self._configFileOrig
    @ConfigFileOrig.setter
    def ConfigFileOrig(self, value):
        self._configFileOrig = value
    
    
    def __init__(self,data,aFile):
        Log.debug("Ingresando Constructor WebService")
        Log.debug(data)
        self.ConfigFileOrig=aFile
        self.Capabilities=data["service"]["capabilities"]
        self.Extensions=data["service"]["extensions"]
        self.FolderName=data["folderName"]
        self.MaxInstancesPerNode=data["service"]["maxInstancesPerNode"]
        self.MinInstancesPerNode=data["service"]["minInstancesPerNode"]
        self.Provider=data["service"]["provider"]
        self.ServiceName=data["service"]["serviceName"]
        self.Type=data["service"]["type"]
        self.Properties=data["service"]["properties"]
        self.Description=data["service"]["description"]
        
        
    
    
