import struct
import time
import re


duration_re = re.compile(r'^\s*(?:(\d+):)?(?:(\d+):)?(\d+(?:\.\d+)?)\s*$')


def read_struct(f, fmt, *keys):
    data = struct.unpack(fmt, f.read(struct.calcsize(fmt)))
    if len(keys) == 0:
        return data
    return dict(zip(keys, data))


def usleep(micros):
    time.sleep(micros / 1000000)


def parse_time(time_str):
    match = duration_re.match(time_str)
    if match is None:
        raise ValueError()

    hours = 0
    mins = 0
    secs = float(match.group(3))
    if match.group(1) is not None:
        if match.group(2) is None:
            mins = int(match.group(1))
        else:
            mins = int(match.group(2))
            hours = int(match.group(1))

    return secs + (mins * 60) + (hours * 3600)


def convert_time_base(src_time, src_time_base, dest_time_base):
    seconds = src_time // src_time_base
    fraction = (src_time % src_time_base) / src_time_base
    return round((seconds * dest_time_base) + (fraction * dest_time_base))


def retrowave_7bit_encode(data: bytes, flag: bool) -> bytes:
    output = bytearray()

    if len(data) < 1:
        return output

    flag_bit = 0x01 if flag else 0x00

    bit_offset = 0
    for input_byte in data:
        if bit_offset == 0:
            output.append(input_byte | flag_bit)
            output.append(((input_byte << 7) & 0xff) | flag_bit)
            bit_offset = 2
        else:
            output[-1] |= (input_byte >> (bit_offset - 1)) & 0x7f
            output.append(((input_byte << (8 - bit_offset)) & 0xff) | flag_bit)
            bit_offset = (bit_offset + 1) % 8

    return output
