print("NSMBWtoNSMBU by AboodXD")
print("(C) 2018")

file = input("\nEnter path to the NSMBW level: ")

import NSMBW
import NSMBU

nsmbw = NSMBW.Game()
nsmbw.LoadLevel(file)
nsmbu = NSMBU.Game()

pa0Obj = {
    0: 0, 1: 1, 2: 2, 3: 3, 4: 156, 5: 157, 6: 158, 7: 159, 8: 160, 9: 161,
    10: 162, 11: 163, 12: 164, 13: 165, 14: 166, 15: 167, 16: 4,
    17: 5, 18: 6, 19: 7, 20: 8, 21: 9,
    22: 10, 23: 11, 24: 12, 25: 13, 26: 15, 27: 16, 28: 17, 29: 18,
    30: 19, 31: 20, 32: 21, 33: 22, 34: 23, 35: 24, 36: 25, 37: 26,
    38: 28, 39: 29, 40: 30, 41: 31, 42: 32, 43: 33, 44: 34, 45: 35,
    46: 36, 47: 37, 48: 38, 49: 40, 50: 41, 51: 42, 52: 43, 53: 44,
    55: 45, 56: 46, 58: 47, 59: 49, 60: 50, 63: 51, 64: 52, 65: 56,
    66: 57, 67: 58, 68: 59, 69: 60, 70: 61, 71: 61, 72: 60, 73: 62,
    74: 63, 75: 64, 76: 65, 77: 66, 78: 67, 79: 68, 80: 69, 81: 70,
    82: 71, 83: 72, 84: 73, 85: 74, 86: 75, 87: 76, 88: 77, 89: 78,
    90: 79, 91: 80, 92: 80, 93: 79, 94: 81, 96: 82, 97: 54, 98: 83,
}

for nsmbwArea in nsmbw.level.areas:
    nsmbu.level.areas.append(nsmbu.level.Area())
    nsmbuArea = nsmbu.level.areas[-1]
    nsmbuArea.areanum = nsmbwArea.areanum
    nsmbuArea.tileset0 = nsmbwArea.tileset0
    nsmbuArea.tileset1 = nsmbwArea.tileset1
    nsmbuArea.tileset2 = nsmbwArea.tileset2
    nsmbuArea.tileset3 = nsmbwArea.tileset3
    nsmbuArea.startEntrance = nsmbwArea.startEntrance
    nsmbuArea.wrapedges = 1 if nsmbwArea.wrapFlag else 0
    nsmbuArea.timelimit = nsmbwArea.timeLimit + 100
    nsmbuArea.Metadata = nsmbwArea.Metadata

    nsmbuArea.zones = nsmbwArea.zones.copy()
    for zone in nsmbuArea.zones:
        zone.background = nsmbuArea.bgs[0]
        if nsmbwArea.creditsFlag or nsmbwArea.ambushFlag or (nsmbwArea.toadHouseType and nsmbwArea.toadHouseType != 2):
            zone.type = 1

        elif nsmbwArea.toadHouseType == 2:
            zone.type = 160

        else:
            zone.type = 0

    nsmbuArea.layers = nsmbwArea.layers.copy()
    for layer in nsmbuArea.layers:
        for obj in layer:
            if obj.tileset == 0:
                if obj.type in pa0Obj:
                    obj.type = pa0Obj[obj.type]

                else:
                    obj.type = 0

            if obj.tileset == 3 and nsmbuArea.tileset3 in ["Pa3_rail", "Pa3_rail_white"] and obj.type < 29:
                obj.type += 84
                obj.tileset = 0

            obj.data = 0

    nsmbuArea.locations = nsmbwArea.locations.copy()
    nsmbuArea.entrances = nsmbwArea.entrances.copy()
    for entrance in nsmbuArea.entrances:
        entrance.unk05 = entrance.unk0C = entrance.unk0F = entrance.unk12 = entrance.camera = entrance.pathID = entrance.pathnodeindex = entrance.unk16 = 0

    print('-' * 80)
    print(nsmbwArea.tileset0)
    print(nsmbwArea.tileset1)
    print(nsmbwArea.tileset2)
    print(nsmbwArea.tileset3)

with open("level.sarc", "wb") as out:
    out.write(nsmbu.level.save())
