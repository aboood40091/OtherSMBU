import struct


class OPTData(struct.Struct):
    def __init__(self):
        super().__init__('>2x4B10x')

    def loadData(self, data):
        (self.lavaParticlesType,
         self.snowEffectFlag,
         self.sfx,
         self.ghostFogFlag) = self.unpack_from(data, 0)

def read(inb):
    opt = OPTData()
    opt.loadData(inb)

    return (opt.lavaParticlesType,
            opt.snowEffectFlag,
            opt.sfx,
            opt.ghostFogFlag)

def printInfo(opt):
    sfx = {
        0: "None",
        1: "Lava",
        2: "Jungle Birds",
        3: "Thunder",
        4: "Beach Waves",
        5: "Dripping",
        6: "Airship",
        7: "W7 Airship",
    }

    print("Lava particles type: %s" % ("None" if not opt.lavaParticlesType else ("Very Frequent" if opt.lavaParticlesType == 3 else ("Frequent" if opt.lavaParticlesType == 2 else "Sparse"))))
    print("Snow Effect flag: %s" % ("No" if opt.snowEffectFlag != 1 else "Yes"))

    sfx = opt.sfx
    if sfx not in sfx:
        sfx = 0

    print("Sound effect: %s" % sfx[opt.sfx])
    print("Ghost Fog flag: %s" % ("No" if opt.ghostFogFlag != 1 else "Yes"))
    

def save(lavaParticlesType,
         snowEffectFlag,
         sfx,
         ghostFogFlag):

    return OPTData().pack(
        lavaParticlesType,
        snowEffectFlag,
        sfx,
        ghostFogFlag,
    )
