import struct


def read(inb):
    fields = {}
    pos = 0

    while pos < len(inb):
        strSize = struct.unpack('<I', inb[pos:pos + 4])[0]
        pos += 4

        if not strSize:
            break

        string = struct.unpack('<%ds' % strSize, inb[pos:pos + strSize])[0]
        pos += strSize

        valueOff = struct.unpack('<I', inb[pos:pos + 4])[0]
        pos += valueOff

        fields[string] = (valueOff, struct.unpack('f', inb[pos:pos + 4])[0])
        pos += 4

    return fields

def save(fields):
    outBuffer = bytearray()

    for field in fields:
        outBuffer += struct.pack('<I', len(field))
        outBuffer += struct.pack('<%ds' % len(field), field)
        outBuffer += struct.pack('<I', fields[field][0])
        outBuffer += b'\0' * (fields[field][0] - 4)
        outBuffer += struct.pack('f', fields[field][1])

    return bytes(outBuffer)
