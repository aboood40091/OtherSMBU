
import struct

unpack_from = struct.unpack_from


class StreamIn:
	def __init__(self, data, pos=0, endian=">"):
		self.data = data
		self.pos = pos
		self.stack = []
		
		self.set_endian(endian)
		
	def set_endian(self, endian):
		self.endian = endian
		
		#For performance
		self.H = endian + "H"
		self.I = endian + "I"
		self.Q = endian + "Q"
		self.h = endian + "h"
		self.i = endian + "i"
		self.q = endian + "q"
		
	def eof(self): return self.pos >= len(self.data)
		
	def substream(self, size):
		return StreamIn(self.read(size), endian=self.endian)
	
	def push(self): self.stack.append(self.pos)
	def pop(self): self.pos = self.stack.pop()
	
	def tell(self): return self.pos
	def seek(self, pos): self.pos = pos
	def skip(self, num): self.pos += num
	def align(self, num): self.skip((num - self.pos % num) % num)
		
	def read(self, num):
		data = self.data[self.pos : self.pos + num]
		self.pos += num
		return data
		
	def unpack(self, fmt, size):
		data = unpack_from(self.endian + fmt, self.data, self.pos)
		self.pos += size
		return data
		
	def u8(self):
		val = self.data[self.pos]
		self.pos += 1
		return val
		
	def u16(self):
		val = unpack_from(self.H, self.data, self.pos)[0]
		self.pos += 2
		return val

	def u32(self):
		val = unpack_from(self.I, self.data, self.pos)[0]
		self.pos += 4
		return val

	def u64(self):
		val = unpack_from(self.Q, self.data, self.pos)[0]
		self.pos += 8
		return val
	
	def s8(self):
		val = unpack_from("b", self.data, self.pos)[0]
		self.pos += 1
		return val

	def s16(self):
		val = unpack_from(self.h, self.data, self.pos)[0]
		self.pos += 2
		return val

	def s32(self):
		val = unpack_from(self.i, self.data, self.pos)[0]
		self.pos += 4
		return val
		
	def s64(self):
		val = unpack_from(self.q, self.data, self.pos)[0]
		self.pos += 8
		return val

	def float(self): return struct.unpack(self.endian + "f", self.read(4))[0]
	def double(self): return struct.unpack(self.endian + "d", self.read(8))[0]
	
	def u24(self):
		if self.endian == ">":
			return (self.u16() << 8) | self.u8()
		return self.u8() | (self.u16() << 8)
		
	def bool(self):
		return bool(self.u8())

	def ascii(self, num): return self.read(num).decode("ascii")
	
	def char(self): return chr(self.u8())
	def wchar(self): return chr(self.u16())
	def string(self):
		start = self.pos
		end = self.data.find(b"\0", start)
		self.pos = end + 1
		return self.data[start : end].decode("ascii")
		
	def wstring(self):
		string = ""
		char = self.wchar()
		while char != "\0":
			string += char
			char = self.wchar()
		return string
		
	def string_at(self, pos):
		return self.data[pos : self.data.find(b"\0", pos)].decode("ascii")
		
	def list(self, func, count):
		return [func() for i in range(count)]
		
		
class StreamOut:
	def __init__(self, endian=">"):
		self.data = bytearray()
		self.pos = 0
		self.stack = []
		
		self.set_endian(endian)
		
	def set_endian(self, endian):
		self.endian = endian
		
	def new(self): return StreamOut(self.endian)
		
	def push(self): self.stack.append(self.pos)
	def pop(self): self.pos = self.stack.pop()
	
	def tell(self): return self.pos
	def seek(self, pos): self.pos = pos
	def skip(self, num): self.pos += num
	
	def write(self, data):
		length = len(data)
		self.data[self.pos : self.pos + length] = data
		self.pos += length
		
	def pad(self, num, char=b"\0"): self.write(char * num)
	def align(self, num, char=b"\0"): self.pad((num - self.pos % num) % num, char)
		
	def u8(self, value): self.write(bytes([value]))
	def u16(self, value): self.write(struct.pack(self.endian + "H", value))
	def u32(self, value): self.write(struct.pack(self.endian + "I", value))
	def u64(self, value): self.write(struct.pack(self.endian + "Q", value))
	
	def s8(self, value): self.write(struct.pack(self.endian + "b", value))
	def s16(self, value): self.write(struct.pack(self.endian + "h", value))
	def s32(self, value): self.write(struct.pack(self.endian + "i", value))
	def s64(self, value): self.write(struct.pack(self.endian + "q", value))
	
	def float(self, value): self.write(struct.pack(self.endian + "f", value))
	def double(self, value): self.write(struct.pack(self.endian + "d", value))
	
	def u24(self, value):
		if self.endian == ">":
			self.u16(value >> 8)
			self.u8(value & 0xFF)
		else:
			self.u8(value & 0xFF)
			self.u16(value >> 8)
			
	bool = u8
	
	def ascii(self, data): self.write(data.encode("ascii"))
	
	def char(self, char): self.u8(ord(char))
	def wchar(self, char): self.u16(ord(char))
	def string(self, s):
		for char in s + "\0":
			self.char(char)
			
	def wstring(self, s):
		for char in s + "\0":
			self.wchar(char)
			
	def list(self, func, data):
		[func(i) for i in data]
