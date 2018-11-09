class QRectF:
    """
    Why would we import PyQt5 just to use a few functions from QRectF?
    Let's make our own custom implementation!
    """
    def __init__(self, *args):
        self.x, self.y, self.w, self.h = args

    def left(self):
        return self.x

    def right(self):
        return self.x + self.w

    def top(self):
        return self.y

    def bottom(self):
        return self.y + self.h

    def contains(self, x, y):
        if x in range(self.x, self.x + self.w) and y in range(self.y, self.y + self.h):
            return True

        return False


class ObjectItem:
    def __init__(self, tileset, type, layer, x, y, width, height, z):
        """
        Creates an object with specific data
        """
        self.tileset = tileset
        self.type = type
        self.original_type = type
        self.objx = x
        self.objy = y
        self.layer = layer
        self.width = width
        self.height = height


class ZoneItem:
    def __init__(self, a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, bounding, bgA, bgB, id=None):
        """
        Creates a zone with specific data
        """
        self.objx = a
        self.objy = b
        self.width = c
        self.height = d
        self.modeldark = e
        self.terraindark = f
        self.id = g
        self.block3id = h
        self.cammode = i
        self.camzoom = j
        self.visibility = k
        self.block5id = l
        self.camtrack = n
        self.music = o
        self.sfxmod = p

        if id is not None:
            self.id = id

        if bounding:
            self.yupperbound = bounding[0]
            self.ylowerbound = bounding[1]
            self.yupperbound2 = bounding[2]
            self.ylowerbound2 = bounding[3]
            self.entryid = bounding[4]
            self.unknownbnf = bounding[5]

        else:
            self.yupperbound = 0
            self.ylowerbound = 0
            self.yupperbound2 = 0
            self.ylowerbound2 = 0
            self.entryid = 0
            self.unknownbnf = 0

        self.ZoneRect = QRectF(self.objx, self.objy, self.width, self.height)


class LocationItem:
    def __init__(self, x, y, width, height, id):
        """
        Creates a location with specific data
        """
        self.objx = x
        self.objy = y
        self.width = width
        self.height = height
        self.id = id


class EntranceItem:
    def __init__(self, x, y, id, destarea, destentrance, type, zone, layer, path, settings, cpd):
        """
        Creates an entrance with specific data
        """
        self.objx = x
        self.objy = y
        self.entid = id
        self.destarea = destarea
        self.destentrance = destentrance
        self.enttype = type
        self.entzone = zone
        self.entsettings = settings
