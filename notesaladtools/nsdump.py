import argparse
from . import opl
from .events import EndEvent, JumpToMarkerEvent, MarkerEvent, OPLWriteEvent, OPMWriteEvent
from .parser import open_parser


def format_reg_opl(reg, val):
    reg = reg & 0x1ff
    reg8 = reg & 0xff
    if reg == 0x08:
        notesel = (val >> 6) & 1
        return f'NOTE SEL: {notesel:b}'
    if 0x20 <= reg8 <= 0x35:
        slot = opl.get_slot(reg - 0x20) + 1
        am = (val >> 7) & 1
        vib = (val >> 6) & 1
        egt = (val >> 5) & 1
        ksr = (val >> 4) & 1
        mult = val & 0x0f
        return f'Slot: {slot:2d} AM: {am:b} VIB: {vib:b} EGT: {egt:b} KSR: {ksr:b} MULT: {mult:x}'
    if 0x40 <= reg8 <= 0x55:
        slot = opl.get_slot(reg - 0x40) + 1
        ksl = (val >> 6) & 0x03
        tl = val & 0x3f
        return f'Slot: {slot:2d} KSL: {ksl:x} TL: {tl:x}'
    if 0x60 <= reg8 <= 0x75:
        slot = opl.get_slot(reg - 0x60) + 1
        ar = (val >> 4) & 0x0f
        dr = val & 0x0f
        return f'Slot: {slot:2d} AR: {ar:x} DR: {dr:x}'
    if 0x80 <= reg8 <= 0x95:
        slot = opl.get_slot(reg - 0x80) + 1
        sl = (val >> 4) & 0x0f
        rr = val & 0x0f
        return f'Slot: {slot:2d} SL: {sl:x} RR: {rr:x}'
    if 0xa0 <= reg8 <= 0xa8:
        channel = opl.get_channel(reg - 0xa0) + 1
        return f'Channel: {channel:2d} F number (L): {val:x}'
    if 0xb0 <= reg8 <= 0xb8:
        channel = opl.get_channel(reg - 0xb0) + 1
        kon = (val >> 5) & 0x01
        block = (val >> 2) & 0x07
        fnum = val & 0x03
        kon_str = 'ON, ' if kon == 1 else 'OFF,'
        return f'KEY {kon_str} Channel: {channel:2d} BLOCK: {block:x} F number (H): {fnum:x}'
    if reg == 0xbd:
        dam = (val >> 7) & 1
        dvb = (val >> 6) & 1
        ryt = (val >> 5) & 1
        bd = (val >> 4) & 1
        sd = (val >> 3) & 1
        tom = (val >> 2) & 1
        tc = (val >> 1) & 1
        hh = val & 1
        return f'DAM: {dam:b} DVB: {dvb:b} RYT: {ryt:b} BD: {bd:b} SD: {sd:b} TOM: {tom:b} TC: {tc:b} HH: {hh:b}'
    if 0xc0 <= reg8 <= 0xc8:
        channel = opl.get_channel(reg - 0xc0) + 1
        chd = (val >> 7) & 1
        chc = (val >> 6) & 1
        chb = (val >> 5) & 1
        cha = (val >> 4) & 1
        fb = (val >> 1) & 0x07
        cnt = val & 1
        return f'Channel: {channel:2d} CHD: {chd:b} CHC: {chc:b} CHB: {chb:b} CHA: {cha:b} FB: {fb:x} CNT: {cnt:b}'
    if 0xe0 <= reg8 <= 0xf5:
        slot = opl.get_slot(reg - 0xe0) + 1
        ws = val & 0x07
        return f'Slot: {slot:2d} WS: {ws:x}'
    if reg == 0x104:
        conn = val & 0x3f
        return f'CONNECTION SEL: {conn:06b}'
    if reg == 0x105:
        new = val & 1
        return f'NEW: {new:b}'
    else:
        return ''


