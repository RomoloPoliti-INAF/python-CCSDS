# CCSDSpy

CCSDSpy is a library to read a data packet coming from a space mission that follows the Consultative Committee for Space Data Systems (CCSDS) standard

Current version **0.1.0**

Installation
Usage
```python
from CCSDS import CCSDS

dat = CCSDS('BepiColombo',packet)
```
wehre *packet* is a string with the HEX rappresentation of the pachet

Limitation

## Data Structure

The CCSDS Header is composed by two blocks 


![TM packet](docs/TM_Packet_H_eader.png)
