#! /usr/bin/env python3
from bitstring import BitStream
import spiceypy as spice
from datetime import datetime, timedelta
from rich.console import Console
from PyCCSDS.dic2table import dict2table
import types


__version__ = "0.2.0"
dateFormat = "%Y-%m-%dT%H:%M:%S.%fZ"
missions = {"bepicolombo": -121, "juice": -29}


def isclass(obj):
    """Return true if the obj is a class.

    Class objects provide these attributes:
        __doc__         documentation string
        __module__      name of module in which this class was defined"""
        
    
    return hasattr(obj,'serialize') and callable(obj.serialize) 


class Seriazable:
    def serialize(self)->dict:
        ret={}
        for item in self.__dict__.items():
            if isclass(item[1]):
                ret[item[0]]=item[1].serialize()
            else:
                ret[item[0]]=item[1]
        return ret

class PacketType(Seriazable):
    
    def __init__(self,tp):
        self.type = tp
        if tp == 0:
            self.typeName = "Telemetry"
        else:
            self.typeName = "Telecommand"
        pass
    
    def __str__(self):
        return self.typeName
    
    def __repr__(self) -> str:
        return self.__str__()

class PacketId(Seriazable):
    def __init__(self,data):
        pID = BitStream(hex=data).unpack('uint: 3, 2*bin: 1, bits: 11')
        self.VersionNum = pID[0]
        self.packetType = PacketType(int(pID[1]))
        self.dataFieldHeaderFlag = pID[2]
        self.Apid = pID[3].uint
        self.Pid = pID[3][0:7].uint
        self.Pcat = pID[3][7:].uint


class SeqControl(Seriazable):
    def __init__(self,data):
        sq = BitStream(hex=data).unpack('bin:2,uint:14')
        self.SegmentationFlag = sq[0]
        self.SSC = sq[1]


class SourcePacketHeader(Seriazable):
    def __init__(self,data):
        # Read the Source Packet Header(48 bits)
        # - Packet ID (16 bits)
        self.packetId = PacketId(data[0:4])
        # - Packet Sequence Control (16 bits)
        self.sequeceControl = SeqControl(data[4:8])
        """ 
        - Packet Length (16 bits)
        In the packet is stored Packet length is an unsigned word 
        expressing “Number of octects contained in Packet Data Field” minus 1.
        """
        self.packetLength = BitStream(hex=data[8:12]).unpack('uint:16')[0]+1
        # Based on BepiColombo SIMBIO-SYS
        # ref: BC-SIM-GAF-IC-002 pag. 48


class DataFieldHeader(Seriazable):
    def __init__(self,data,missionID,t0):
        # Read The Data Field Header (80 bit)
        dfhData = BitStream(hex=data).unpack('bin:1,uint:3,bin:4,3*uint:8,uint:1,uint:31,uint:16')
        self.pusVersion = int(dfhData[1])
        self.ServiceType = dfhData[3]
        self.ServiceSubType = dfhData[4]
        self.DestinationId = dfhData[5]
        self.Synchronization = dfhData[6]
        self.CorseTime = dfhData[7]
        self.FineTime = dfhData[8]
        self.SCET = "%s.%s" % (self.CorseTime, self.FineTime)
        if self.Synchronization == 0:
            self.UTCTime = self.scet2UTC(missionID,t0)
        else:
            self.UTCTime = datetime.strptime('1970-01-01T00:00:00.00000Z', dateFormat)
        pass

    
    def scet2UTC(self,missionID,t0):
        if t0 == None:
            et = spice.scs2e(missionID, "{}.{}".format(self.CorseTime, self.FineTime))
            ScTime = spice.et2utc(et, 'ISOC', 5)
        else:
            dt=datetime.strptime(t0,dateFormat)
            sc = self.CorseTime + self.FineTime*(2**(-16))
            f=dt+timedelta(seconds=sc)
            ScTime=f.strftime(dateFormat)
        return ScTime+'Z'

class PackeDataField:
    def __init__(self,data, missionID,t0):
        # Data Field Header
        self.DFHeader = DataFieldHeader(data[0:20],missionID,t0)
        # Data
        self.Data = data[20:]
        pass  


class CCSDS:
    """ Reader for the CCSDS header """
    def __init__(self, missionName, data,console:Console=Console(),t0= None):
        # Check Mission id and Name
        if isinstance(missionName, str):
            if missionName.lower() not in missions:
                console.print(f"WARNING: the Mission name is not valid. time converte setted to 1970-01-01 00:00:00",style="bold red")
                t0 = datetime.strptime("1970-01-01T00:00:00.0000Z", dateFormat)
            missionID=missions.get(missionName.lower(),None)
        else:
            missionID=missionName
        self.console=console
        self.missionName=missionName
        # Source Packet Header
        self.SPH = SourcePacketHeader(data[0:12])
        # Packet Data Field
        self.PDF = PackeDataField(data[12:],missionID,t0)
        self.APID = self.SPH.packetId.Apid
        self.Service=self.PDF.DFHeader.ServiceType
        self.subService=self.PDF.DFHeader.ServiceSubType
        self.Data=self.PDF.Data

    def __str__(self)->str:
        return f"{self.missionName.title()} - APID: {self.APID} - {'TM(' if self.SPH.packetId.packetType.type == 0 else 'TC('}{self.Service},{self.subService}) - Data: {self.Data}"

    def __repr__(self) -> str:
        return self.__str__()

    def show(self):
        from rich.panel import Panel
        from rich.columns import Columns
        c=Columns([Panel(dict2table(self.SPH.serialize()),title="Source Packet Header", border_style='magenta'),
                   Panel(dict2table(self.PDF.DFHeader.serialize(),reset=True),title="Data Field Header",border_style="magenta"),],
                  expand=False,equal=False)
        p=Panel(c,title=self.__str__(),style='yellow', expand=False)
        return p 
