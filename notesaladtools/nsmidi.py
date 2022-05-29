import argparse
from math import floor
import sys
import time

import mido
from .midi import OPL2EmulatorOutput, OPL3EmulatorOutput, OPMEmulatorOutput, StdOutOutput, VGMMIDIOutput


def list_devices():
    print('Input devices:')
    for dev in mido.get_input_names():
        print('  mido:' + dev)
    print('  file:<path>')
    print('Output devices:')
    for dev in mido.get_output_names():
        print('  mido:' + dev)
    print('  opl2em')
    print('  opl3em')
    print('  opmem')
    print('  stdout')


def get_device_events(dev):
    with dev:
        while True:
            yield dev.poll()


def get_file_events(file):
    with file:
        msg_time = time.perf_counter()
        for msg in file:
            if msg.is_meta:
                continue
            msg_time = msg_time + msg.time
            while time.perf_counter() < msg_time:
                yield None
            yield msg


def open_midi_input(dev_name):
    print('Opening input device: ' + dev_name)
    if dev_name.startswith('mido:'):
        return get_device_events(mido.open_input(dev_name[5:]))
    if dev_name.startswith('file:'):
        return get_file_events(mido.MidiFile(dev_name[5:]))
    return None


def open_midi_output(dev_name):
    print('Opening output device: ' + dev_name)
    if dev_name.startswith('mido:'):
        return mido.open_output(dev_name[5:])
    if dev_name == 'opl2em':
        return OPL2EmulatorOutput()
    if dev_name == 'opl3em':
        return OPL3EmulatorOutput()
    if dev_name == 'opmem':
        return OPMEmulatorOutput()
    if dev_name == 'stdout':
        return StdOutOutput()
    return None


def main():
    parser = argparse.ArgumentParser(
        prog='nsmidi', description='Route MIDI events to a real or emulated device.')
    parser.add_argument('--list-devs', '-l', help='list input or output devices',
                        action='store_true', default=False)
    parser.add_argument('--input-device', '-i', metavar='DEVICE',
                        nargs=1, help='select input device')
    parser.add_argument('--output-device', '-o',
                        metavar='DEVICE', nargs=1, help='select output device')
    parser.add_argument('--disable-channel', '-d', metavar='CHANNEL', nargs=1, action='append', type=int,
                        help='do not output events on the specified channel')
    parser.add_argument('--solo-channel', '-s', metavar='CHANNEL', nargs=1,
                        action='append', type=int, help='only play events on the specified channel')
    parser.add_argument('--swap-perc', '-p', action='store_true',
                        default=False, help='swap channels 10 and 16')
    args = parser.parse_args()
    if args.list_devs:
        list_devices()
        return
    if args.input_device is None:
        print('No input device specified')
        sys.exit(1)
    if args.output_device is None:
        print('No output device specified')
        sys.exit(1)

    input_dev = open_midi_input(args.input_device[0])
    if input_dev is None:
        print('Cannot open input device')
        sys.exit(1)
    output_dev = open_midi_output(args.output_device[0])
    if output_dev is None:
        print('Cannot open output device')
        sys.exit(1)
    print('Ready')

    ignore_channels = [c[0] for c in args.disable_channel] if args.disable_channel is not None else [
    ]
    solo_channels = [
        c[0] for c in args.solo_channel] if args.solo_channel is not None else None

    with output_dev:
        output_dev.reset()
        try:
            for msg in input_dev:
                if msg is None:
                    time.sleep(0.001)
                    if isinstance(output_dev, VGMMIDIOutput):
                        cur_time_ms = floor(time.perf_counter() * 1000)
                        output_dev.set_time(cur_time_ms)
                        output_dev.update()
                else:
                    if hasattr(msg, 'channel'):
                        if msg.channel in ignore_channels:
                            continue
                        if solo_channels is not None and not msg.channel in solo_channels:
                            continue
                        if args.swap_perc:
                            if msg.channel == 9:
                                msg = msg.copy(channel=15)
                            elif msg.channel == 15:
                                msg = msg.copy(channel=9)
                    output_dev.send(msg)
        finally:
            output_dev.reset()
