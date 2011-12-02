#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""
This module is released with the LGPL license.
Copyright 2011 Matteo Mattei <matteo.mattei@gmail.com>; Nicola Ponzeveroni <nicola.ponzeveroni@gilbarco.com>

It is intended to be used to access ROMFS filesystem data.
Based on linux/romfs_fs.h
"""
__all__ = ['RomfsNode','Romfs']

def __mkw(h,l): return ((ord(h)&0x00ff)<< 8|(ord(l)&0x00ff))
def __mkl(h,l): return (((h)&0xffff)<<16|((l)&0xffff))
def __mk4(a,b,c,d): return __mkl(__mkw(a,b),__mkw(c,d))

ROMSB_WORD0 = __mk4('-','r','o','m')
ROMSB_WORD1 = __mk4('1','f','s','-')
ROMFH_SIZE = 16
ROMFH_PAD = (ROMFH_SIZE-1)
ROMFH_MASK = (~ROMFH_PAD)

ROMFH_TYPE=7
ROMFH_HRD=0
ROMFH_DIR=1
ROMFH_REG=2
ROMFH_SYM=3
ROMFH_BLK=4
ROMFH_CHR=5
ROMFH_SCK=6
ROMFH_FIF=7
ROMFH_EXEC=8

class _Romfs_base:
	""" ROMFS BASE CLASS """
	def makeInteger(self,buf,start,lenght):
		""" Assemble multibyte integer """
		ret = 0
		for i in range(start,start+lenght):
			ret = ret*256+ord(buf[i])
		return ret

class _Romfs_inode(_Romfs_base):
	""" ROMFS INODE CLASS: contains single inode data. """
	def __init__(self,buf):
		""" _Romfs_inode constructor: accept file content buffer """
		self.next     = self.makeInteger(buf, 0,4)
		self.spec     = self.makeInteger(buf, 4,4)
		self.size     = self.makeInteger(buf, 8,4)
		self.checksum = self.makeInteger(buf,12,4)
		self.name     = buf[16:buf.find('\x00',16)]

	def inode_dump(self,sys_stdout_like_object):
		""" print informations about romfs inode. Only for debug. """
		name = self.name
		sys_stdout_like_object.write("INODE: next=%08d spec=%08d size=%08d checksum=%08d name=%s\n" % (self.next,self.spec,self.size,self.checksum,name))

class Romfs_super_block(_Romfs_base):
	""" ROMFS SUPERBLOCK CLASS: contains the romfs image header data. """
	def __init__(self,buf):
		""" Romfs_super_block constructor: accept file content buffer. """
		self.word0    = self.makeInteger(buf, 0,4)
		self.word1    = self.makeInteger(buf, 4,4)
		self.size     = self.makeInteger(buf, 8,4)
		self.checksum = self.makeInteger(buf,12,4)
		self.name     = buf[16:buf.find('\x00',16)]
		self.start = (ROMFH_SIZE + len(self.name) + 1 + ROMFH_PAD) & ROMFH_MASK
		self.stop  = (self.size)

	def check(self):
		""" Return True if the file is a ROMFS. False otherwise. """
		if self.word0 == ROMSB_WORD0 and self.word1 == ROMSB_WORD1:
			return True
		return False
	
	def end(self):
		""" Return start + size of the whole romfs image. """
		return self.start+self.size

class RomfsNode:
	""" ROMFSNODE CLASS: give access to single inode. """
	def __init__(self):
		""" RomfsNode constructor: no parameters supplied. """
		self.parent = None
		self.name     = ""
		self.start    = 0
		self.length   = 0
		self.next     = 0
		self.children = []
		self.romfs = None
		
	def __body(self):
		""" Return the starting point of the file content. """
		return self.start + (ROMFH_SIZE + len(self.name) + 1 + ROMFH_PAD) & ROMFH_MASK
		
	def dump(self,sys_stdout_like_object,level=0):
		""" Print all files and directories on stdout. Only for debug. """
		for i in range(0,level):
			sys_stdout_like_object.stdout.write("    ")
		sys_stdout_like_object.write(self.name+"\n")
		for c in self.children:
			c.dump(sys_stdout_like_object,level+1)

	def isFolder(self):
		""" Check if the current node is a Folder or not. """
		return ((self.next & ROMFH_TYPE) == ROMFH_DIR)

	def hasAttribute(self,attr):
		""" Check if the inode has the specified attribute flags set.
		Use the ROMFH_* constants. """
		attr = (attr & ROMFH_TYPE)
		return ((self.next & attr) == attr)
		
	def findAll(self,path=""):
		""" Return a list of inode paths contained in the current inode. """
		if not self.name=="":
			path+=("/"+self.name)
		if self.isFolder():
			ret = []
			for c in self.children:
				ret = ret + c.findAll(path)
			return ret
		else:
			return [path]

	def hasChildren(self):
		""" Check if an inode has some children. """
		return len(self.children)!=0

	def getContent(self):
		""" Return a buffer (string) containing the current inode data. """
		self.romfs.romfs.seek(self.__body())
		return self.romfs.romfs.read(self.length)
	
	def select(self,path):
		""" Returns the inodes in the path specified.
		The path must contain the current inode name. """
		levels = path.split("/")
		return self.__selectl(levels, 0)
	
	def __selectl(self,levels,index):
		""" Recursive implementation of select. Internal use. """
		if len(levels)==index+1 and self.name == levels[index]:
			 return self
		for c in self.children:
			if c.name==levels[index+1]:
				return c.__selectl(levels,index+1)
		return None

	def getPath(self):
		""" Returns this inode path. """
		buf = self.name
		p = self.parent
		while p != None :
			if not p.name=="":
				buf = p.name+"/"+buf
			else:
				buf = "/"+buf
			p = p.parent
		return buf

	def dirlist(self,path):
		""" Return the list of the inodes directly contained in the inode identified by path. 
		Return None if the path does not exists. """
		node = self.select(path)
		if node==None :
			return None
		return node.children
		
	def read(self,path):
		""" Return the content of the inodes directly contained in the inode identified by path. 
		Return None if the path does not exists. """
		node = self.select(path)
		if node==None :
			return None
		return node.getContent()
		
	def close(self):
		self.romfs.close()
	
	def getLength(self):
		return self.length
		
	def getName(self):
		return self.name
		
class Romfs:
	""" ROMFS class: give access to the whole Romfs image. """
	def __init__(self,filehandle=None):
		""" Romfs class constructor: open file hanlde (optional). """
		self.romfs = filehandle
		
	def open(self, path):
		""" Open a romfs file: accepts path of the Romfs. """
		if self.romfs==None:
			self.romfs = open(path,"rb")
		
	def close(self):
		""" Close a romfs file: no parameter supply. """
		if self.romfs!=None:
			self.romfs.close()
			self.romfs = None
	
	def getRoot(self):
		""" Returns the root node of ROMfs filesystem 
		that contains recursively all other nodes. 
		Actual file parsing happens during this call. """
		buf = self.romfs.read(1024)
		b = Romfs_super_block(buf)
		if not b.check():
			self.close()
			raise IOError("The file supplied is not a romfs image")
		n = RomfsNode()
		n.romfs = self
		n.name=""
		n.next = ROMFH_DIR
		n.start = 0
		n.length = b.size
		n.children = self.__listnames(b.start,b.end())
		for ch in n.children:
			ch.parent = n
		return n
	
	def __listnames(self,start,stop):
		""" Recursively read all inner inodes. Internal usage. """
		children = []
		while start!=0 and start < stop:
			self.romfs.seek(start)
			buff = self.romfs.read(256)
			if len(buff) < ROMFH_SIZE + ROMFH_PAD:
				return children
			inode = _Romfs_inode(buff)
			#inode.inode_dump()
			r = RomfsNode()
			r.name   = inode.name
			r.length = inode.size
			r.start  = start
			r.next   = inode.next
			r.romfs = self
			header_end = start + ROMFH_SIZE + (len(inode.name) + 1 + ROMFH_PAD) & ROMFH_MASK
			child_end  = inode.next & ROMFH_MASK
			if child_end==0:
				child_end = stop
			if (inode.next & ROMFH_TYPE) == ROMFH_REG:
				# regular file
				pass
			elif (inode.next & ROMFH_TYPE) == ROMFH_DIR:
				# directory
				self.romfs.seek(start)
				r.children = self.__listnames(header_end,child_end)
				for ch in r.children:
					ch.parent = r
			else:
				# unknown
				pass
			if r.name!="." and r.name!="..":
				children.append( r )
			start = r.next & ROMFH_MASK
		return children

if __name__=="__main__":
	import sys
	filename = sys.argv[1]
	r = Romfs()
	r.open(filename)
	n = r.getRoot()
	for i in n.findAll():
		print(i)
	r.close()
