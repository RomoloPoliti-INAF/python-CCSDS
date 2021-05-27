# CCSDSpy

---

CCSDSpy is a library to read a data packet coming from a space mission that follows the Consultative Committee for Space Data Systems (CCSDS) standard

Current version **0.1.0**

[[_TOC_]]

## Installation
## Usage
```python
from CCSDS import CCSDS

dat = CCSDS('BepiColombo',packet)
```
wehre *packet* is a string with the HEX rappresentation of the pachet

## Limitation

## Data Structure

The CCSDS Header is composed by two blocks:
+ the Source Packet Header 
+ the Packet Data Field

The first one il long 48 bits the second one has a varble dimension and structure depending by the type and the content of the packet. in [Figure 1](#figure-1-telemetry-packet) is reported the structure for a Telemetry Packet.

The structure of the CCSDS class follow the structure of the packet header.


```mermaid
classDiagram
    CCSDS --|> SPH
    CCSDS --|> PDF
    SPH --|> packetID
    SPH--|> sequenceControl
    PDF --|> DFHeader
    class CCSDS{
        + str Data 
    }
    class DFHeader{
        + uint PUSVersion
        + uint ServiceType
        + uint ServiceSubType
        + uint DestinationId
        + uint Synchronization
        + uint CorseTime
        + uint FineTime
        + str SCET
        + str  UTCTime
    }
    class SPH{
        + uint packetLength
    }
    class packetID{
        + uint VersionNum
        + uint packetType
        + uint dataFieldHeaderFlag 
        + uint Apid
        + uint Pid
        + uint Pcat
    }
    class sequenceControl{
        + bin SegmentationFlag
        + uint SSC
    }
    class PDF{
        +str Data
    }
```

![TM packet](docs/TM_Packet_Header.png "Telemetry packet")
####Figure 1 - Telemetry Packet
