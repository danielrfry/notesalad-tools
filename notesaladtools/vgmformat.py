import struct


class VGMHeader:
    def __init__(self):
        self.ident = b'Vgm '
        self.eof_offset = 0
        self.version = 0x151
        self.sn76489_clock = 0
        self.ym2413_clock = 0
        self.gd3_offset = 0
        self.total_samples = 0
        self.loop_offset = 0
        self.loop_samples = 0
        self.rate = 0
        self.sn_fb = 0
        self.snw = 0
        self.sf = 0
        self.ym2612_clock = 0
        self.ym2151_clock = 0
        self.vgm_data_offset = 0
        self.sega_pcm_clock = 0
        self.spcm_interface = 0
        self.rf5c68_clock = 0
        self.ym2203_clock = 0
        self.ym2608_clock = 0
        self.ym2610_b_clock = 0
        self.ym3812_clock = 0
        self.ym3526_clock = 0
        self.y8950_clock = 0
        self.ymf262_clock = 0
        self.ymf278b_clock = 0
        self.ymf271_clock = 0
        self.ymz280b_clock = 0
        self.rf5c164_clock = 0
        self.pwm_clock = 0
        self.ay8910_clock = 0
        self.ayt = 0
        self.ay_flags = 0
        self.vm = 0
        self.lb = 0
        self.lm = 0
        self.gb_dmg_clock = 0
        self.nes_apu_clock = 0
        self.multipcm_clock = 0
        self.upd7759_clock = 0
        self.okim6258_clock = 0
        self.of = 0
        self.kf = 0
        self.cf = 0
        self.okim6295_clock = 0
        self.k051649_clock = 0
        self.k054539_clock = 0
        self.huc6280_clock = 0
        self.c140_clock = 0
        self.k053260_clock = 0
        self.pokey_clock = 0
        self.qsound_clock = 0
        self.scsp_clock = 0
        self.extra_hdr_ofs = 0
        self.wonderswan_clock = 0
        self.vsu_clock = 0
        self.saa1099_clock = 0
        self.es5503_clock = 0
        self.es5506_clock = 0
        self.es_chns = 0
        self.cd = 0
        self.x1_010_clock = 0
        self.c352_clock = 0
        self.ga20_clock = 0

    def pack(self):
        return struct.pack(
            '<4sIIIIIIIIIHBBIIIIIIIIIIIIIIIIIIIBBBBBxBBIIIIIBBBxIIIIIIIIIIIIIIIHBxIII28x',
            self.ident,
            self.eof_offset,
            self.version,
            self.sn76489_clock,
            self.ym2413_clock,
            self.gd3_offset,
            self.total_samples,
            self.loop_offset,
            self.loop_samples,
            self.rate,
            self.sn_fb,
            self.snw,
            self.sf,
            self.ym2612_clock,
            self.ym2151_clock,
            self.vgm_data_offset,
            self.sega_pcm_clock,
            self.spcm_interface,
            self.rf5c68_clock,
            self.ym2203_clock,
            self.ym2608_clock,
            self.ym2610_b_clock,
            self.ym3812_clock,
            self.ym3526_clock,
            self.y8950_clock,
            self.ymf262_clock,
            self.ymf278b_clock,
            self.ymf271_clock,
            self.ymz280b_clock,
            self.rf5c164_clock,
            self.pwm_clock,
            self.ay8910_clock,
            self.ayt,
            self.ay_flags & 0xff,
            (self.ay_flags >> 8) & 0xff,
            (self.ay_flags >> 16) & 0xff,
            self.vm,
            self.lb,
            self.lm,
            self.gb_dmg_clock,
            self.nes_apu_clock,
            self.multipcm_clock,
            self.upd7759_clock,
            self.okim6258_clock,
            self.of,
            self.kf,
            self.cf,
            self.okim6295_clock,
            self.k051649_clock,
            self.k054539_clock,
            self.huc6280_clock,
            self.c140_clock,
            self.k053260_clock,
            self.pokey_clock,
            self.qsound_clock,
            self.scsp_clock,
            self.extra_hdr_ofs,
            self.wonderswan_clock,
            self.vsu_clock,
            self.saa1099_clock,
            self.es5503_clock,
            self.es5506_clock,
            self.es_chns,
            self.cd,
            self.x1_010_clock,
            self.c352_clock,
            self.ga20_clock
        )


class GD3Tag:
    def __init__(self):
        self.track_name_en = ''
        self.track_name_jp = ''
        self.game_name_en = ''
        self.game_name_jp = ''
        self.system_name_en = ''
        self.system_name_jp = ''
        self.track_author_en = ''
        self.track_author_jp = ''
        self.release_date = ''
        self.vgm_author = ''
        self.notes = ''

    def get_fields(self):
        return (
            self.track_name_en,
            self.track_name_jp,
            self.game_name_en,
            self.game_name_jp,
            self.system_name_en,
            self.system_name_jp,
            self.track_author_en,
            self.track_author_jp,
            self.release_date,
            self.vgm_author,
            self.notes
        )

    def pack(self):
        gd3 = b''.join([field.encode('utf-16_le') +
                       b'\x00\x00' for field in self.get_fields()])
        gd3 = b'Gd3 \x00\x01\x00\x00' + struct.pack('<I', len(gd3)) + gd3
        return gd3

    def is_empty(self):
        for field in self.get_fields():
            if field != '':
                return False
            return True
