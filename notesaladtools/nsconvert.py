import argparse

from notesaladtools.utils import parse_time
from notesaladtools.vgmformat import GD3Tag
from .parser import open_parser
from .writer import open_writer
from .processor import add_end_pause, add_key_off, convert_event_times, detect_loop, optimise, set_endpoint
from .processor import trim_start_silence, trim_start_to_marker, trim_start_to_time


def main():
    parser = argparse.ArgumentParser(
        prog='nsconvert', description='Convert .DRO and .VGM files to other formats.')
    parser.add_argument('input', metavar='INPUT',
                        nargs=1, help='the input file')
    parser.add_argument('output', metavar='OUTPUT',
                        nargs=1, help='the output file')
    parser.add_argument('--optimise', '-o', action='store_true',
                        help='apply optimisation to reduce file size')
    parser.add_argument('--trim-start-silence',
                        action='store_true', help='trim silence from start')
    parser.add_argument('--trim-start-to-marker', nargs=1, type=int,
                        metavar='INDEX', help='trim start to specified marker')
    parser.add_argument('--start', '-s', nargs=1, type=parse_time, metavar='TIME',
                        help='cut the specified amount of data from the beginning')
    parser.add_argument('--duration', '-d', nargs=1, type=parse_time,
                        metavar='DURATION', help='cut the file to the specified duration')
    parser.add_argument('--pause', '-p', nargs=1, type=parse_time,
                        metavar='PAUSE', help='add a pause of PAUSE seconds at the end')
    parser.add_argument('--key-off', '-k', action='store_true',
                        help='add key off events at end')
    parser.add_argument('--detect-loop', '-l', action='store_true',
                        help='treat duplicate markers as loop')
    parser.add_argument('--end-on-loop', action='store_true',
                        help='cut the file at the loop end point without looping')
    parser.add_argument('--title', nargs=1, type=str,
                        metavar='TITLE', help='set track title in metadata')
    parser.add_argument('--game', nargs=1, type=str,
                        metavar='GAME', help='set game name in metadata')
    parser.add_argument('--system', nargs=1, type=str,
                        metavar='SYSTEM', help='set system name in metadata')
    parser.add_argument('--artist', nargs=1, type=str,
                        metavar='ARTIST', help='set track artist in metadata')
    parser.add_argument('--release-date', nargs=1, type=str,
                        metavar='DATE', help='set release date in metadata')
    parser.add_argument('--vgm-author', nargs=1, type=str,
                        metavar='AUTHOR', help='set VGM file author in metadata')
    parser.add_argument('--notes', nargs=1, type=str,
                        metavar='NOTES', help='set notes in metadata')

    args = parser.parse_args()

    gd3_tag = GD3Tag()
    if args.title is not None:
        gd3_tag.track_name_en = args.title[0]
    if args.game is not None:
        gd3_tag.game_name_en = args.game[0]
    if args.system is not None:
        gd3_tag.system_name_en = args.system[0]
    if args.artist is not None:
        gd3_tag.track_author_en = args.artist[0]
    if args.release_date is not None:
        gd3_tag.release_date = args.release_date[0]
    if args.vgm_author is not None:
        gd3_tag.vgm_author = args.vgm_author[0]
    if args.notes is not None:
        gd3_tag.notes = args.notes[0]

    with open_parser(args.input[0]) as vgmparser:
        with open_writer(args.output[0]) as vgmwriter:
            if not gd3_tag.is_empty():
                vgmwriter.gd3_tag = gd3_tag

            events = vgmparser.read_events()

            # Set up filters
            if args.trim_start_to_marker:
                events = trim_start_to_marker(
                    events, args.trim_start_to_marker[0])
            if args.start is not None:
                start_time = int(args.start[0] * vgmparser.time_base)
                events = trim_start_to_time(events, start_time)            
            if args.trim_start_silence:
                events = trim_start_silence(events)
            if args.duration is not None:
                duration = int(args.duration[0] * vgmparser.time_base)
                events = set_endpoint(events, duration)
            if args.optimise:
                events = optimise(events)
            if args.key_off:
                events = add_key_off(events)
            if args.pause is not None:
                pause_length = int(args.pause[0] * vgmparser.time_base)
                events = add_end_pause(events, pause_length)
            if args.end_on_loop:
                events = detect_loop(events, True)
            elif args.detect_loop:
                events = detect_loop(events)

            events = convert_event_times(
                events, vgmparser.time_base, vgmwriter.time_base)

            for event in events:
                vgmwriter.write_event(event)
