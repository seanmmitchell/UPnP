from colorama import Fore, Style
from enum import Enum
from sys import argv, exit, stdout
from threading import Lock
import upnpclient
import socket

## Log Levels
OutputLevel = 4
class OutSev(Enum):
    Critical = 0
    Error = 1
    Warning = 2
    Info = 3
    Debug = 4
##

LockOutput = Lock()

def Out(Sev, Message, File=False):
    # Add file implementation for scripting usage
    if(Sev.value <= OutputLevel):
        LockOutput.acquire()

        if(Sev == OutSev.Critical):
            print(" %s%s[%s]%s%s %s" % ((Fore.RED, Style.BRIGHT, Sev.name, Fore.WHITE, Style.NORMAL, Message)))
        elif(Sev == OutSev.Error):
            print(" %s%s[%s]%s%s %s" % ((Fore.RED, Style.NORMAL, Sev.name, Fore.WHITE, Style.NORMAL, Message)))
        elif(Sev == OutSev.Warning):
            print(" %s%s[%s]%s%s %s" % ((Fore.YELLOW, Style.NORMAL, Sev.name, Fore.WHITE, Style.NORMAL, Message)))
        elif(Sev == OutSev.Info):
            print(" %s%s[%s]%s%s %s" % ((Fore.WHITE, Style.NORMAL, Sev.name, Fore.WHITE, Style.NORMAL, Message)))
        elif(Sev == OutSev.Debug):
            print(" %s%s[%s]%s%s %s" % ((Fore.CYAN, Style.NORMAL, Sev.name, Fore.WHITE, Style.NORMAL, Message)))
        else:
            print(Sev + " - " + Message)    

        stdout.flush()
        LockOutput.release()
        return
    else:
        # ignored
        return

def PortMappingRestrictions(device):
    print(device.WANIPConn1.AddPortMapping.argsdef_in)

def AddPortMapping(device, RemoteHost, ExternalPort, Protocol, InternalHost, InternalPort, Description, NewEnabled="1", Duration=7200):
    devicePublicIP = device.WANIPConn1.GetExternalIPAddress()["NewExternalIPAddress"]
    Out(OutSev.Info, "UPnP Port Mapping | %s(%s):%s ---> %s:%s (%s) | (Desc: %s) (Enabled: %s) (Duration: %s)" % (RemoteHost,devicePublicIP,ExternalPort,InternalHost,InternalPort,Protocol,Description,("True" if (NewEnabled == "1") else "False"),("Infinite" if (Duration == 0) else str(Duration) + "s")))
    try:
        device.WANIPConn1.AddPortMapping(
            NewRemoteHost=RemoteHost,
            NewExternalPort=ExternalPort,
            NewProtocol=Protocol,
            NewInternalPort=InternalPort,
            NewInternalClient=InternalHost,
            NewEnabled=NewEnabled,
            NewPortMappingDescription=Description,
            NewLeaseDuration=Duration
        )
        Out(OutSev.Info, "UPnP Port Mapped | %s(%s):%s ---> %s:%s (%s)" % (RemoteHost,devicePublicIP,ExternalPort,InternalHost,InternalPort,Protocol))
    except upnpclient.soap.SOAPError as e:
        errid = int(str(e)[1:4]) # this is def wrong right??
        if(errid == 725):
            Out(OutSev.Critical, "Failed UPnP Port Mapping | OnlyPermanentLeasesSupported - Set duration to 0 (infinite)")
        elif(errid == 726):
            Out(OutSev.Critical, "Failed UPnP Port Mapping | RemoteHostOnlySupportsWildcard - Leave empty remote host.")
        

def Dump(obj):
    Out(OutSev.Debug, "Dumping Obj: " + str(obj))
    ## Methods
    object_methods = [method_name for method_name in dir(obj)
        if callable(getattr(obj, method_name))]
    obj_meth_str = ""
    for method in object_methods:
        obj_meth_str += (method + " ")
    Out(OutSev.Debug, "\tMethods:" + obj_meth_str)
    ## Attributes
    object_attr = [attr for attr in dir(obj)
        if not callable(getattr(obj, attr))]
    object_attr_str = ""
    for attr in object_attr:
        object_attr_str += (attr + " ")
    Out(OutSev.Debug, "\tAttributes:" + object_attr_str)

