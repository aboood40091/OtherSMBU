import SarcLib
import struct


class Game:
    class Level:
        """
        Class for a level from New Super Mario Bros. U
        """

        def __init__(self):
            """
            Initializes the level with default settings
            """
            self.areas = []

        class Area:
            """
            Class for a parsed NSMBU level area
            """

            def __init__(self):
                """
                Creates a completely new NSMBW area
                """
                # Default area number
                self.areanum = 1

                # Default tileset names for NSMBU
                self.tileset0 = 'Pa0_jyotyu'
                self.tileset1 = ''
                self.tileset2 = ''
                self.tileset3 = ''

                self.blocks = [b''] * 15
                self.blocks[4] = b'\x00\x00\x00\x00\x00\x00\x00\x00Black\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

                # Settings
                self.startEntrance = 0
                self.unk1 = 0
                self.unk2 = 0
                self.wrapedges = 0
                self.timelimit = 400
                self.unk3 = 100
                self.unk4 = 100
                self.unk5 = 100
                self.unk6 = 0
                self.timelimit2 = 300
                self.timelimit3 = 0

                # Lists of things
                self.entrances = []
                self.sprites = []
                self.bounding = []
                self.bgs = []
                self.zones = []
                self.locations = []
                self.pathdata = []
                self.nPathdata = []
                self.paths = []
                self.nPaths = []
                self.comments = []
                self.layers = [[], [], []]

                # BG data
                self.bgCount = 1
                self.bgs = {}
                self.bgblockid = []
                bg = struct.unpack('>HxBxxxx16sHxx', self.blocks[4])
                self.bgblockid.append(bg[0])
                self.bgs[bg[0]] = bg

            @staticmethod
            def MapPositionToZoneID(zones, x, y, useid=False):
                """
                Returns the zone ID containing or nearest the specified position
                """
                id = 0
                minimumdist = -1
                rval = -1

                for zone in zones:
                    r = zone.ZoneRect
                    if r.contains(x, y) and useid:
                        return zone.id
                    elif r.contains(x, y) and not useid:
                        return id

                    xdist = 0
                    ydist = 0
                    if x <= r.left(): xdist = r.left() - x
                    if x >= r.right(): xdist = x - r.right()
                    if y <= r.top(): ydist = r.top() - y
                    if y >= r.bottom(): ydist = y - r.bottom()

                    dist = (xdist ** 2 + ydist ** 2) ** 0.5
                    if dist < minimumdist or minimumdist == -1:
                        minimumdist = dist
                        rval = zone.id

                    id += 1

                return rval

            def save(self):
                """
                Save the area back to a file
                """
                # Prepare this first because otherwise the game refuses to load some sprites
                self.SortSpritesByZone()

                # We don't parse blocks 4, 6, 12, 13
                # Save the other blocks
                self.SaveTilesetNames()  # block 1
                self.SaveOptions()  # block 2
                self.SaveEntrances()  # block 7
                self.SaveSprites()  # block 8
                self.SaveLoadedSprites()  # block 9
                self.SaveZones()  # blocks 10, 3, and 5
                self.SaveLocations()  # block 11
                self.SavePaths()  # blocks 14 and 15

                # Save the metadata
                rdata = bytearray(self.Metadata.save())
                if len(rdata) % 4 != 0:
                    for i in range(4 - (len(rdata) % 4)):
                        rdata.append(0)
                rdata = bytes(rdata)

                # Save the main course file
                # We'll be passing over the blocks array two times.
                # Using bytearray here because it offers mutable bytes
                # and works directly with struct.pack_into(), so it's a
                # win-win situation
                FileLength = (15 * 8) + len(rdata)
                for block in self.blocks:
                    FileLength += len(block)

                course = bytearray()
                for i in range(FileLength): course.append(0)
                saveblock = struct.Struct('>II')

                HeaderOffset = 0
                FileOffset = (15 * 8) + len(rdata)
                struct.pack_into('{0}s'.format(len(rdata)), course, 0x78, rdata)
                for block in self.blocks:
                    blocksize = len(block)
                    saveblock.pack_into(course, HeaderOffset, FileOffset, blocksize)
                    if blocksize > 0:
                        course[FileOffset:FileOffset + blocksize] = block
                    HeaderOffset += 8
                    FileOffset += blocksize

                # Return stuff
                return (
                    bytes(course),
                    self.SaveLayer(0),
                    self.SaveLayer(1),
                    self.SaveLayer(2),
                )

            def SortSpritesByZone(self):
                """
                Sorts the sprite list by zone ID so it will work in-game
                """

                split = {}
                zones = []

                f_MapPositionToZoneID = self.MapPositionToZoneID
                zonelist = self.zones

                for sprite in self.sprites:
                    zone = f_MapPositionToZoneID(zonelist, sprite.objx, sprite.objy)
                    sprite.zoneID = zone
                    if not zone in split:
                        split[zone] = []
                        zones.append(zone)
                    split[zone].append(sprite)

                newlist = []
                zones.sort()
                for z in zones:
                    newlist += split[z]

                self.sprites = newlist 

            def SaveTilesetNames(self):
                """
                Saves the tileset names back to block 1
                """
                self.blocks[0] = ''.join(
                    [self.tileset0.ljust(32, '\0'), self.tileset1.ljust(32, '\0'), self.tileset2.ljust(32, '\0'),
                     self.tileset3.ljust(32, '\0')]).encode('utf-8')

            def SaveOptions(self):
                """
                Saves block 2, the general options
                """
                optstruct = struct.Struct('>xxBBxxxxxBHxBBBBxxBHH')
                buffer = bytearray(0x18)
                optstruct.pack_into(buffer, 0, self.unk1, self.unk2, self.wrapedges, self.timelimit, self.unk3, self.unk4,
                                    self.unk5, self.startEntrance, self.unk6, self.timelimit2, self.timelimit3)
                self.blocks[1] = bytes(buffer)

            def SaveLayer(self, idx):
                """
                Saves an object layer to a bytes object
                """
                layer = self.layers[idx]
                if not layer: return None

                offset = 0
                objstruct = struct.Struct('>HhhHHB')
                buffer = bytearray((len(layer) * 16) + 2)
                f_int = int
                for obj in layer:
                    objstruct.pack_into(buffer,
                                        offset,
                                        f_int((obj.tileset << 12) | obj.type),
                                        f_int(obj.objx),
                                        f_int(obj.objy),
                                        f_int(obj.width),
                                        f_int(obj.height),
                                        f_int(obj.data))
                    offset += 16
                buffer[offset] = 0xFF
                buffer[offset + 1] = 0xFF
                return bytes(buffer)

            def SaveEntrances(self):
                """
                Saves the entrances back to block 7
                """
                offset = 0
                entstruct = struct.Struct('>HHxBxxBBBBBBxBxBBBBBBx')
                buffer = bytearray(len(self.entrances) * 24)
                zonelist = self.zones
                for entrance in self.entrances:
                    zoneID = self.MapPositionToZoneID(zonelist, entrance.objx, entrance.objy)
                    entstruct.pack_into(buffer, offset, int(entrance.objx), int(entrance.objy), int(entrance.unk05),
                                        int(entrance.entid), int(entrance.destarea), int(entrance.destentrance),
                                        int(entrance.enttype), int(entrance.unk0C), zoneID, int(entrance.unk0F),
                                        int(entrance.entsettings), int(entrance.unk12), int(entrance.camera),
                                        int(entrance.pathID), int(entrance.pathnodeindex), int(entrance.unk16))
                    offset += 24
                self.blocks[6] = bytes(buffer)

            def SavePaths(self):
                """
                Saves the paths back to block 14 and 15
                """
                pathstruct = struct.Struct('>BbHHxBxxxx')
                nodecount = 0
                for path in self.pathdata:
                    nodecount += len(path['nodes'])
                if self.nPathdata:
                    nodecount += len(self.nPathdata['nodes'])
                nodebuffer = bytearray(nodecount * 20)
                nodeoffset = 0
                nodeindex = 0
                offset = 0
                pathcount = len(self.pathdata)
                if self.nPathdata:
                    pathcount += 1
                buffer = bytearray(pathcount * 12)

                nPathSaved = False

                for path in self.pathdata:
                    if len(path['nodes']) < 1: continue

                    if path['id'] > 90 and not nPathSaved and self.nPathdata:
                        self.WriteNabbitPathNodes(nodebuffer, nodeoffset, self.nPathdata['nodes'])

                        pathstruct.pack_into(buffer, offset, 90, 0, int(nodeindex), int(len(self.nPathdata['nodes'])), 0)
                        offset += 12
                        nodeoffset += len(self.nPathdata['nodes']) * 20
                        nodeindex += len(self.nPathdata['nodes'])

                        nPathSaved = True

                    self.WritePathNodes(nodebuffer, nodeoffset, path['nodes'])

                    pathstruct.pack_into(buffer, offset, int(path['id']), 0, int(nodeindex), int(len(path['nodes'])),
                                         2 if path['loops'] else 0)
                    offset += 12
                    nodeoffset += len(path['nodes']) * 20
                    nodeindex += len(path['nodes'])

                if not nPathSaved and self.nPathdata:
                    self.WriteNabbitPathNodes(nodebuffer, nodeoffset, self.nPathdata['nodes'])

                    pathstruct.pack_into(buffer, offset, 90, 0, int(nodeindex), int(len(self.nPathdata['nodes'])), 0)
                    offset += 12
                    nodeoffset += len(self.nPathdata['nodes']) * 20
                    nodeindex += len(self.nPathdata['nodes'])

                self.blocks[13] = bytes(buffer)
                self.blocks[14] = bytes(nodebuffer)

            def WritePathNodes(self, buffer, offst, nodes):
                """
                Writes the path node data to the block 15 bytearray
                """
                offset = int(offst)

                nodestruct = struct.Struct('>HHffhHBBBx')
                for node in nodes:
                    nodestruct.pack_into(buffer, offset, int(node['x']), int(node['y']), float(node['speed']),
                                         float(node['accel']), int(node['delay']), 0, 0, 0, 0)
                    offset += 20

            def WriteNabbitPathNodes(self, buffer, offst, nodes):
                """
                Writes the Nabbit path node data to the block 15 bytearray
                """
                offset = int(offst)

                nodestruct = struct.Struct('>HHffhHBBBx')
                for node in nodes:
                    nodestruct.pack_into(buffer, offset, int(node['x']), int(node['y']), 0.0,
                                         0.0, int(node['action']), 0, 0, 0, 0)
                    offset += 20

            def SaveSprites(self):
                """
                Saves the sprites back to block 8
                """
                offset = 0
                sprstruct = struct.Struct('>HHH10sBB3sxxx')
                buffer = bytearray((len(self.sprites) * 24) + 4)
                f_int = int
                for sprite in self.sprites:
                    try:
                        sprstruct.pack_into(buffer, offset, f_int(sprite.type), f_int(sprite.objx), f_int(sprite.objy),
                                            sprite.spritedata[:10],
                                            self.MapPositionToZoneID(self.zones, sprite.objx, sprite.objy, True), 0,
                                            sprite.spritedata[10:] + b'\0')
                    except struct.error:
                        # Hopefully this will solve the mysterious bug, and will
                        # soon no longer be necessary.
                        raise ValueError('SaveSprites struct.error. Current sprite data dump:\n' + \
                                         str(offset) + '\n' + \
                                         str(sprite.type) + '\n' + \
                                         str(sprite.objx) + '\n' + \
                                         str(sprite.objy) + '\n' + \
                                         str(sprite.spritedata[:6]) + '\n' + \
                                         str(sprite.zoneID) + '\n' + \
                                         str(bytes([sprite.spritedata[7], ])) + '\n',
                                         )
                    offset += 24
                buffer[offset] = 0xFF
                buffer[offset + 1] = 0xFF
                buffer[offset + 2] = 0xFF
                buffer[offset + 3] = 0xFF
                self.blocks[7] = bytes(buffer)

            def SaveLoadedSprites(self):
                """
                Saves the list of loaded sprites back to block 9
                """
                ls = []
                for sprite in self.sprites:
                    if sprite.type not in ls: ls.append(sprite.type)
                ls.sort()

                offset = 0
                sprstruct = struct.Struct('>Hxx')
                buffer = bytearray(len(ls) * 4)
                for s in ls:
                    sprstruct.pack_into(buffer, offset, int(s))
                    offset += 4
                self.blocks[8] = bytes(buffer)

            def SaveZones(self):
                """
                Saves blocks 10, 3, and 5; the zone data, boundings, and background data respectively
                """
                bdngstruct = struct.Struct('>llllHHxxxxxxxx')
                bgStruct = struct.Struct('>HxBxxxx16sHxx')
                zonestruct = struct.Struct('>HHHHxBxBBBBBxBBxBxBBxBxx')
                offset = 0
                i = 0
                zcount = len(self.zones)
                buffer2 = bytearray(28 * zcount)
                buffer4 = bytearray(28 * zcount)
                buffer9 = bytearray(28 * zcount)
                for z in self.zones:
                    bdngstruct.pack_into(buffer2, offset, z.yupperbound, z.ylowerbound, z.yupperbound2, z.ylowerbound2, i,
                                         z.unknownbnf)
                    bgStruct.pack_into(buffer4, offset, z.id, z.background[1], z.background[2], z.background[3])
                    zonestruct.pack_into(buffer9, offset,
                                         z.objx, z.objy, z.width, z.height,
                                         0, 0, z.id, i,
                                         z.cammode, z.camzoom, z.visibility, z.id,
                                         z.camtrack, z.music, z.sfxmod, z.type)
                    offset += 28
                    i += 1

                self.blocks[2] = bytes(buffer2)
                self.blocks[4] = bytes(buffer4)
                self.blocks[9] = bytes(buffer9)

            def SaveLocations(self):
                """
                Saves block 11, the location data
                """
                locstruct = struct.Struct('>HHHHBxxx')
                offset = 0
                zcount = len(self.locations)
                buffer = bytearray(12 * zcount)

                for z in self.locations:
                    locstruct.pack_into(buffer, offset, int(z.objx), int(z.objy), int(z.width), int(z.height), int(z.id))
                    offset += 12

                self.blocks[10] = bytes(buffer)

        def save(self):
            """
            Save the level back to a file
            """

            # Make a new archive
            newArchive = SarcLib.SARC_Archive()

            # Create a folder within the archive
            courseFolder = SarcLib.Folder('course')
            newArchive.addFolder(courseFolder)

            # Go through the areas, save them and add them back to the archive
            for areanum, area in enumerate(self.areas):
                course, L0, L1, L2 = area.save()

                if course is not None:
                    courseFolder.addFile(SarcLib.File('course%d.bin' % (areanum + 1), course))
                if L0 is not None:
                    courseFolder.addFile(SarcLib.File('course%d_bgdatL0.bin' % (areanum + 1), L0))
                if L1 is not None:
                    courseFolder.addFile(SarcLib.File('course%d_bgdatL1.bin' % (areanum + 1), L1))
                if L2 is not None:
                    courseFolder.addFile(SarcLib.File('course%d_bgdatL2.bin' % (areanum + 1), L2))

            outerArchive = SarcLib.SARC_Archive()
            outerArchive.addFile(SarcLib.File('level', newArchive.save()[0]))
            outerArchive.addFile(SarcLib.File('levelname', b'level'))

            return outerArchive.save()[0]

    def __init__(self):
        self.level = self.Level()
