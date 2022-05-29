class VGMEvent:
    def __init__(self, time):
        self.time = time


class OPLWriteEvent(VGMEvent):
    def __init__(self, time, reg, value):
        super().__init__(time)
        self.reg = reg & 0x1ff
        self.value = value


class OPMWriteEvent(VGMEvent):
    def __init__(self, time, reg, value):
        super().__init__(time)
        self.reg = reg & 0xff
        self.value = value


class MarkerEvent(VGMEvent):
    def __init__(self, time, index):
        super().__init__(time)
        self.index = index


class JumpToMarkerEvent(VGMEvent):
    def __init__(self, time, index):
        super().__init__(time)
        self.index = index


class EndEvent(VGMEvent):
    def __init__(self, time):
        super().__init__(time)
