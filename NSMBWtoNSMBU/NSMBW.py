import archive
from items import ObjectItem, ZoneItem, LocationItem, EntranceItem
import os
import pickle
import struct

try:
    import pyximport
    pyximport.install()
    import lh_cy as lh

except ImportError:
    import lh


def checkContent(data):
    if not data.startswith(b'U\xAA8-'):
        return False

    required = (b'course\0', b'course1.bin\0', b'\0\0\0\x80')
    for r in required:
        if r not in data:
            return False

    return True


def IsNSMBLevel(filename):
    """
    Does some basic checks to confirm a file is a NSMBW level
    """
    if not os.path.isfile(filename):
        return False

    with open(filename, 'rb') as f:
        data = f.read()

    if lh.IsLHCompressed(bytes(data)):
        try:
            data = lh.UncompressLH(bytearray(data))

        except IndexError:
            return False

    if checkContent(data):
        return True


class Metadata:
    """
    Class for the new level metadata system
    """

    # This new system is much more useful and flexible than the old
    # system, but is incompatible with older versions of Reggie.
    # They will fail to understand the data, and skip it like it
    # doesn't exist. The new system is written with forward-compatibility
    # in mind. Thus, when newer versions of Reggie are created
    # with new metadata values, they will be easily able to add to
    # the existing ones. In addition, the metadata system is lossless,
    # so unrecognized values will be preserved when you open and save.

    # Type values:
    # 0 = binary
    # 1 = string
    # 2+ = undefined as of now - future Reggies can use them
    # Theoretical limit to type values is 4,294,967,296

    def __init__(self, data=None):
        """
        Creates a metadata object with the data given
        """
        self.DataDict = {}
        if data is None: return

        if data[0:4] != b'MD2_':
            # This is old-style metadata - convert it
            try:
                strdata = ''
                for d in data: strdata += chr(d)
                level_info = pickle.loads(strdata)
                for k, v in level_info.iteritems():
                    self.setStrData(k, v)
            except Exception:
                pass
            if ('Website' not in self.DataDict) and ('Webpage' in self.DataDict):
                self.DataDict['Website'] = self.DataDict['Webpage']
            return

        # Iterate through the data
        idx = 4
        while idx < len(data) - 4:

            # Read the next (first) four bytes - the key length
            rawKeyLen = data[idx:idx + 4]
            idx += 4

            keyLen = (rawKeyLen[0] << 24) | (rawKeyLen[1] << 16) | (rawKeyLen[2] << 8) | rawKeyLen[3]

            # Read the next (key length) bytes - the key (as a str)
            rawKey = data[idx:idx + keyLen]
            idx += keyLen

            key = ''
            for b in rawKey: key += chr(b)

            # Read the next four bytes - the number of type entries
            rawTypeEntries = data[idx:idx + 4]
            idx += 4

            typeEntries = (rawTypeEntries[0] << 24) | (rawTypeEntries[1] << 16) | (rawTypeEntries[2] << 8) | \
                          rawTypeEntries[3]

            # Iterate through each type entry
            for entry in range(typeEntries):
                # Read the next four bytes - the type
                rawType = data[idx:idx + 4]
                idx += 4

                type = (rawType[0] << 24) | (rawType[1] << 16) | (rawType[2] << 8) | rawType[3]

                # Read the next four bytes - the data length
                rawDataLen = data[idx:idx + 4]
                idx += 4

                dataLen = (rawDataLen[0] << 24) | (rawDataLen[1] << 16) | (rawDataLen[2] << 8) | rawDataLen[3]

                # Read the next (data length) bytes - the data (as bytes)
                entryData = data[idx:idx + dataLen]
                idx += dataLen

                # Add it to typeData
                self.setOtherData(key, type, entryData)

    def binData(self, key):
        """
        Returns the binary data associated with key
        """
        return self.otherData(key, 0)

    def strData(self, key):
        """
        Returns the string data associated with key
        """
        data = self.otherData(key, 1)
        if data is None: return
        s = ''
        for d in data: s += chr(d)
        return s

    def otherData(self, key, type):
        """
        Returns unknown data, with the given type value, associated with key (as binary data)
        """
        if key not in self.DataDict: return
        if type not in self.DataDict[key]: return
        return self.DataDict[key][type]

    def setBinData(self, key, value):
        """
        Sets binary data, overwriting any existing binary data with that key
        """
        self.setOtherData(key, 0, value)

    def setStrData(self, key, value):
        """
        Sets string data, overwriting any existing string data with that key
        """
        data = []
        for char in value: data.append(ord(char))
        self.setOtherData(key, 1, data)

    def setOtherData(self, key, type, value):
        """
        Sets other (binary) data, overwriting any existing data with that key and type
        """
        if key not in self.DataDict: self.DataDict[key] = {}
        self.DataDict[key][type] = value

    def save(self):
        """
        Returns a bytes object that can later be loaded from
        """

        # Sort self.DataDict
        dataDictSorted = []
        for dataKey in self.DataDict: dataDictSorted.append((dataKey, self.DataDict[dataKey]))
        dataDictSorted.sort(key=lambda entry: entry[0])

        data = []

        # Add 'MD2_'
        data.append(ord('M'))
        data.append(ord('D'))
        data.append(ord('2'))
        data.append(ord('_'))

        # Iterate through self.DataDict
        for dataKey, types in dataDictSorted:

            # Add the key length (4 bytes)
            keyLen = len(dataKey)
            data.append(keyLen >> 24)
            data.append((keyLen >> 16) & 0xFF)
            data.append((keyLen >> 8) & 0xFF)
            data.append(keyLen & 0xFF)

            # Add the key (key length bytes)
            for char in dataKey: data.append(ord(char))

            # Sort the types
            typesSorted = []
            for type in types: typesSorted.append((type, types[type]))
            typesSorted.sort(key=lambda entry: entry[0])

            # Add the number of types (4 bytes)
            typeNum = len(typesSorted)
            data.append(typeNum >> 24)
            data.append((typeNum >> 16) & 0xFF)
            data.append((typeNum >> 8) & 0xFF)
            data.append(typeNum & 0xFF)

            # Iterate through typesSorted
            for type, typeData in typesSorted:

                # Add the type (4 bytes)
                data.append(type >> 24)
                data.append((type >> 16) & 0xFF)
                data.append((type >> 8) & 0xFF)
                data.append(type & 0xFF)

                # Add the data length (4 bytes)
                dataLen = len(typeData)
                data.append(dataLen >> 24)
                data.append((dataLen >> 16) & 0xFF)
                data.append((dataLen >> 8) & 0xFF)
                data.append(dataLen & 0xFF)

                # Add the data (data length bytes)
                for d in typeData: data.append(d)

        return data

