from io import BufferedWriter
from threading import Lock
import struct

from .events import OPMWriteEvent


class OPMController:
    def __init__(self, chip):
        self.chip = chip
        self.realtime = None if chip is None else chip.realtime
        self.registers = []
        self._clear_registers()

    def _clear_registers(self):
        self.registers.clear()
        for _ in range(0, 0x100):
            self.registers.append(None)

    def write_event(self, event):
        if isinstance(event, OPMWriteEvent):
            self.write(event.reg, event.value)

    def write(self, reg, value):
        reg = reg & 0xff
        if self.registers[reg] != value:
            if self.chip is not None:
                self.chip.write(reg, value)
            self.registers[reg] = value

    def read(self, reg, default=None):
        reg = reg & 0xff
        return default if self.registers[reg] is None else self.registers[reg]

    def wait(self, time):
        if self.chip is not None:
            self.chip.wait(time)

    def flush(self):
        if self.chip is not None:
            self.chip.flush()

    def reset(self):
        self._clear_registers()
        if self.chip is not None:
            self.chip.reset()

    def close(self):
        if self.chip is not None:
            self.chip.close()

    def all_notes_off(self):
        # TODO: Implement this for OPM
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class OPMChip:
    realtime = True

    def write(self, reg, value):
        raise NotImplementedError()

    def flush(self):
        raise NotImplementedError()

    def wait(self, wait_time):
        pass

    def reset(self):
        raise NotImplementedError()

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class OPMUSBSerial(OPMChip):
    def __init__(self, device_path):
        from serial import Serial
        self.device = BufferedWriter(Serial(device_path, 115200))

    def write(self, reg, value):
        reg = reg & 0xff
        value = value & 0xff
        self.device.write(struct.pack('<BBB', 0, reg, value))

    def flush(self):
        self.device.flush()

    def reset(self):
        self.device.write(b'\xff\x00\x01')
        self.flush()

    def close(self):
        self.device.close()


class OPMWAV(OPMChip):
    realtime = False

    def __init__(self, wav_path, sample_rate=55930):
        import wave
        from notesalad import opm
        self.sample_rate = sample_rate
        self.wav = wave.open(wav_path, 'wb')
        self.wav.setnchannels(2)
        self.wav.setsampwidth(2)
        self.wav.setframerate(self.sample_rate)
        self.opm_device = opm.OPMEmulator(self.sample_rate)

    def write(self, reg, value):
        reg = reg & 0xff
        self.opm_device.write(reg, value)

    def wait(self, wait_time):
        if wait_time <= 0:
            return
        samples = round(wait_time * self.sample_rate)
        while samples > 0:
            buffersamples = min(samples, 11025)
            buffer = bytearray(buffersamples * 4)
            self.opm_device.get_samples(buffer)
            self.wav.writeframes(buffer)
            samples -= buffersamples

    def flush(self):
        raise NotImplementedError()

    def reset(self):
        self.opm_device.reset()

    def close(self):
        self.wav.close()


class OPMEmulator(OPMChip):
    def __init__(self, sample_rate=44100):
        import pyaudio
        from notesalad import opm
        self.sample_rate = sample_rate
        self.pyaudio = pyaudio
        self.opm = opm
        self._write_queue = []
        self._queue_lock = Lock()
        self.p = pyaudio.PyAudio()
        self.opm_device = opm.OPMEmulator(self.sample_rate)
        self.stream = self.p.open(format=pyaudio.paInt16, channels=2, rate=self.sample_rate,
                                  output=True)

    def write(self, reg, value):
        reg = reg & 0x1ff
        self.opm_device.write(reg, value)

    def reset(self):
        self.opm_device.reset()

    def flush(self):
        pass

    def wait(self, wait_time):
        if wait_time <= 0:
            return
        samples = round(wait_time * self.sample_rate)
        while samples > 0:
            buffersamples = min(samples, 11025)
            buffer = bytearray(buffersamples * 4)
            self.opm_device.get_samples(buffer)
            self.stream.write(bytes(buffer))
            samples -= buffersamples

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
