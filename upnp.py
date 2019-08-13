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
        

def DeviceOutput(device):
    print(" -[[ GENERAL ]]-\r\nDevice Name: %s\r\nDevice Location: %s\r\nDevice Maker & Model: %s | %s\r\nDevice Description: %s" % (device.friendly_name, device.device_name, device.manufacturer, device.model_name, device.model_description))
    if(hasattr(device, 'WANIPConn1')):
        print(" -[[ WANIPConn1 ]]-")
        NATCapable = device.WANIPConn1.GetNATRSIPStatus()
        print("Device NAT Enabled: %s" % (NATCapable["NewNATEnabled"]))
        print("Device Public IP: %s" % (device.WANIPConn1.GetExternalIPAddress()["NewExternalIPAddress"]))
    print(" -[[ SERVICES ]]-")
    if(hasattr(device, "Layer3Forwarding1")):
        print("Layer 3 Forwarding: True")

#parse input


Out(OutSev.Info, "Starting UPnP discovery...")
upnpclient.util.logging.disable()
devices = upnpclient.discover(2)
Out(OutSev.Info, "UPnP Discovery Complete...")

### DEBUG
#print("-----------------------------------------------------------")
#for device in devices:
#    #print(device)
#    DeviceOutput(device)
#    print("-----------------------------------------------------------")

for device in devices:
    if(hasattr(device, "Layer3Forwarding1")):
        AddPortMapping(device, "", 10003, "UDP", "192.168.1.15", 10003, "TEST upnpclient in Py3", NewEnabled="1", Duration=0)
