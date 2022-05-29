from mido.ports import BaseOutput
from .opl import OPLWriteEvent, OPLController, OPLEmulator
from .opm import OPMWriteEvent, OPMController, OPMEmulator


class VGMMIDIOutput(BaseOutput):
    def _open(self, driver):
        self.driver = driver

    def set_time(self, time_ms):
        self.driver.set_time(time_ms)

    def update(self):
        self.driver.update()

    def _send(self, msg):
        self.driver.send(msg.bin())

    def _close(self):
        self.driver.close()


class OPL2MIDIOutput(VGMMIDIOutput):
    def _open(self, device):
        self.device = device
        from notesalad.opl import OPL2MIDI, OPLCallbackDevice
        driver = OPL2MIDI(OPLCallbackDevice(
            lambda reg, value: self._opl_write(reg, value), lambda: self._opl_reset()))
        super()._open(driver)
        driver.reset()

    def _opl_write(self, reg, value):
        self.device.write_event(OPLWriteEvent(0, reg, value))

    def _opl_reset(self):
        self.device.reset()


class OPL3MIDIOutput(VGMMIDIOutput):
    def _open(self, device):
        self.device = device
        from notesalad.opl import OPL3MIDI, OPLCallbackDevice
        driver = OPL3MIDI(OPLCallbackDevice(
            lambda reg, value: self._opl_write(reg, value), lambda: self._opl_reset()))
        super()._open(driver)
        driver.reset()
        self.device.write_event(OPLWriteEvent(0, 0x105, 1))

    def _opl_write(self, reg, value):
        self.device.write_event(OPLWriteEvent(0, reg, value))

    def _opl_reset(self):
        self.device.reset()


class OPMMIDIOutput(VGMMIDIOutput):
    def _open(self, device):
        self.device = device
        from notesalad.opm import OPMMIDI, OPMCallbackDevice
        driver = OPMMIDI(OPMCallbackDevice(
            lambda reg, value: self._opm_write(reg, value), lambda: self._opm_reset()))
        super()._open(driver)
        driver.reset()

    def _opm_write(self, reg, value):
        self.device.write_event(OPMWriteEvent(0, reg, value))

    def _opm_reset(self):
        self.device.reset()


class OPL2EmulatorOutput(OPL2MIDIOutput):
    def _open(self, **kwargs):
        device = OPLController(OPLEmulator())
        super()._open(**kwargs, device=device)

    def _close(self):
        super()._close()
        self.device.close()


class OPL3EmulatorOutput(OPL3MIDIOutput):
    def _open(self, **kwargs):
        device = OPLController(OPLEmulator())
        super()._open(**kwargs, device=device)

    def _close(self):
        super()._close()
        self.device.close()


class OPMEmulatorOutput(OPMMIDIOutput):
    def _open(self, **kwargs):
        device = OPMController(OPMEmulator())
        super()._open(**kwargs, device=device)

    def _close(self):
        super()._close()
        self.device.close()


class StdOutOutput(BaseOutput):
    def _send(self, msg):
        print(msg)
