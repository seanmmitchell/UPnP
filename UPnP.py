from colorama import Fore, Style
from enum import Enum
from threading import Lock
import upnpclient

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

# Discover
Out(OutSev.Info, "Starting UPnP discovery...")
upnpclient.util.logging.disable()
devices = upnpclient.discover(2)
for device in devices:
    DeviceOutput(device)
Out(OutSev.Info, "UPnP Discovery Complete...")

#parse input

#exec
for device in devices:
    if(hasattr(device, "Layer3Forwarding1")):
        AddPortMapping(device, "", 10003, "UDP", "192.168.1.15", 10003, "TEST upnpclient in Py3", NewEnabled="1", Duration=0)
