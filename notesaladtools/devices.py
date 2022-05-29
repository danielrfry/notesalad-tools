from .opl import OPLController, OPLUSBSerial, OPLWAV, OPLEmulator
from .opm import OPMController, OPMUSBSerial, OPMWAV, OPMEmulator


def get_device(name):
    if name == 'oplem':
        return OPLController(OPLEmulator())
    if name == 'opmem':
        return OPMController(OPMEmulator())

    parts = name.split(':', maxsplit=1)
    if len(parts) > 1:
        (devtype, path) = parts
        if devtype == 'oplser':
            return OPLController(OPLUSBSerial(path))
        if devtype == 'oplwav':
            return OPLController(OPLWAV(path))
        if devtype == 'opmser':
            return OPMController(OPMUSBSerial(path))
        if devtype == 'opmwav':
            return OPMController(OPMWAV(path))
    raise ValueError('Invalid device name')
