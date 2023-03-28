#! /usr/bin/env python3
from bitstring import BitStream
import spiceypy as spice
from datetime import datetime, timedelta
from rich.console import Console


class PacketId:
    def __init__(self,data):
        pID = BitStream(hex=data).unpack('uint: 3, 2*bin: 1, bits: 11')
        self.VersionNum = pID[0]
        self.packetType = pID[1]
        self.dataFieldHeaderFlag = pID[2]
        self.Apid = pID[3].uint
        self.Pid = pID[3][0:7].uint
        self.Pcat = pID[3][7:].uint
        pass
    def serialize(self):
        return [self.VersionNum, self.packetType, self.dataFieldHeaderFlag,
                self.Apid, self.Pid, self.Pcat]

class SeqControl:
    def __init__(self,data):
        sq = BitStream(hex=data).unpack('bin:2,uint:14')
        self.SegmentationFlag = sq[0]
        self.SSC = sq[1]

    def serialize(self):
        return [self.SegmentationFlag, self.SSC]

class SourcePacketHeader:
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
    def serialize(self):
        return [*self.packetId.serialize(), *self.sequeceControl.serialize(), self.packetLength]

class DataFieldHeader:
    def __init__(self,data,missionID,t0):
        # Read The Data Field Header (80 bit)
        dfhData = BitStream(hex=data).unpack('bin:1,uint:3,bin:4,3*uint:8,uint:1,uint:31,uint:16')
        self.pusVersion = dfhData[1]
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
            self.UTCTime = '1970-01-01T00:00:00.00000Z'
        pass

    def serialize(self):
        return [self.pusVersion, self.ServiceType, self.ServiceSubType,
                self.DestinationId, self.SCET, self.UTCTime]

    def scet2UTC(self,missionID,t0):
        if t0 == None:
            et = spice.scs2e(missionID, "{}.{}".format(self.CorseTime, self.FineTime))
            ScTime = spice.et2utc(et, 'ISOC', 5)
        else:
            dateFormat = "%Y-%m-%dT%H:%M:%S.%f"
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
    def __init__(self, missionID, data,console:Console=None,t0= None):
        if type(missionID) is str:
            if missionID.lower() == 'bepicolombo':
                missionID=-121
            elif missionID.lower() == 'juice':
                missionID=-29
            else:
                if t0 == None:
                    print("WARNING: the Mission name is not valid. time converte setted to 1970-01-01 00:00:00")
                    t0 = "1970-01-01T00:00:00"
        # Source Packet Header
        self.SPH = SourcePacketHeader(data[0:12])
        # Packet Data Field
        self.PDF = PackeDataField(data[12:],missionID,t0)
        self.APID = self.SPH.packetId.Apid
        self.Service=self.PDF.DFHeader.ServiceType
        self.subService=self.PDF.DFHeader.ServiceSubType
        self.Data=self.PDF.Data

