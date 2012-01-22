#This Python script is designed for IronPython 2.7.1.
# It requires the GEngine.dll which is the .NET GoldParser 5.0 made by Devin Cook, available at goldparser.org
VERSION=1.0
#-------------------------------------------------------------------------------
#Imports
import sys
import os
import clr

clr.AddReferenceToFileAndPath(os.path.join(sys.path[0],"GEngine.dll"))
import GOLD
import System
Emit=System.Reflection.Emit

import library
import reduction_handlers
from utility import RaiseSyntaxError,FormatError,ProgramEnd



#-------------------------------------------------------------------------------
#Global variable holder class
class varc(): pass
var=varc()

	
#-------------------------------------------------------------------------------
def Compile(target):
	
	#Gets script directory
	base=sys.path[0]
	#Changes working directory to base, so that file outputs there.
	os.chdir(base)
	print("Mirror Compiler")
	print("Version %s" % VERSION)
	print('----------')
	print("Compiling %s with options %s" % (target,var.opts))
	var.mirParser=GOLD.Parser()
	#Load the Mirror.egt grammar tables
	var.mirParser.LoadTables(os.path.join(base,"Mirror.egt"))
	print("Reading source file...")
	var.mirParser.Open(open(target,"r").read()+"\n")
	print("Parsing source file...")
	ACCEPTED=False
	#Below basically just checks that the grammar reduces properly to one CompilationUnit.
	while True:
		a=var.mirParser.Parse()
		if a==GOLD.ParseMessage.TokenRead: pass
		elif a==GOLD.ParseMessage.Reduction: pass
		elif a==GOLD.ParseMessage.Accept:
			print("Program accepted!")
			root=var.mirParser.CurrentReduction
			ACCEPTED=True
			break
		elif a==GOLD.ParseMessage.LexicalError:
			print("LEXICAL ERROR- Unrecognized token.\n" + FormatError(var.mirParser))
			break
		elif a==GOLD.ParseMessage.SyntaxError:
			print("SYNTAX ERROR.\n" + FormatError(var.mirParser,expecting=True))
			break
		elif a==GOLD.ParseMessage.GroupError:
			print("SYNTAX ERROR- Unexpected end of file.")
			break
		elif a==GOLD.ParseMessage.InternalError:
			print("An internal parsing error has occurred.")
			break
		elif a==GOLD.ParseMessage.NotLoadedError:
			print("Parsing error: Tables not loaded.")
			break
	if ACCEPTED:
		print("Parsing successful. Compiling.")
		#Creates the "emit" subname under var global variables, to store emit things in.
		var.emit=varc()
		#Our target output file's name without the directory and extension
		targetOutput=os.path.splitext(os.path.split(target)[1])[0]
		#Generate ourselves an assembly name!
		var.emit.name= System.Reflection.AssemblyName(targetOutput)
		#Define ourselves a dynamic assembly, which lets us stick code into it
		var.emit.asmb= System.AppDomain.CurrentDomain.DefineDynamicAssembly(var.emit.name,Emit.AssemblyBuilderAccess.Save)
		var.emit.modb= var.emit.asmb.DefineDynamicModule(targetOutput)
		var.emit.typeBuilder= var.emit.modb.DefineType("$Root")
		#We define our static main function under name, which calls all the statements in the file.
		var.emit.methb=var.emit.typeBuilder.DefineMethod("Main",System.Reflection.MethodAttributes.Static,System.Void,System.Type.EmptyTypes)
		#Our method's IL generator!
		var.emit.il=var.emit.methb.GetILGenerator()
		library.setupMirScope()
		var.TypeStack=[]
		#Compiles all statements
		reduction_handlers.CompileTree(root,var.MIRSCOPE)
		#Save
		var.emit.il.Emit(Emit.OpCodes.Ret)
		var.emit.typeBuilder.CreateType()
		var.emit.modb.CreateGlobalFunctions()
		var.emit.asmb.SetEntryPoint(var.emit.methb)
		var.emit.asmb.Save(targetOutput+".exe")
	else:
		print("Parsing FAILED.")
	ProgramEnd()
	
	
	
#Execute compilation
#TODO: Implement compile from command line options		
if __name__=="__main__":
	try:
		opts=set()
		var.opts=opts
		opts.add("pause")
		Compile(os.path.join(sys.path[0],"test.mir"))
	except:
		import traceback
		traceback.print_exc()
		print("Press enter to continue.")
		raw_input()