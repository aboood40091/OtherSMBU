# Code provided by Kinnay
from parser_ import Parser, Struct
import binascii
import enum
import sys


class ParamType(enum.IntEnum):
	BOOL = 0
	FLOAT = 1
	INT = 2
	VEC2 = 3
	VEC3 = 4
	VEC4 = 5
	COLOR = 6
	STRING32 = 7
	STRING64 = 8
	TYPE9 = 9
	CURVE = 12


class Color(Struct):
	fields = (
		("r", "float"),
		("g", "float"),
		("b", "float"),
		("a", "float")
	)
		
		
class Vec2(Struct):
	fields = (
		("x", "float"),
		("y", "float")
	)
		
		
class Vec3(Struct):
	fields = (
		("x", "float"),
		("y", "float"),
		("z", "float")
	)
	
	
class Vec4(Struct):
	fields = (
		("x", "float"),
		("y", "float"),
		("z", "float"),
		("w", "float")
	)


class Param(Parser):

	sizes = {
		ParamType.BOOL: 1,
		ParamType.FLOAT: 4,
		ParamType.INT: 4,
		ParamType.VEC2: 8,
		ParamType.VEC3: 12,
		ParamType.VEC4: 16,
		ParamType.COLOR: 16,
		ParamType.STRING32: 32,
		ParamType.STRING64: 64,
		ParamType.TYPE9: 128
	}

	def __repr__(self):
		return repr(self.value)
		
	def reset(self):
		self.type = 0
		self.name_hash = 0
		self.value = None

	def load(self, stream):
		stream.u32() #Size
		self.type = stream.u32()
		self.name_hash = stream.u32()

		if self.type == ParamType.BOOL: self.value = stream.bool()
		elif self.type == ParamType.FLOAT: self.value = stream.float()
		elif self.type == ParamType.INT: self.value = stream.s32()
		elif self.type == ParamType.VEC2: self.value = Vec2.from_stream(stream)
		elif self.type == ParamType.VEC3: self.value = Vec3.from_stream(stream)
		elif self.type == ParamType.VEC4: self.value = Vec4.from_stream(stream)
		elif self.type == ParamType.COLOR: self.value = Color.from_stream(stream)
		elif self.type == ParamType.STRING32:
			data = stream.read(0x20)
			self.value = data[:data.index(b"\0")].decode("ascii")
		elif self.type == ParamType.STRING64:
			data = stream.read(0x40)
			self.value = data[:data.index(b"\0")].decode("ascii")
		elif self.type == ParamType.TYPE9:
			self.value = stream.read(0x80)
		else:
			raise ValueError("Param type %i" %self.type)
			
	def save(self, stream):
		stream.u32(self.sizes[self.type])
		stream.u32(self.type)
		stream.u32(self.name_hash)
		
		if self.type == ParamType.BOOL: stream.bool(self.value)
		elif self.type == ParamType.FLOAT: stream.float(self.value)
		elif self.type == ParamType.INT: stream.s32(self.value)
		elif self.type in [ParamType.VEC2, ParamType.VEC3, ParamType.VEC4, ParamType.COLOR]:
			self.value.save(stream)
		elif self.type == ParamType.STRING32:
			data = self.value.encode("ascii") + b"\0"
			data += b"\xCD" * (31 - len(data))
			if len(data) == 31:
				data += b"\0"
			stream.write(data)
		elif self.type == ParamType.STRING64:
			data = self.value.encode("ascii") + b"\0"
			data += b"\xCD" * (63 - len(data))
			if len(data) == 63:
				data += b"\0"
			stream.write(data)
		elif self.type == ParamType.TYPE9:
			stream.write(self.value)


class ParamObj(Parser):
	def __repr__(self):
		return "{" + ", ".join([repr(param) for param in self.params]) + "}"
		
	def reset(self):
		self.name_hash = 0
		self.group_hash = 0
		self.params = []

	def load(self, stream):
		stream.u32() #Size
		num_params = stream.u32()
		self.name_hash = stream.u32()
		self.group_hash = stream.u32()
		
		self.params = []
		for i in range(num_params):
			self.params.append(Param.from_stream(stream))
			
	def save(self, stream):
		substream = stream.new()
		substream.u32(len(self.params))
		substream.u32(self.name_hash)
		substream.u32(self.group_hash)
		for param in self.params:
			param.save(substream)
		
		stream.u32(len(substream.data) + 4)
		stream.write(substream.data)


class ParamList(Parser):
	def __repr__(self):
		return "[" + ", ".join([repr(x) for x in self.lists + self.objs]) + "]"
		
	def reset(self):
		self.name_hash = 0
		self.lists = []
		self.objs = []

	def load(self, stream):
		stream.u32() #Size
		self.name_hash = stream.u32()
		num_lists = stream.u32()
		num_objs = stream.u32()
		
		self.lists = []
		self.objs = []
		for i in range(num_lists):
			self.lists.append(ParamList.from_stream(stream))
		for i in range(num_objs):
			self.objs.append(ParamObj.from_stream(stream))
			
	def save(self, stream):
		substream = stream.new()
		substream.u32(self.name_hash)
		substream.u32(len(self.lists))
		substream.u32(len(self.objs))
		for list in self.lists:
			list.save(substream)
		for obj in self.objs:
			obj.save(substream)
			
		stream.u32(len(substream.data) + 4)
		stream.write(substream.data)


class AAMPFile(Parser):
	def __repr__(self):
		return "<%s %s>" %(self.type, self.param_root)
		
	def reset(self):
		self.type = "aglenv"
		self.version = 0
		self.param_root = ParamList.new()
		self.param_root.name_hash = binascii.crc32(b"param_root")

	def load(self, stream):
		stream.set_endian("<")

		if stream.ascii(4) != "AAMP": return self.ERROR
		if stream.u32() != 1: return self.ERROR
		if stream.u32() != 1: return self.ERROR
		stream.u32() #Filesize
		self.version = stream.s32()
		stream.u32() #Type length
		self.type = stream.string()
		
		self.param_root = ParamList.from_stream(stream)
		
	def save(self, stream):
		stream.set_endian("<")
	
		data_stream = stream.new()
		self.param_root.save(data_stream)
		
		stream.ascii("AAMP")
		stream.u32(1)
		stream.u32(1)
		stream.u32(0x18 + len(self.type) + 1 + len(data_stream.data))
		stream.u32(self.version)
		stream.u32(len(self.type))
		stream.string(self.type)
		stream.write(data_stream.data)

def main():
        if (sys.argv) != 2:
                print("Inavlid arguments")
                sys.exit(1)

        aamp = AAMPFile.from_file(sys.argv[1])
        print(aamp)