def DeviceOutput(device):
    Out(OutSev.Debug, "Device Name: %s" % (device.friendly_name))
    Out(OutSev.Debug, "\tGeneral:")
    Out(OutSev.Debug, "\t\tDevice Location: %s" % (device.device_name))
    Out(OutSev.Debug, "\t\tDevice Maker & Model: %s | %s" % (device.manufacturer, device.model_name))
    Out(OutSev.Debug, "\t\tDevice Description: %s" % (device.model_description))
    Dump(device)
    if(hasattr(device, 'WANIPConn1')):
        Out(OutSev.Debug, "\tWANIPConn1:")
        NATCapable = device.WANIPConn1.GetNATRSIPStatus()
        Out(OutSev.Debug, "\t\tDevice NAT Enabled: %s" % (NATCapable["NewNATEnabled"]))
        Out(OutSev.Debug, "\t\tDevice Public IP: %s" % (device.WANIPConn1.GetExternalIPAddress()["NewExternalIPAddress"]))
    Out(OutSev.Debug, "\tSERVICES:")
    if(hasattr(device, "Layer3Forwarding1")):
        Out(OutSev.Debug, "\t\tLayer 3 Forwarding: True")


# Usage read out
def usage ():
    print('''USAGE:\n\nUPnP.py\n
Gives a CLI interface for easy UPnP management.\n\n
\t--log (Critical (0) Error (1) Warning (2) Info (3) Debug (4))\t\t Sets a max log level for the application.
\tmap\tExternalPort\tProtocol\tInternalHost\tInternalPort\tDescription \t\t Creates a port mapping. Leave InternalHost "" to autofill.''')

# Temp Set New Output Level to Default Output Level
newOutputLevel = OutputLevel

# port map operation
Map = ""
ExternalPort = ""
Protocol = ""
InternalHost = ""
InternalPort = ""
Description = ""

for x in range(len(argv)):
    arg = argv[x]
    if arg == "--log":
        try:
            newOutputLevel = argv[x+1]
        except IndexError as ie:
            Out(OutSev.Critical, "No log level given.")
            usage()
            exit(0)

        try:
            newOutputLevel = int(newOutputLevel)

            if newOutputLevel > 4 or newOutputLevel < 0:
                Out(OutSev.Critical, "Invalid new log level given.")
                usage()
                exit(0)

            Out(OutSev.Info, "Setting the new output level to: %s" % (OutSev(newOutputLevel).name))
            #OutputLevel = newOutputLevel SET LATER, NOT HERE
        except Exception as e:
            Out(OutSev.Critical, "Failed to parse new log level.")
            usage()
            exit(0)
    elif arg == "map":
        try:
            Map = "true"
            ExternalPort = int(argv[x+1])
            Protocol = argv[x+2]
            InternalHost = argv[x+3]
            InternalPort = int(argv[x+4])
            Description = argv[x+5]
        except:
            Map = "false"
    elif (arg == "-h" or arg == "--h") or (arg == "-help" or arg == "--help"):
        usage()
        quit(0)
        
# now set
OutputLevel = newOutputLevel

# Discover
Out(OutSev.Info, "Starting UPnP discovery...")
upnpclient.util.logging.disable(100)
devices = upnpclient.discover(2)
for device in devices:
    DeviceOutput(device)
Out(OutSev.Info, "UPnP Discovery Complete...")

#exec

if Map == "true":
    if InternalHost == "":
      hostname = socket.gethostname()
      InternalHost = socket.gethostbyname(hostname)
    for device in devices:
        if(hasattr(device, "Layer3Forwarding1")):
            AddPortMapping(device, "", ExternalPort, Protocol, InternalHost, InternalPort, Description, NewEnabled="1", Duration=0)
