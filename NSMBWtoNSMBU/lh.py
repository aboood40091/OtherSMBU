#!/usr/bin/python
# -*- coding: latin-1 -*-

# Based on:
# https://github.com/Treeki/RandomStuff/blob/master/LHDecompressor.cpp


class LHContext:
    buf1 = bytearray(0x800)
    buf2 = bytearray(0x80)


def GetUncompressedSize(inData):
    outSize = inData[1] | (inData[2] << 8) | (inData[3] << 16)

    if not outSize:
        outSize = inData[4] | (inData[5] << 8) | (inData[6] << 16) | (inData[7] << 24)

    return outSize


def LoadLHPiece(buf, inData, unk):
    r6 = 1 << unk
    r7 = 2
    r9 = 1
    r10 = 0
    r11 = 0
    r12 = r6 - 1
    r30 = r6 << 1

    if unk <= 8:
        r6 = inData[0]
        inOffset = 1
        copiedAmount = 1
    else:
        r6 = inData[0] | (inData[1] << 8)
        inOffset = 2
        copiedAmount = 2

    dataSize = (r6 + 1) << 2
    while copiedAmount < dataSize:
        r6 = unk + 7
        r6 = (r6 - r11) >> 3

        if r11 < unk:
            for i in range(r6):
                r4 = inData[inOffset]
                r10 <<= 8
                r10 |= r4
                copiedAmount += 1
                inOffset += 1
            r11 += (r6 << 3)

        if r9 < r30:
            r0 = r11 - unk
            r9 += 1
            r0 = r10 >> r0
            r0 &= r12
            buf[r7] = r0 >> 8
            buf[r7 + 1] = r0 & 0xFF
            r7 += 2

        r11 -= unk

    return copiedAmount


def IsLHCompressed(inData):
    return inData.startswith(b'@')


def UncompressLH(inData):
    context = LHContext()

    outLength = GetUncompressedSize(inData)
    outData = bytearray(outLength)

    outIndex = 0
    outSize = inData[1] | (inData[2] << 8) | (inData[3] << 16)
    inData = inData[4:]

    if not outSize:
        outSize = inData[0] | (inData[1] << 8) | (inData[2] << 16) | (inData[3] << 24)
        inData = inData[4:]

    inData = inData[LoadLHPiece(context.buf1, inData, 9):]
    inData = inData[LoadLHPiece(context.buf2, inData, 5):]

    # this is a direct conversion of the PPC ASM, pretty much
    r0 = 0x10
    r3 = 0x100
    r4 = 0
    r5 = 0
    r6 = 0

    while outIndex < outSize:
        r12 = 2  # Used as an offset into context.buf1
        r7 = r4  # Used as an offset into inData

        while True:
            if not r6:
                r5 = inData[r7]
                r6 = 8
                r4 += 1
                r7 += 1

            r11 = (context.buf1[r12] << 8) | context.buf1[r12 + 1]
            r8 = r5 >> (r6 - 1)
            r6 -= 1

            r9 = r8 & 1
            r10 = r11 & 0x7F
            r8 = r3 >> r9  # sraw?
            r8 = r11 & r8
            flag = not r8
            r8 = (r10 + 1) << 1
            r9 += r8

            if flag:
                r12 &= ~3
                r8 = r9 << 1
                r12 += r8
                continue
            else:
                r8 = r12 & ~3  # offset into buf1
                r7 = r9 << 1
                r7 = (context.buf1[r8 + r7] << 8) | context.buf1[r8 + r7 + 1]

            break

        if r7 < 0x100:
            outData[outIndex] = r7
            outIndex += 1
            continue

        # block copy?
        r7 &= 0xFF
        r25 = 2  # used as an offset into context.buf2
        r7 += 3
        r7 &= 0xFFFF  # r7 is really an ushort, probably
        r8 = r4  # used as an offset into inData

        while True:
            if not r6:
                r5 = inData[r8]
                r6 = 8
                r4 += 1
                r8 += 1

            r12 = (context.buf2[r25] << 8) | context.buf2[r25 + 1]
            r9 = r5 >> (r6 - 1)
            r6 -= 1
            r10 = r9 & 1
            r11 = r12 & 7
            r9 = r0 >> r10  # sraw
            r9 = r12 & r9
            flag = not r9
            r9 = r11 + 1
            r9 <<= 1
            r10 += r9

            if flag:
                r25 &= ~3
                r9 = r10 << 1
                r25 += r9
                continue
            else:
                r9 = r25 & ~3
                r8 = r10 << 1
                r11 = (context.buf2[r9 + r8] << 8) | context.buf2[r9 + r8 + 1]

            break

        r10 = 0
        if r11:
            r8 = r4  # offset into inData
            r10 = 1

            while True:
                r11 -= 1
                r9 = r11 & 0xFFFF
                if r9:
                    r10 = (r10 << 1) & 0xFFFF
                    if not r6:
                        r5 = inData[r8]
                        r6 = 8
                        r4 += 1
                        r8 += 1

                    r6 -= 1
                    r9 = r5 >> r6
                    r9 &= 1
                    r10 |= r9
                else:
                    break

        if (outIndex + r7) > outSize:
            r7 = outSize - outIndex
            r7 &= 0xFFFF

        r9 = r10 + 1
        r8 = outIndex  # offset into outData
        r10 = r9 & 0xFFFF
        while True:
            r9 = r7 & 0xFFFF
            r7 -= 1
            if r9:
                r9 = outIndex - r10
                outIndex += 1
                outData[r8] = outData[r9]
                r8 += 1
            else:
                break

    return bytes(outData)
