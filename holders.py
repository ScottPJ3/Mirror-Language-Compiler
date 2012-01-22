from compiler import var
from utility import RaiseSyntaxError
var.Types={}


class Scope():
	def __init__(self,parent):
		self.dict={}
		self.parent=parent
	def referenceExistsInScopeTree(self,item):
		return item in self.dict or item in self.parent
	def referenceExistsInScope(self,item):
		return item in self.dict
	def getNearestReference(self,item):
		if item in self.dict:
			return self.dict[item]
		else:
			return self.parent[item]
	def reassign(self,item,value):
		#Reassigns value to item. Item must already be in THIS scope or SyntaxError is raised.
		if not self.referenceExistsInScope(item):
			RaiseSyntaxError("Reference %s does not exist in scope." % item)
		else:
			self.dict[item]=value
	def declare(self,item,value):
		#Declares item to be of value in THIS scope. Raises Syntax Error if already in THIS scope.
		if self.referenceExistsInScope(item):
			RaiseSyntaxError("Reference %s already exists in scope." % item)
		else:
			self.dict[item]=value
		
class PartialScope(Scope):
	def __init__(self,parent):
		Scope.__init__(self,parent)
	def reassign(self,item,value):
		#Reassigns value to item in the scope above this scope.
		if not self.referenceExistsInScope(item):
			self.parent.reassign(item,value)
		else:
			self.dict[item]=value
			
			
			
class Type():
	def __init__(self,name,CILType):
		self.name=name
		self.typedict={}
		self.CILType=CILType
		var.Types[name]=self
	def __contains__(self,value):
		return value in self.typedict
	def __getitem__(self,value):
		return self.typedict[value]
	def __setitem__(self,item,value):
		self.typedict[item]=value
		
class Variable():
	def __init__(self,vtype,ILAddress):
		self.type=vtype
		self.typedict=var.Types[self.type]
		self.ILAddress=ILAddress
	def __contains__(self,value):
		return value in self.typedict
	def __getitem__(self,value):
		return self.typedict[value]
		
class Function(Variable):
	def __init__(self,vtype,ILAddress,functionLocation,arguments,optional_arguments):
		Variable.__init__(self,vtype,ILAddress)
		self.functionLocation=functionLocation
		self.arguments=arguments
		self.optional_arguments=optional_arguments
		
class MirrorType(Variable):
	def __init__(self,vtype,ILAddress,CILType,attributes):
		Variable.__init__(self,vtype,ILAddress)
		self.CILType=CILType
		self.attributes=attributes