def format_reg_opm(reg, val):
    reg = reg & 0xff
    val = val & 0xff
    if reg == 0x08:
        sn = (val & 0x78) >> 3
        ch = (val & 0x07)
        return f'Channel: {ch:d} Slot: {sn:04b}'
    if reg == 0x0f:
        ne = (val & 0x80) >> 7
        nfrq = (val & 0x1f)
        return f'Noise Enable: {ne:b} Frequency: {nfrq:2x}'
    if reg == 0x10:
        return f'CLKA1: {val:02x}'
    if reg == 0x11:
        clka2 = val & 0x3
        return f'CLKA2: {clka2:x}'
    if reg == 0x12:
        return f'CLKB: {val:02x}'
    if reg == 0x14:
        csm = (val & 0x80) >> 7
        rst_a = (val & 0x10) >> 4
        rst_b = (val & 0x20) >> 5
        irq_a = (val & 0x04) >> 2
        irq_b = (val & 0x08) >> 3
        load_a = (val & 0x01)
        load_b = (val & 0x02) >> 1
        return f'CSM: {csm:b} RSTA: {rst_a:b} RSTB: {rst_b:b} IRQA: {irq_a:b} IRQB: {irq_b:b} LOADA: {load_a:b} ' \
            + f'LOADB: {load_b:b}'
    if reg == 0x18:
        return f'Low Frequency: {val:2x}'
    if reg == 0x19:
        return f'PMD/AMD: {val:2x}'
    if reg == 0x1b:
        ct1 = (val & 0x40) >> 6
        ct2 = (val & 0x80) >> 7
        w = (val & 0x03)
        return f'CT1: {ct1:b} CT2: {ct2:b} Waveform: {w:x}'
    if 0x20 <= reg <= 0x27:
        ch = reg - 0x20
        r = (val & 0x80) >> 7
        l = (val & 0x40) >> 6
        fb = (val & 0x38) >> 3
        conect = (val & 0x07)
        return f'Channel: {ch:d} Left: {l:b} Right: {r:b} Feedback: {fb:x} Connection: {conect:x}'
    if 0x28 <= reg <= 0x2f:
        ch = reg - 0x28
        octave = (val & 0x70) >> 4
        note = (val & 0x0f)
        return f'Channel: {ch:d} Octave: {octave:x} Note: {note:x}'
    if 0x30 <= reg <= 0x37:
        ch = reg - 0x30
        kf = (val & 0xfc) >> 2
        return f'Channel: {ch:d} Key Fraction: {kf:2x}'
    if 0x38 <= reg <= 0x3f:
        ch = reg - 0x38
        pms = (val & 0x70) >> 4
        ams = (val & 0x03)
        return f'Channel: {ch:d} PMS: {pms:x} AMS: {ams:x}'
    if 0x40 <= reg <= 0x5f:
        slot = reg - 0x40
        dt1 = (val & 0x70) >> 4
        mul = (val & 0x0f)
        return f'Slot: {slot:d} Detune 1: {dt1:x} Mult: {mul:x}'
    if 0x60 <= reg <= 0x7f:
        slot = reg - 0x60
        tl = (val & 0x7f)
        return f'Slot: {slot:d} Level: {tl:2x}'
    if 0x80 <= reg <= 0x9f:
        slot = reg - 0x80
        ks = (val & 0xc0) >> 6
        ar = (val & 0x1f)
        return f'Slot: {slot:d} Key Scaling: {ks:x} Attack: {ar:2x}'
    if 0xa0 <= reg <= 0xbf:
        slot = reg - 0xa0
        amsen = (val & 0x80) >> 7
        d1r = (val & 0x1f)
        return f'Slot: {slot:d} AM Enabled: {amsen:b} Decay 1: {d1r:2x}'
    if 0xc0 <= reg <= 0xdf:
        slot = reg - 0xc0
        dt2 = (val & 0xc0) >> 6
        d2r = (val & 0x1f)
        return f'Slot: {slot:d} Detune 2: {dt2:x} Decay 2: {d2r:2x}'
    if 0xe0 <= reg <= 0xff:
        slot = reg - 0xe0
        d1l = (val & 0xf0) >> 4
        rr = (val & 0x0f)
        return f'Slot: {slot:d} Decay 1 Level: {d1l:x} Release: {rr:x}'
    return ''


def format_event(event):
    event_type = type(event)
    if event_type == OPLWriteEvent:
        reg = event.reg
        port = (reg & 0x100) >> 8
        reg8 = reg & 0xff
        value = event.value
        details = format_reg_opl(reg, value)
        desc = f'{port:d} {reg8:02x} {value:02x} | {details}'
    elif event_type == OPMWriteEvent:
        reg = event.reg
        value = event.value
        details = format_reg_opm(reg, value)
        desc = f'{reg:02x} {value:02x} | {details}'
    elif event_type == MarkerEvent:
        desc = f'Marker: {event.index}'
    elif event_type == JumpToMarkerEvent:
        desc = f'Jump to marker: {event.index}'
    elif event_type == EndEvent:
        desc = 'End'
    else:
        desc = '(unknown event)'
    return f'{event.time:08d}: {desc}'


def print_events(input_parser):
    for event in input_parser.read_events():
        print(format_event(event))


def summarize(input_parser):
    chips_used = {}
    for event in input_parser.read_events():
        event_type = type(event)
        if event_type == OPLWriteEvent:
            chips_used['OPL2'] = True
            reg_lsb = event.reg & 0xff
            if 0xb0 <= reg_lsb <= 0xb8 and (event.value & 0x20) != 0:
                # Key on
                if event.reg & 0x100 != 0:
                    chips_used['OPL3'] = True
        elif event_type == OPMWriteEvent:
            chips_used['OPM'] = True
    print('Chips used: ' + ', '.join(chips_used))


def main():
    parser = argparse.ArgumentParser(
        prog='nsdump', description='List or summarize register writes in VGM files.')
    parser.add_argument('--summarize', '-s', help='display a summary of the file instead of listing all writes',
                        action='store_true', default=False)
    parser.add_argument('file', metavar='FILE', nargs=1,
                        help='the input VGM file')
    args = parser.parse_args()
    with open_parser(args.file[0]) as input_parser:
        if args.summarize:
            summarize(input_parser)
        else:
            print_events(input_parser)