class Game:
    class Level:
        """
        Class for a level from New Super Mario Bros. Wii
        """

        def __init__(self):
            """
            Initializes the level with default settings
            """
            self.areas = []

        class Area:
            """
            Class for a parsed NSMBW level area
            """

            def __init__(self):
                """
                Creates a completely new NSMBW area
                """
                # Default area number
                self.areanum = 1

                # Default tileset names for NSMBW
                self.tileset0 = 'Pa0_jyotyu'
                self.tileset1 = ''
                self.tileset2 = ''
                self.tileset3 = ''

                self.blocks = [b''] * 14
                self.blocks[0] = b'Pa0_jyotyu\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                self.blocks[1] = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc8\x00\x00\x00\x00\x00\x00\x00\x00'
                self.blocks[3] = b'\x00\x00\x00\x00\x00\x00\x00\x00'
                self.blocks[7] = b'\xff\xff\xff\xff'

                self.defEvents = 0
                self.timeLimit = 200
                self.creditsFlag = False
                self.startEntrance = 0
                self.ambushFlag = False
                self.toadHouseType = 0
                self.wrapFlag = False
                self.unkFlag1 = False
                self.unkFlag2 = False

                self.unkVal1 = 0
                self.unkVal2 = 0

                self.entrances = []
                self.sprites = []
                self.bounding = []
                self.bgA = []
                self.bgB = []
                self.zones = []
                self.locations = []
                self.pathdata = []
                self.paths = []
                self.comments = []

            def load(self, course, L0, L1, L2):
                """
                Loads an area from the archive files
                """

                # Load in the course file and blocks
                self.LoadBlocks(course)

                # Load stuff from individual blocks
                self.LoadTilesetNames()  # block 1
                self.LoadOptions()  # block 2
                self.LoadEntrances()  # block 7
                self.LoadSprites()  # block 8
                self.LoadZones()  # block 10 (also blocks 3, 5, and 6)
                self.LoadLocations()  # block 11
                self.LoadPaths()  # block 12 and 13

                # Load the editor metadata
                if self.block1pos[0] != 0x70:
                    rddata = course[0x70:self.block1pos[0]]
                    self.LoadReggieInfo(rddata)
                else:
                    self.LoadReggieInfo(None)

                self.layers = [[], [], []]

                if L0 is not None:
                    self.LoadLayer(0, L0)

                if L1 is not None:
                    self.LoadLayer(1, L1)

                if L2 is not None:
                    self.LoadLayer(2, L2)

                return True

            def LoadBlocks(self, course):
                """
                Loads self.blocks from the course file
                """
                self.blocks = [b''] * 14
                getblock = struct.Struct('>II')
                for i in range(14):
                    data = getblock.unpack_from(course, i * 8)
                    if data[1] == 0:
                        self.blocks[i] = b''
                    else:
                        self.blocks[i] = course[data[0]:data[0] + data[1]]

                self.block1pos = getblock.unpack_from(course, 0)

            def LoadTilesetNames(self):
                """
                Loads block 1, the tileset names
                """
                data = struct.unpack_from('32s32s32s32s', self.blocks[0])
                self.tileset0 = data[0].strip(b'\0').decode('utf-8')
                self.tileset1 = data[1].strip(b'\0').decode('utf-8')
                self.tileset2 = data[2].strip(b'\0').decode('utf-8')
                self.tileset3 = data[3].strip(b'\0').decode('utf-8')

            def LoadOptions(self):
                """
                Loads block 2, the general options
                """
                optdata = self.blocks[1]
                optstruct = struct.Struct('>IxxxxHh?BxxB?Bx')
                data = optstruct.unpack(optdata)
                self.defEvents, wrapByte, self.timeLimit, self.creditsFlag, unkVal, self.startEntrance, self.ambushFlag, self.toadHouseType = data
                self.wrapFlag = bool(wrapByte & 1)
                self.unkFlag1 = bool(wrapByte >> 3)
                self.unkFlag2 = bool(unkVal == 100)

                """
                Loads block 4, the unknown maybe-more-general-options block
                """
                optdata2 = self.blocks[3]
                optdata2struct = struct.Struct('>xxHHxx')
                data = optdata2struct.unpack(optdata2)
                self.unkVal1, self.unkVal2 = data

            def LoadEntrances(self):
                """
                Loads block 7, the entrances
                """
                entdata = self.blocks[6]
                entcount = len(entdata) // 20
                entstruct = struct.Struct('>HHxxxxBBBBxBBBHxB')
                offset = 0
                entrances = []
                for i in range(entcount):
                    data = entstruct.unpack_from(entdata, offset)
                    entrances.append(EntranceItem(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9],
                                     data[10]))
                    offset += 20
                self.entrances = entrances

            def LoadSprites(self):
                """
                Loads block 8, the sprites
                """
                spritedata = self.blocks[7]
                sprcount = len(spritedata) // 16
                sprstruct = struct.Struct('>HHH8sxx')
                offset = 0
                sprites = []

                unpack = sprstruct.unpack_from
                append = sprites.append
                for i in range(sprcount):
                    data = unpack(spritedata, offset)
                    append([data[0], data[1], data[2], data[3]])
                    offset += 16
                self.sprites = sprites

            def LoadZones(self):
                """
                Loads block 3, the bounding preferences
                """
                bdngdata = self.blocks[2]
                count = len(bdngdata) // 24
                bdngstruct = struct.Struct('>llllHHxxxx')
                offset = 0
                bounding = []
                for i in range(count):
                    datab = bdngstruct.unpack_from(bdngdata, offset)
                    bounding.append([datab[0], datab[1], datab[2], datab[3], datab[4], datab[5]])
                    offset += 24
                self.bounding = bounding

                """
                Loads block 5, the top level background values
                """
                bgAdata = self.blocks[4]
                bgAcount = len(bgAdata) // 24
                bgAstruct = struct.Struct('>xBhhhhHHHxxxBxxxx')
                offset = 0
                bgA = []
                for i in range(bgAcount):
                    data = bgAstruct.unpack_from(bgAdata, offset)
                    bgA.append([data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8]])
                    offset += 24
                self.bgA = bgA

                """
                Loads block 6, the bottom level background values
                """
                bgBdata = self.blocks[5]
                bgBcount = len(bgBdata) // 24
                bgBstruct = struct.Struct('>xBhhhhHHHxxxBxxxx')
                offset = 0
                bgB = []
                for i in range(bgBcount):
                    datab = bgBstruct.unpack_from(bgBdata, offset)
                    bgB.append([datab[0], datab[1], datab[2], datab[3], datab[4], datab[5], datab[6], datab[7], datab[8]])
                    offset += 24
                self.bgB = bgB

                """
                Loads block 10, the zone data
                """
                zonedata = self.blocks[9]
                zonestruct = struct.Struct('>HHHHHHBBBBxBBBBxBB')
                count = len(zonedata) // 24
                offset = 0
                zones = []
                for i in range(count):
                    dataz = zonestruct.unpack_from(zonedata, offset)

                    # Find the proper bounding
                    boundObj = None
                    id = dataz[7]
                    for checkb in self.bounding:
                        if checkb[4] == id: boundObj = checkb

                    zones.append(
                        ZoneItem(dataz[0], dataz[1], dataz[2], dataz[3], dataz[4], dataz[5], dataz[6], dataz[7], dataz[8],
                                 dataz[9], dataz[10], dataz[11], dataz[12], dataz[13], dataz[14], dataz[15], boundObj, bgA, bgB,
                                 i))
                    offset += 24
                self.zones = zones

            def LoadLocations(self):
                """
                Loads block 11, the locations
                """
                locdata = self.blocks[10]
                locstruct = struct.Struct('>HHHHBxxx')
                count = len(locdata) // 12
                offset = 0
                locations = []
                for i in range(count):
                    data = locstruct.unpack_from(locdata, offset)
                    locations.append(LocationItem(data[0], data[1], data[2], data[3], data[4]))
                    offset += 12
                self.locations = locations

            def LoadLayer(self, idx, layerdata):
                """
                Loads a specific object layer from a string
                """
                objcount = len(layerdata) // 10
                objstruct = struct.Struct('>HHHHH')
                offset = 0
                z = (2 - idx) * 8192

                layer = self.layers[idx]
                append = layer.append
                unpack = objstruct.unpack_from
                for i in range(objcount):
                    data = unpack(layerdata, offset)
                    append(ObjectItem(data[0] >> 12, data[0] & 4095, idx, data[1], data[2], data[3], data[4], z))
                    z += 1
                    offset += 10

            def LoadPaths(self):
                """
                Loads block 12, the paths
                """
                # Path struct: >BxHHH
                pathdata = self.blocks[12]
                pathcount = len(pathdata) // 8
                pathstruct = struct.Struct('>BxHHH')
                offset = 0
                unpack = pathstruct.unpack_from
                pathinfo = []
                paths = []
                for i in range(pathcount):
                    data = unpack(pathdata, offset)
                    nodes = self.LoadPathNodes(data[1], data[2])
                    add2p = {'id': int(data[0]),
                             'nodes': [],
                             'loops': data[3] == 2
                             }
                    for node in nodes:
                        add2p['nodes'].append(node)
                    pathinfo.append(add2p)

                    offset += 8

                for i in range(pathcount):
                    xpi = pathinfo[i]
                    for xpj in xpi['nodes']:
                        paths.append([xpj['x'], xpj['y'], xpi, xpj])

                self.pathdata = pathinfo
                self.paths = paths

            def LoadPathNodes(self, startindex, count):
                """
                Loads block 13, the path nodes
                """
                # PathNode struct: >HHffhxx
                ret = []
                nodedata = self.blocks[13]
                nodestruct = struct.Struct('>HHffhxx')
                offset = startindex * 16
                unpack = nodestruct.unpack_from
                for i in range(count):
                    data = unpack(nodedata, offset)
                    ret.append({'x': int(data[0]),
                                'y': int(data[1]),
                                'speed': float(data[2]),
                                'accel': float(data[3]),
                                'delay': int(data[4])
                                # 'id':i
                                })
                    offset += 16
                return ret

            def LoadReggieInfo(self, data):
                if (data is None) or (len(data) == 0):
                    self.Metadata = Metadata()
                    return

                try:
                    self.Metadata = Metadata(data)

                except Exception:
                    self.Metadata = Metadata()  # fallback

        def load(self, data):
            """
            Loads a NSMBW level from bytes data.
            """
            arc = archive.U8.load(data)

            try:
                arc['course']

            except:
                return False

            # Sort the area data
            areaData = {}
            for name, val in arc.files:
                if val is None:
                    continue

                name = name.replace('\\', '/').split('/')[-1]

                if not name.startswith('course'):
                    continue

                if not name.endswith('.bin'):
                    continue

                if '_bgdatL' in name:
                    # It's a layer file
                    if len(name) != 19:
                        continue

                    try:
                        thisArea = int(name[6])
                        laynum = int(name[14])

                    except ValueError:
                        continue

                    if not (0 < thisArea < 5):
                        continue

                    if thisArea not in areaData:
                        areaData[thisArea] = [None] * 4

                    areaData[thisArea][laynum + 1] = val

                else:
                    # It's the course file
                    if len(name) != 11:
                        continue

                    try:
                        thisArea = int(name[6])

                    except ValueError:
                        continue

                    if not (0 < thisArea < 5):
                        continue

                    if thisArea not in areaData:
                        areaData[thisArea] = [None] * 4

                    areaData[thisArea][0] = val

            # Create area objects
            self.areas = []
            thisArea = 1
            while thisArea in areaData:
                course = areaData[thisArea][0]
                L0 = areaData[thisArea][1]
                L1 = areaData[thisArea][2]
                L2 = areaData[thisArea][3]

                newarea = self.Area()
                newarea.areanum = thisArea
                newarea.load(course, L0, L1, L2)

                self.areas.append(newarea)

                thisArea += 1

            return True

    def LoadLevel(self, name):
        """
        Load a level from any game into the editor
        """
        if not os.path.isfile(name):
            return False

        if not IsNSMBLevel(name):
            return False

         # Open the file
        with open(name, 'rb') as fileobj:
            levelData = fileobj.read()

        # Decompress, if needed
        if lh.IsLHCompressed(bytes(levelData)):
            try:
                levelData = lh.UncompressLH(bytearray(levelData))

            except IndexError:
                return False

        # Load the actual level
        # Create the new level object
        self.level = self.Level()

        # Load it
        if not self.level.load(levelData):
            raise Exception

        # If we got this far, everything worked! Return True.
        return True
