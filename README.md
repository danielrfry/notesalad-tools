# Note Salad Tools

This is a collection of tools written in Python for converting, manipulating and rendering VGM and MIDI files using [Note Salad](https://github.com/danielrfry/notesalad)'s MIDI implementation. These were originally written for testing and debugging Note Salad; if you just want to play VGM files, better alternatives are available.

## Installing

### Requirements

- [libnotesalad](https://github.com/danielrfry/notesalad)
- Python 3 (I use 3.8.x, other versions may work)

I recommend installing in a [virtualenv](https://pypi.org/project/virtualenv/) to avoid conflicts with other packages.

First, install the Python bindings for Note Salad. In the Note Salad repository:

```
cd python
pip install -e .
```

Next, install the Note Salad Tools package. In the Note Salad Tools repository:

```
pip install -e .
```

For full functionality, install optional packages:

```
# For realtime playback using OPL/OPM emulators:
pip install pyaudio
# For MIDI-related functionality:
pip install mido python-rtmidi
```

## Usage

This section contains a few examples showing some of the available functionality of each tool.

### nsplay

Play VGM, VGZ, DRO and MID files or render to WAV output. (Playback is likely to work smoothly only on macOS for the moment).

Playing files:

```
# Using the OPL emulator:
nsplay --device oplem AB_JULIA.vgm
nsplay --device oplem Marbles.dro
nsplay --device oplem CANYON.MID
# Using the OPM emulator:
nsplay --device opmem "02 Level 1.vgz"
```

Rendering files to WAV:

```
# OPL:
nsplay --device oplwav:AB_JULIA.wav AB_JULIA.vgm
# OPM:
nsplay --device "opmwav:02 Level 1.wav" "02 Level 1.vgz"
```

### nsconvert

Convert DRO, VGM, VGZ and MIDI files to VGM or VGZ.

Converting MIDI files to VGM using **libnotesaladcore**'s MIDI implementation (currently only OPL3 is supported):

```
nsconvert CANYON.MID CANYON_OPL3.vgm
```

Converting DRO to VGZ, extracting 20 seconds from the source beginning at 1 minute, 23 seconds:

```
nsconvert --start 1:23 --duration 20 Marbles.dro Marbles.vgz
```

### nsmidi

Route MIDI events between physical MIDI ports and Note Salad's OPL/OPM MIDI implementation and emulators. Allows playing sounds in realtime using a MIDI controller, for example. (Realtime playback is likely to work smoothly only on macOS for now).

Listing MIDI ports:

```
% nsmidi --list-devs
Input devices:
  mido:IAC Driver Bus 1
  mido:YMF262 Player
  mido:Oxygen 49
  file:<path>
Output devices:
  mido:IAC Driver Bus 1
  mido:YMF262 Player
  mido:Oxygen 49
  opl2em
  opl3em
  opmem
  stdout
```

Routing MIDI events from a MIDI controller to the emulated OPL3:

```
nsmidi --input-device "mido:Oxygen 49" --output-device opl3em
```

Playing a MIDI file via a physical MIDI device:

```
nsmidi --input-device "file:CANYON.MID" --output-device "mido:YMF262 Player"
```

### nsdump

"Disassemble" a VGM, VGZ or DRO file, showing the register writes and the affected FM parameters. (Only OPL and OPM are supported).

```
nsdump "02 Spice Opera.vgz"
```

Sample output:

```
...
00000088: 0 e4 00 | Slot:  5 WS: 0
00000088: 0 44 00 | Slot:  5 KSL: 0 TL: 0
00000088: 0 64 f4 | Slot:  5 AR: f DR: 4
00000088: 0 84 06 | Slot:  5 SL: 0 RR: 6
00000088: 0 24 12 | Slot:  5 AM: 0 VIB: 0 EGT: 0 KSR: 1 MULT: 2
00000088: 0 44 0b | Slot:  5 KSL: 0 TL: b
00000088: 0 a1 57 | Channel:  2 F number (L): 57
00000132: 0 b1 25 | KEY ON,  Channel:  2 BLOCK: 1 F number (H): 1
00000132: 0 c2 00 | Channel:  3 CHD: 0 CHC: 0 CHB: 0 CHA: 0 FB: 0 CNT: 0
00000132: 0 e2 02 | Slot:  3 WS: 2
00000132: 0 42 1f | Slot:  3 KSL: 0 TL: 1f
00000132: 0 62 f8 | Slot:  3 AR: f DR: 8
00000132: 0 82 f5 | Slot:  3 SL: f RR: 5
00000132: 0 22 01 | Slot:  3 AM: 0 VIB: 0 EGT: 0 KSR: 0 MULT: 1
00000132: 0 e5 00 | Slot:  6 WS: 0
00000132: 0 45 80 | Slot:  6 KSL: 2 TL: 0
00000132: 0 65 f2 | Slot:  6 AR: f DR: 2
00000132: 0 85 f3 | Slot:  6 SL: f RR: 3
00000132: 0 25 12 | Slot:  6 AM: 0 VIB: 0 EGT: 0 KSR: 1 MULT: 2
00000132: 0 45 88 | Slot:  6 KSL: 2 TL: 8
00000132: 0 b2 31 | KEY ON,  Channel:  3 BLOCK: 4 F number (H): 1
00000132: 0 c5 0e | Channel:  6 CHD: 0 CHC: 0 CHB: 0 CHA: 0 FB: 7 CNT: 0
...
```
