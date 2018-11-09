
from stream import StreamIn, StreamOut

class Parser:
	ERROR = -1
	
	@classmethod
	def new(cls, *args):
		instance = cls()
		instance.reset(*args)
		return instance

	@classmethod
	def from_stream(cls, stream):
		instance = cls()
		if instance.load(stream) != cls.ERROR:
			return instance
		
	@classmethod
	def from_data(cls, data, endian=">"):
		instance = cls()
		if instance.load_data(data, endian) != cls.ERROR:
			return instance
		
	@classmethod
	def from_file(cls, filename, endian=">"):
		with open(filename, "rb") as f:
			return cls.from_data(f.read(), endian)
			
	def load_data(self, data, endian=">"):
		stream = StreamIn(data, endian=endian)
		return self.load(stream)
			
	def to_data(self, endian=">"):
		stream = StreamOut(endian=endian)
		self.save(stream)
		return stream.data
		
	def to_file(self, filename, endian=">"):
		data = self.to_data()
		with open(filename, "wb") as f:
			f.write(data)
			
	def copy(self): return self.from_data(self.to_data())
		
	def reset(self, *args): raise NotImplementedError
	def load(self, stream): raise NotImplementedError
	def save(self, stream): raise NotImplementedError
	

class Struct(Parser):

	default = {
		"u8": 0,
		"u16": 0,
		"u32": 0,
		"s8": 0,
		"s16": 0,
		"s32": 0,
		"float": .0
	}
	
	def __repr__(self):
		s = "<%s " %self.__class__.__name__
		
		fields = []
		for name, _ in self.fields:
			fields.append("%s=%s" %(name, getattr(self, name)))
		s += " ".join(fields) + ">"
		return s

	def reset(self):
		for name, type in self.fields:
			setattr(self, name, self.get_default(type))
			
	def load(self, stream):
		for name, type in self.fields:
			setattr(self, name, self.get_value(stream, type))
			
	def save(self, stream):
		for name, type in self.fields:
			value = getattr(self, name)
			self.set_value(stream, type, value)
			
	def get_default(self, fmt):
		if type(fmt) != str:
			return fmt.new()

		if "*" in fmt:
			fmt, count = fmt.split("*")
			count = int(count)
			return [self.get_default(fmt) for i in range(count)]
		return self.default[fmt]
			
	def get_value(self, stream, fmt):
		if type(fmt) != str:
			return fmt.from_stream(stream)

		elif "*" in fmt:
			fmt, count = fmt.split("*")
			count = int(count)
			return [self.get_value(stream, fmt) for i in range(count)]

		elif fmt == "u8": value = stream.u8()
		elif fmt == "u16": value = stream.u16()
		elif fmt == "u32": value = stream.u32()
		elif fmt == "s8": value = stream.s8()
		elif fmt == "s16": value = stream.s16()
		elif fmt == "s32": value = stream.s32()
		elif fmt == "float": value = stream.float()
		else: raise RuntimeError("Invalid struct type:", fmt)
		return value
		
	def set_value(self, stream, fmt, value):
		if type(fmt) != str:
			value.save(stream)

		elif "*" in fmt:
			fmt, count = fmt.split("*")
			[self.set_value(stream, fmt, val) for val in value]

		elif fmt == "u8": stream.u8(value)
		elif fmt == "u16": stream.u16(value)
		elif fmt == "u32": stream.u32(value)
		elif fmt == "s8": stream.s8(value)
		elif fmt == "s16": stream.s16(value)
		elif fmt == "s32": stream.s32(value)
		elif fmt == "float": stream.float(value)
		else: raise RuntimeError("Invalid struct type:", fmt)
