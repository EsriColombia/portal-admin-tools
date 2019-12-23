# -*- coding: cp1252 -*-
import json,sys, os
import http.client
import urllib.request
import urllib.error
import urllib.parse
import logging

Log=logging.getLogger('__main__')

class security:    
    def getToken(self,username, password, serverName, serverPort):
        # Token URL is typically http://server[:port]/arcgis/admin/generateToken
        tokenURL = "/arcgis/admin/generateToken"

        # URL-encode the token parameters:-
        params = urllib.parse.urlencode({'username': username, 'password': password, 'client': 'requestip', 'f': 'json'})
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
         
        # Connect to URL and post parameters
        httpConn = http.client.HTTPSConnection(serverName, serverPort)
        httpConn.request("POST", tokenURL, params, headers)
        # Read response
        response = httpConn.getresponse()
        if (response.status != 200):
            httpConn.close()
            Log.error ("Error while fetch tokens from admin URL. Please check the URL and try again.")
            return
        else:
            data = response.read()
            httpConn.close()
            if ("error" in str(data)):
                err = json.loads(data)  
                Log.error ("Error: {}".format(err["messages"]))
            else:
                # Extract the token from it
                token = json.loads(data)        
                return token['token']