import gzip
import io
import os
import struct
from .events import JumpToMarkerEvent, MarkerEvent, OPLWriteEvent, OPMWriteEvent
from .vgmformat import VGMHeader


class Writer:
    def write_event(self, event):
        raise NotImplementedError()

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class VGMWriter(Writer):
    def __init__(self, output_file):
        super().__init__()
        self.time_base = 44100
        self.output_file = output_file
        self.current_time = 0
        self.ym3812_clock = 0
        self.ymf262_clock = 0
        self.ym2151_clock = 0
        self.duration = 0
        self.events = []
        self.gd3_tag = None

    def write_event(self, event):
        if event.time < self.duration:
            raise ValueError('Event time is in the past')

        self.duration = event.time

        self.events.append(event)
        if isinstance(event, OPLWriteEvent):
            if event.reg & 0x100 and self.ymf262_clock == 0:
                self.ymf262_clock = 14318180
                self.ym3812_clock = 0
            elif self.ym3812_clock == 0 and self.ymf262_clock == 0:
                self.ym3812_clock = 3579545
        elif isinstance(event, OPMWriteEvent):
            if self.ym2151_clock == 0:
                self.ym2151_clock = 3579545

    def close(self):
        markers = {}
        loop_start_marker = None
        loop_end_time = None
        self.output_file.seek(256)
        for event in self.events:
            time = event.time
            self._write_delay(time)

            if isinstance(event, OPLWriteEvent):
                if self.ymf262_clock != 0:
                    if event.reg & 0x100:
                        self.output_file.write(struct.pack(
                            '<BBB', 0x5f, event.reg & 0xff, event.value))
                    else:
                        self.output_file.write(struct.pack(
                            '<BBB', 0x5e, event.reg, event.value))
                elif self.ym3812_clock != 0 and not event.reg & 0x100:
                    self.output_file.write(struct.pack(
                        '<BBB', 0x5a, event.reg, event.value))
            elif isinstance(event, OPMWriteEvent):
                if self.ym2151_clock != 0:
                    self.output_file.write(struct.pack(
                        '<BBB', 0x54, event.reg, event.value))
            elif isinstance(event, MarkerEvent):
                markers[event.index] = {
                    'pos': self.output_file.tell(), 'time': time}
            elif isinstance(event, JumpToMarkerEvent):
                if loop_start_marker is not None:
                    loop_start_marker = markers[event.index]
                    loop_end_time = time

        # End of sound data marker
        self.output_file.write(b'\x66')

        gd3_offset = 0
        if self.gd3_tag is not None:
            gd3_offset = self.output_file.tell() - 0x14
            self.output_file.write(self.gd3_tag.pack())

        header = VGMHeader()
        header.eof_offset = self.output_file.tell() - 4
        header.total_samples = self.duration
        header.ym2151_clock = self.ym2151_clock
        header.vgm_data_offset = 0xcc
        header.ym3812_clock = self.ym3812_clock
        header.ymf262_clock = self.ymf262_clock
        header.gd3_offset = gd3_offset

        if loop_end_time is not None and loop_start_marker is not None:
            header.loop_offset = loop_start_marker['pos'] - 0x1c
            header.loop_samples = loop_end_time - loop_start_marker['time']

        self.output_file.seek(0)
        self.output_file.write(header.pack())
        self.output_file.close()

    def _write_delay(self, wait_until):
        wait_time = wait_until - self.current_time
        while True:
            if wait_time <= 0:
                break
            if wait_time == 735:
                self.output_file.write(b'\x62')
                wait_time -= 735
            elif wait_time == 882:
                self.output_file.write(b'\x63')
                wait_time -= 882
            else:
                wait_cmd_time = min(wait_time, 65535)
                self.output_file.write(struct.pack('<BH', 0x61, wait_cmd_time))
                wait_time -= wait_cmd_time
        self.current_time = wait_until


class BufferedStream(io.RawIOBase):
    def __init__(self, dest_stream):
        super().__init__()
        self.dest_stream = dest_stream
        self.buffer = io.BytesIO()

    def close(self):
        self.dest_stream.write(self.buffer.getvalue())
        self.dest_stream.close()
        self.buffer.close()

    def readable(self):
        return self.buffer.readable()

    def readline(self, *args, **kwargs):
        return self.buffer.readline(*args, **kwargs)

    def readlines(self, *args, **kwargs):
        return self.buffer.readlines(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self.buffer.seek(*args, **kwargs)

    def seekable(self):
        return self.buffer.seekable()

    def tell(self):
        return self.buffer.tell()

    def truncate(self, *args, **kwargs):
        return self.buffer.truncate(*args, **kwargs)

    def writable(self):
        return self.buffer.writable()

    def writelines(self, *args, **kwargs):
        return self.buffer.writelines(*args, **kwargs)

    def read(self, *args, **kwargs):
        return self.buffer.read(*args, **kwargs)

    def readinto(self, *args, **kwargs):
        return self.buffer.readinto(*args, **kwargs)

    def write(self, *args, **kwargs):
        return self.buffer.write(*args, **kwargs)


def open_writer(path):
    (_, ext) = os.path.splitext(path)
    ext = ext.lower()
    if ext == '.vgm':
        return VGMWriter(open(path, 'wb'))
    if ext == '.vgz':
        return VGMWriter(BufferedStream(gzip.open(path, 'wb')))
    return None
