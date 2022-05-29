from copy import copy

from notesaladtools.utils import convert_time_base
from .events import EndEvent, JumpToMarkerEvent, MarkerEvent, OPLWriteEvent, OPMWriteEvent


class RegBuffer:
    def __init__(self):
        self.opl_registers = {}
        self.opm_registers = {}

    def update(self, event):
        if isinstance(event, OPLWriteEvent):
            self.opl_registers[event.reg] = event.value
        elif isinstance(event, OPMWriteEvent):
            self.opm_registers[event.reg] = event.value

    def set_opl_registers(self, time):
        if 0x105 in self.opl_registers:
            yield OPLWriteEvent(time, 0x105, self.opl_registers[0x105])

        for reg, value in self.opl_registers.items():
            if reg != 0x105:
                yield OPLWriteEvent(time, reg, value)

    def set_opm_registers(self, time):
        for reg, value in self.opm_registers.items():
            yield OPMWriteEvent(time, reg, value)

    def set_all_registers(self, time):
        yield from self.set_opl_registers(time)
        yield from self.set_opm_registers(time)

    def clear(self):
        self.opl_registers = {}
        self.opm_registers = {}


def is_opl_key_on(event):
    if not isinstance(event, OPLWriteEvent):
        return False
    if (event.reg & 0xff) >= 0xb0 and (event.reg & 0xff) <= 0xb8:
        return (event.value & 0x20) != 0
    return False


def is_opm_key_on(event):
    if not isinstance(event, OPMWriteEvent):
        return False
    return event.reg == 0x108


def is_key_on(event):
    return is_opl_key_on(event) or is_opm_key_on(event)


def set_key_off(event):
    if is_opl_key_on(event):
        return OPLWriteEvent(event.time, event.reg, event.value & ~0x20)
    if is_opm_key_on(event):
        return OPMWriteEvent(event.time, event.reg, event.value & 0x07)
    return event


def optimise(events):
    reg_buffer = RegBuffer()

    for event in events:
        if isinstance(event, OPLWriteEvent):
            if reg_buffer.opl_registers.get(event.reg, None) != event.value:
                yield event
        elif isinstance(event, OPMWriteEvent):
            if reg_buffer.opm_registers.get(event.reg, None) != event.value:
                yield event
        else:
            yield event
        reg_buffer.update(event)

        if isinstance(event, MarkerEvent):
            reg_buffer.clear()


def trim_start(events, condition):
    reg_buffer = RegBuffer()
    found_start = False
    time_offset = 0
    for event in events:
        if not found_start:
            cond_result = condition(event)
            if cond_result is None:
                reg_buffer.update(set_key_off(event))
                continue
            time_offset = cond_result
            found_start = True
            yield from reg_buffer.set_all_registers(0)
        new_event = copy(event)
        new_event.time = event.time - time_offset
        yield new_event

    if not found_start:
        yield EndEvent(0)


def trim_start_silence(events):
    yield from trim_start(events, lambda event: event.time if is_key_on(event) else None)


def trim_start_to_marker(events, marker_index):
    yield from trim_start(events, lambda event: event.time if isinstance(event, MarkerEvent)
                          and event.index == marker_index else None)


def trim_start_to_time(events, time):
    yield from trim_start(events, lambda event: time if event.time >= time else None)


def set_endpoint(events, time):
    for event in events:
        if isinstance(event, EndEvent):
            continue
        if event.time >= time:
            break
        yield event
    yield EndEvent(time)


def add_key_off(events):
    reg_buffer = RegBuffer()
    end_time = 0
    uses_opl = False
    uses_opm = False

    for event in events:
        reg_buffer.update(event)
        end_time = event.time
        if isinstance(event, OPLWriteEvent):
            uses_opl = True
        if isinstance(event, OPMWriteEvent):
            uses_opm = True
        if not isinstance(event, EndEvent):
            yield event

    # OPL
    if uses_opl:
        for reg_base in range(0xb0, 0xb9):
            for reg in (reg_base, 0x100 | reg_base):
                if reg in reg_buffer.opl_registers:
                    value = reg_buffer.opl_registers[reg] & 0x1f
                    yield OPLWriteEvent(end_time, reg, value)

    # OPM
    if uses_opm:
        for ch in range(0, 8):
            yield OPMWriteEvent(end_time, 0x108, ch)

    yield EndEvent(end_time)


def add_end_pause(events, pause_length):
    end_time = 0
    for event in events:
        end_time = event.time
        if not isinstance(event, EndEvent):
            yield event

    yield EndEvent(end_time + pause_length)


def detect_loop(events, end_on_loop=False):
    markers = {}
    for event in events:
        if isinstance(event, MarkerEvent):
            if event.index in markers:
                if not end_on_loop:
                    yield JumpToMarkerEvent(event.time, event.index)
                yield EndEvent(event.time)
                break
            markers[event.index] = True
            yield event
        else:
            yield event


def convert_event_times(events, src_time_base, dest_time_base):
    for event in events:
        new_event = copy(event)
        new_event.time = convert_time_base(
            event.time, src_time_base, dest_time_base)
        yield new_event
