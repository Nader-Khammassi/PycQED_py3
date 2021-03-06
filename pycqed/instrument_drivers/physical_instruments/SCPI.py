'''
File:       SCPI.py
Author:     Wouter Vlothuizen, TNO/QuTech
Purpose:    base class for SCPI ('Standard Commands for Programmable
            Instruments') commands
Usage:      don't use directly, use a derived class (e.g. QWG)
Notes:
Bugs:
'''

from qcodes import IPInstrument
from qcodes import validators as vals

"""
FIXME: we would like to be able to choose the base class separately, so the
user can choose (e.g. use VISA for IEE488 bus units, and IpInstrument for
networked units). This would also make the inits cleaner
"""


class SCPI(IPInstrument):

    def __init__(self, name, address, port, **kwargs):
        super().__init__(name, address, port,
                         write_confirmation=False,  # required for QWG
                         **kwargs)
        # FIXME convert operation etc to parameters
        # IDN is implemented in the instrument base class

        # example of how the commands could look
        self.add_function('reset', call_cmd='*RST')

    def _recv(self):
        """
        Overwrites base IP recv command to ensuring read till EOM
        """

        resp = self._socket.makefile().readline().rstrip()
        return resp

    def ask_float(self, str):
        return float(self.ask(str))

    def ask_int(self, str):
        return int(self.ask(str))

    ###
    # Generic SCPI commands from IEEE 488.2 (IEC 625-2) standard
    ###

    def clearStatus(self):
        self.write('*CLS')

    def setEventStatusEnable(self, value):
        self.write('*ESE %d' % value)

    def getEventStatusEnable(self):
        return self.ask('*ESE?')

    def getEventStatusEnableRegister(self):
        return self.ask('*ESR?')

    def getIdentity(self):
        return self.ask('*IDN?')

    def operationComplete(self):
        self.write('*OPC')

    def getOperationComplete(self):
        return self.ask('*OPC?')

    def getOptions(self):
        return self.ask('*OPT?')

    def serviceRequestEnable(self, value):
        self.write('*SRE %d' % value)

    def getServiceRequestEnable(self):
        return self.ask_int('*SRE?')

    def getStatusByte(self):
        return self.ask_int('*STB?')

    def getTestResult(self):
        # NB: result bits are device dependent
        return self.ask_int('*TST?')

    def trigger(self):
        self.write('*TRG')

    def wait(self):
        self.write('*WAI')

    def reset(self):
        self.write('*RST')

    ###
    # Required SCPI commands (SCPI std V1999.0 4.2.1)
    ###

    def getError(self):
        ''' Returns:    '0,"No error"' or <error message>
        '''
        return self.ask('system:err?')

    def getSystemErrorCount(self):
        return self.ask_int('system:error:count?')

    def getSystemVersion(self):
        return self.ask('system:version?')

    ###
    # IEEE 488.2 binblock handling
    ###

    def binBlockWrite(self, binBlock, header):
        ''' write IEEE488.2 binblock
                Input:
                        binBlock    bytearray
                        header      string
        '''
        totHdr = header + SCPI.buildHeaderString(len(binBlock))
        binMsg = totHdr.encode() + binBlock
#       self.writeBinary(binMsg)
        self._socket.send(binMsg)       # FIXME: hack
        self.write('')                  # add a Line Terminator

    def binBlockRead(self):
        # FIXME: untested
        ''' read IEEE488.2 binblock
        '''
        # get and decode header
        headerA = self.readBinary(2)                        # consume '#N'
        # FIXME: Matlab code
        digitCnt = str2double(char(headerA(2)))
        headerB = obj.readBinary(digitCnt)
        byteCnt = str2double(char(headerB))

        # get binblock
        binBlock = obj.readBinary(byteCnt)
        self.readBinary(2)                                  # consume <CR><LF>
        return binBlock

    @staticmethod
    def buildHeaderString(byteCnt):
        ''' generate IEEE488.2 binblock header
        '''
        byteCntStr = str(byteCnt)
        digitCntStr = str(len(byteCntStr))
        binHeaderStr = '#' + digitCntStr + byteCntStr
        return binHeaderStr

    @staticmethod
    def getByteCntFromHeader(headerStr):
        ''' decode IEEE488.2 binblock header
        '''
        # FIXME: old Matlab code
        digitCnt = sscanf(headerStr, '#%1d')
        formatString = sprintf('%%%dd', digitCnt)           # e.g. '%3d'
        # byteCnt = sscanf(headerStr(3:end), formatString)        # NB: skip
        # first '#N'
        return byteCnt
