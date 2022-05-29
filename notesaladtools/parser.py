import os.path
import gzip
import struct
from .utils import read_struct
from .events import EndEvent, JumpToMarkerEvent, MarkerEvent, OPLWriteEvent, OPMWriteEvent


class Parser:
    def __init__(self, input_file):
        self.input_file = input_file
        self.time_base = None
        self.duration = None

    def read_events(self):
        raise NotImplementedError()

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class DROParser(Parser):
    def __init__(self, input_file):
        super().__init__(input_file)
        self.time_base = 1000
        self._read_header()

    def _read_header(self):
        dro_header = read_struct(
            self.input_file, '<8sHH', 'cSignature', 'iVersionMajor', 'iVersionMinor')
        if not (dro_header['iVersionMajor'] == 2 and dro_header['iVersionMinor'] == 0):
            raise Exception('Only version 2.0 DRO files are supported')

        dro2_header = read_struct(self.input_file, '<IIBBBBBB', 'iLengthPairs', 'iLengthMS', 'iHardwareType',
                                  'iFormat', 'iCompression', 'iShortDelayCode', 'iLongDelayCode', 'iCodemapLength')
        if dro2_header['iFormat'] != 0:
            raise Exception('Only interleaved DRO files are supported')

        self.event_count = dro2_header['iLengthPairs']
        self.duration = dro2_header['iLengthMS']
        self.hardware_type = dro2_header['iHardwareType']

        self._short_delay = dro2_header['iShortDelayCode']
        self._long_delay = dro2_header['iLongDelayCode']

        self.codemap = self.input_file.read(dro2_header['iCodemapLength'])
        self._start_pos = self.input_file.tell()

    def read_events(self):
        self.input_file.seek(self._start_pos)
        cur_time = 0
        for _ in range(1, self.event_count):
            code = self.input_file.read(1)[0]
            value = self.input_file.read(1)[0]
            if code == self._short_delay:
                cur_time = cur_time + value + 1
            elif code == self._long_delay:
                cur_time = cur_time + ((value + 1) << 8)
            elif code & 0x80:
                reg = self.codemap[code & 0x7f] | 0x100
                yield OPLWriteEvent(cur_time, reg, value)
            else:
                reg = self.codemap[code]
                yield OPLWriteEvent(cur_time, reg, value)
        yield EndEvent(max(cur_time, self.duration))

    def close(self):
        self.input_file.close()


class VGMParser(Parser):
    def __init__(self, input_file):
        super().__init__(input_file)
        self.time_base = 44100
        self._read_header()

    def _read_header(self):
        vgm_header = read_struct(self.input_file, '<4sIIIIIIII', 'ident', 'end_offset', 'ver',
                                 'sn76489clock', 'ym2413clock', 'gd3_offset', 'total_samples', 'loop_offset',
                                 'loop_samples')

        if vgm_header['ver'] < 0x150:
            raise Exception('Unsupported VGM version')

        self.input_file.seek(0x34)
        self._vgm_offset = read_struct(self.input_file, '<I', 'vgm_offset')[
            'vgm_offset'] + 0x34
        self._end_offset = vgm_header['end_offset'] + 4
        self.duration = vgm_header['total_samples']
        self._has_loop = vgm_header['loop_offset'] != 0 and vgm_header['loop_samples'] != 0
        self._loop_offset = vgm_header['loop_offset'] + 0x1c
        self._loop_samples = vgm_header['loop_samples']

    def read_events(self):
        self.input_file.seek(self._vgm_offset)

        cur_time = 0
        loop_start_time = 0
        loop_done = False
        while True:
            pos = self.input_file.tell()
            if pos >= self._end_offset:
                break

            if self._has_loop and pos == self._loop_offset:
                loop_start_time = cur_time
                yield MarkerEvent(cur_time, 0)

            cmd = self.input_file.read(1)[0]
            if cmd in (0x5a, 0x5e):
                reg = self.input_file.read(1)[0]
                value = self.input_file.read(1)[0]
                yield OPLWriteEvent(cur_time, reg, value)
            elif cmd == 0x5f:
                reg = self.input_file.read(1)[0] | 0x100
                value = self.input_file.read(1)[0]
                yield OPLWriteEvent(cur_time, reg, value)
            elif cmd == 0x54:
                reg = self.input_file.read(1)[0]
                value = self.input_file.read(1)[0]
                yield OPMWriteEvent(cur_time, reg, value)
            elif cmd == 0x61:
                samples = read_struct(self.input_file, '<H', 'samples')[
                    'samples']
                cur_time = cur_time + samples
            elif cmd == 0x62:
                cur_time = cur_time + 735
            elif cmd == 0x63:
                cur_time = cur_time + 882
            elif cmd == 0x66:
                break
            else:
                if (cmd & 0xf0) == 0x70:
                    samples = (cmd & 0xf) + 1
                    cur_time = cur_time + samples
                else:
                    raise Exception('Unsupported VGM command')

            if self._has_loop and not loop_done and cur_time >= loop_start_time + self._loop_samples:
                loop_done = True
                yield JumpToMarkerEvent(loop_start_time + self._loop_samples, 0)

        yield EndEvent(max(cur_time, self.duration))


