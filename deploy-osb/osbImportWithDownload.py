# Carrega as classes do python.
import os
import ConfigParser
import sys
import wlstModule
import sys
import threading
import time
import types
import urllib
import re
import shutil

# Carrega as classes do JAVA.
from java.io import File
from java.io import FileInputStream
from java.io import FileReader
from java.lang import Exception
from java.util import ArrayList
from java.util import Collections
from java.util import *

#carrega a classe do yamlbeans
from com.esotericsoftware.yamlbeans import YamlReader

# Carrega as do WLS e OSB para deploy.
from com.bea.wli.config import Ref
from com.bea.wli.monitoring import StatisticType
from com.bea.wli.config.customization import Customization
from com.bea.wli.sb.management.importexport import ALSBImportOperation
from com.bea.wli.sb.management.configuration import SessionManagementMBean
from com.bea.wli.sb.management.configuration import ALSBConfigurationMBean
from com.bea.wli.sb.management.configuration import CommonServiceConfigurationMBean
from com.bea.wli.config.resource import Diagnostics
from com.bea.wli.config.importexport import ImportResult

from org.apache.xmlbeans import XmlException

#===================================================================
# Utility function to print the list of operations
#===================================================================
def printOpMap(map):
    set = map.entrySet()
    for entry in set:
        op = entry.getValue()
        print op.getOperation(),
        ref = entry.getKey()
        print ref
    print

#===================================================================
# Utility function to print the diagnostics
#===================================================================
def printDiagMap(map):
    set = map.entrySet()
    for entry in set:
        diag = entry.getValue().toString()
        print diag
    print

#===================================================================
# Utility function to load properties from a config file
#===================================================================
def loadProps(configPropFile):
    propInputStream = FileInputStream(configPropFile)
    configProps = Properties()
    configProps.load(propInputStream)
    return configProps

#===================================================================
# Connect to the Admin Server
#===================================================================
def connectToServer(username, password, url):
    connect(username, password, url)
    domainRuntime()

def connectToServerUsingConfig(userConfig, keyFile, admUrl):
    connect(userConfigFile=userConfig,userKeyFile=keyFile, url=admUrl)
    domainRuntime()

#===================================================================
# Utility function to read a binary file
#===================================================================
def readBinaryFile(fileName):
    file = open(fileName, 'rb')
    bytes = file.read()
    return bytes

#===================================================================
# Utility function to create an arbitrary session name
#===================================================================
def createSessionName(sessionName):
    sessionName = String(sessionName)
    return sessionName

#===================================================================
# Utility function to load a session MBeans
#===================================================================
def getSessionManagementMBean(sessionName):
    sessionMBean = findService(SessionManagementMBean.NAME,SessionManagementMBean.TYPE)
    sessionMBean.createSession(sessionName)
    return sessionMBean

#===================================================================
# Utility function to download osb jar import file
#===================================================================
def download_file(url,dest,filename):
    testfile = urllib.URLopener()
    global filepath
    filepath = dest + 'sbimport_'+ filename + '/'

    print "creating the directory: " + filepath
    if not os.path.exists(filepath):
     os.makedirs(filepath)

    testfile.retrieve(url,filepath + filename)

#===================================================================
# Utility function to get osb jar import file name
#===================================================================

def file_name(url):
    path = re.search('.*\/(?P<filename>.*)', url)
    filename = path.group("filename")
    return filename

#===================================================================
# Utility to set weblogic connect arguments.
#===================================================================

def __set_connect_args__(env, yaml_data):
    global username
    global password
    global url_admin

    if env == 'prod':
        username = yaml_data['environment'][env][color]['user']
        password = yaml_data['environment'][env][color]['password']
        url_admin = yaml_data['environment'][env][color]['url']
    else:
        username = yaml_data['environment'][env]['user']
        password = yaml_data['environment'][env]['password']
        url_admin = yaml_data['environment'][env]['url']

#===================================================================
# Utility to parse yml environment file.
#===================================================================

def __parse_yaml__(filename):
    reader = YamlReader(FileReader(filename))
    yaml = reader.read()
    return yaml


