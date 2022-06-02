import argparse
import time
from .parser import open_parser
from .devices import get_device


def main():
    parser = argparse.ArgumentParser(
        prog='nsplay', description='Play back .DRO, .VGM and .VGZ files.')
    parser.add_argument('--device', '-d', metavar='DEVICE', default=('oplem',),
                        type=str, nargs=1, help='set the device to use', dest='device')
    parser.add_argument('file', metavar='FILE', nargs=1,
                        help='the file to play')

    args = parser.parse_args()

    with open_parser(args.file[0]) as vgmparser, get_device(args.device[0]) as chip:
        try:
            chip.reset()

            last_event_time = 0
            for event in vgmparser.read_events():
                chip.wait((event.time - last_event_time) / vgmparser.time_base)
                chip.write_event(event)
                last_event_time = event.time

            chip.wait((vgmparser.duration - last_event_time) /
                      vgmparser.time_base)

            chip.all_notes_off()
        except KeyboardInterrupt:
            # Reset chip
            chip.reset()
            print()