class RADParser(Parser):
    def __init__(self, input_file):
        super().__init__(input_file)
        import pyrad
        self.event_queue = []
        self.current_time = 0
        self.duration = 0
        self.tune_data = input_file.read()
        self.registers = {}

        def write_cbk(reg, value):
            self._add_event(reg, value)

        self.rad_reader = pyrad.RADParser(self.tune_data, write_cbk)
        self.time_base = self.rad_reader.get_time_base()
        if self.time_base == -1:
            raise Exception('Unsupported RAD file')

    def _add_event(self, reg, value):
        if (not reg in self.registers) or self.registers[reg] != value:
            self.event_queue.append(OPLWriteEvent(
                self.current_time, reg, value))
            self.registers[reg] = value

    def read_events(self):
        while not self.rad_reader.update():
            self.current_time += 1
            for event in self.event_queue:
                yield event
            self.event_queue.clear()
        self.duration = self.current_time
        yield EndEvent(self.duration)


class OPL3MIDIParser(Parser):
    def __init__(self, input_file):
        super().__init__(input_file)
        self._event_queue = []
        self._current_time = 0
        self.duration = 0
        self.time_base = 1000

        def write_cbk(reg, value):
            self._event_queue.append(OPLWriteEvent(
                self._current_time, reg, value))
        import mido
        import notesalad.opl
        self._midi_file = mido.MidiFile(input_file)
        self._midi_impl = notesalad.opl.OPL3MIDI(
            notesalad.opl.OPLCallbackDevice(write_cbk, None))

    def read_events(self):
        yield OPLWriteEvent(0, 0x105, 0x01)
        event_time = 0
        for msg in self._midi_file:
            event_time = event_time + (msg.time * 1000)
            while self._current_time < event_time:
                self._midi_impl.set_time(self._current_time)
                self._midi_impl.update()
                self._current_time = self._current_time + 1
            if msg.is_meta:
                continue
            if self._filter_midi(msg):
                self._midi_impl.send(msg.bin())
            for event in self._event_queue:
                yield event
            self._event_queue.clear()
        self.duration = self._current_time
        yield EndEvent(self.duration)

    def _filter_midi(self, _msg):
        return True


class OPL3RawParser(Parser):
    def __init__(self, input_file):
        super().__init__(input_file)
        self.time_base = 49716
        self.duration = 0

    def read_events(self):
        while True:
            packet = self.input_file.read(12)
            if len(packet) < 12:
                yield EndEvent(self.duration)
                break
            current_time, reg, value = struct.unpack('<qHH', packet)
            self.duration = current_time
            if reg < 0x200:
                yield OPLWriteEvent(current_time, reg, value)
            elif reg == 0x202:
                yield MarkerEvent(current_time, value)


def open_parser(path):
    (_, ext) = os.path.splitext(path)
    ext = ext.lower()
    if ext == '.dro':
        return DROParser(open(path, 'rb'))
    if ext == '.vgm':
        return VGMParser(open(path, 'rb'))
    if ext == '.vgz':
        return VGMParser(gzip.open(path))
    if ext == '.rad':
        return RADParser(open(path, 'rb'))
    if ext == '.mid':
        return OPL3MIDIParser(path)
    if ext == '.opl3raw':
        return OPL3RawParser(open(path, 'rb'))
    return None