try:
    # import the service bus configuration
    # argv[1] is the config properties file
    global color
    global env

    print("jar is ",sys.argv)

    configFile = os.getcwd() + '/conf/environment.yml'

    print "parse general environment yml"
    yaml_data = __parse_yaml__(configFile)

    env = sys.argv[1]

    if env == "prod":
        if sys.argv[4] in 'customization_file':
            color = sys.argv[2]
            preserve = sys.argv[3]
            customFileUrl = sys.argv[5]
            val = 6
        else:
            color = sys.argv[2]
            preserve = sys.argv[3]
            val = 4
            customFileUrl = ""
    else:
        if sys.argv[3] in 'customization_file':
            color = ""
            preserve = sys.argv[2]
            customFileUrl = sys.argv[4]
            val = 5
        else:
            color = ""
            preserve = sys.argv[2]
            val = 3
            customFileUrl = ""

    basePath = yaml_data['general_info']['basepath']
    SessionMBean = None
    ## TO-DO ##

    global customFile
    customFile = ""
    if customFileUrl:
        custom_file_name = file_name(customFileUrl)
        download_file(customFileUrl,basePath,custom_file_name)
        custom_file_path = filepath + custom_file_name
        print("custom_file_path is " + custom_file_path)
        customFile = custom_file_path


    sessionName =  yaml_data['general_info']['session_name']

    __set_connect_args__(env, yaml_data)

    print 'Loading user credentials config from :', configFile

    print 'URL:', url_admin

    connectToServer(username, password, url_admin)

    for i in range(val,len(sys.argv)):
      try:

       url_artifactory = sys.argv[i]
       importJarFile = file_name(url_artifactory)

       print "download osb import jar from : ", url_artifactory
       download_file(url_artifactory,basePath,importJarFile)


       sessionDesc = "Import jar " + importJarFile + " automatically"

       print 'Loading Deployment config from :', configFile
       print 'sessionName', sessionName
       print 'sessionDesc', sessionDesc

       preserveEnvironmentValues = (preserve == 'true')
       preserveExistingOperationalValues = (preserve == 'true')
       preserveExistingSecurityAndPolicyConfig = (preserve == 'true')
       preserveExistingAccessControlPolicies = (preserve == 'true')
       preserveExistingCredentials = ( preserve == 'true')


       importJar = filepath + importJarFile

       print 'Attempting to import:', importJar, "on OSB Admin Server listening on: ", url_admin

       print 'Reading file', importJar
       theBytes = readBinaryFile(importJar)

       #print 'Creating session', sessionName
       sessionName = createSessionName(sessionName)
       print 'Starting SessionMBean session'

       # get session Mbean
       SessionMBean = findService(SessionManagementMBean.NAME, SessionManagementMBean.TYPE)
       print 'SessionMBean', SessionMBean
       SessionMBean.createSession(sessionName)

       #print 'ALSBConfiguration MBean found', ALSBConfigurationMBean
       ALSBConfigurationMBean = findService(String(ALSBConfigurationMBean.NAME + ".").concat(sessionName), ALSBConfigurationMBean.TYPE)

       print 'Uploading Jar'
       ALSBConfigurationMBean.uploadJarFile(theBytes)

       print 'Preparing import plan'
       alsbJarInfo = ALSBConfigurationMBean.getImportJarInfo()

       print 'Setting preserve flags'
       alsbImportPlan = alsbJarInfo.getDefaultImportPlan()
       alsbImportPlan.setPreserveExistingEnvValues(preserveEnvironmentValues)
       alsbImportPlan.setPreserveExistingOperationalValues(preserveExistingOperationalValues)
       alsbImportPlan.setPreserveExistingSecurityAndPolicyConfig(preserveExistingSecurityAndPolicyConfig)
       alsbImportPlan.setPreserveExistingAccessControlPolicies(preserveExistingAccessControlPolicies)
       alsbImportPlan.setPreserveExistingCredentials(preserveExistingCredentials)

       print 'Importing resources'
       importResult = ALSBConfigurationMBean.importUploaded(alsbImportPlan)

       if importResult.getImported().size() > 0:
           for res in importResult.getImported():
               print "<INFO> - Efetuando deploy do processo %s" % res.toString()
       if importResult.getImportDiagnostics().size() > 0:
           for res2 in importResult.getImportDiagnostics().values():
               print "<WARNING> - %s " % res2.toString()
       if importResult.getFailed().size() > 0:
           for importa in importResult.getFailed().values():
               print "<ERROR> - %s " % importa.toString()
               print "Excecao ocorrido durande o deploy, favor verificar os logs para mais informa��es!"


       if importResult.getFailed().size() > 0:
           print 'One or more resources could not be imported properly'
           print 'The following resources failed to import'
           for entry in importResult.getFailed().entrySet():
               ref = entry.getKey()
               diagnostics = entry.getValue().toString()
               print ref + " Reason: " + diagnostics
           raise

       ######## TO-DO ############################
       #customize if a customization file is specified
       #affects only the created resources
       if customFile:
            print 'Loading customization File', customFile
            iStream = FileInputStream(customFile)
            customizationList = Customization.fromXML(iStream)
            ALSBConfigurationMBean.customize(customizationList)

       SessionMBean.activateSession(sessionName, sessionDesc)
       print
       print "Deployment of: " + importJar + " finished successfully"

       print "deleting the directory: " + filepath
       if os.path.exists(filepath):
        shutil.rmtree(filepath)

      except Exception, e:
        try:
          if os.path.exists(filepath):
             shutil.rmtree(filepath)

             SessionMBean.discardSession(sessionName)
        except:
         print "Nao existe sessao criada"
         print e
        pass

    disconnect()

except Exception, e:
    print e
    print "Unexpected error: ", sys.exc_info()[0]
    dumpStack()
