from compiler import var
import System
import holders
Emit=System.Reflection.Emit

def setupMirScope():
	#Creates the base scope of any Mirror program
	var.MIRSCOPE=holders.Scope({})
	typeString=holders.Type("str",System.String)
	typeReal=holders.Type("real",System.Double)
	typeInt=holders.Type("int",System.Int32)
	typeBoolean=holders.Type("bool",System.Boolean)
	typeFunction=holders.Type("function",System.IntPtr)
	typeType=holders.Type("type",System.Type)
	#Declare inbuilt functions
	vtype="function"
	var.MIRSCOPE["print"]=holders.Function("function",var.emit.il.DeclareLocal(var.Types[vtype].CILType),System.Type.GetMethod(System.Console,"WriteLine",System.Array[System.Type]([System.String])),["str"],[])
	