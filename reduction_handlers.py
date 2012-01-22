import holders
from compiler import var
from utility import RaiseSyntaxError
import GOLD
import System
Emit=System.Reflection.Emit
#-------------------------------------------------------------------------------
#Compiler reduction helpers
#-------------------------------------------------------------------------------
def GetTextFromNameNode(reduction):
	#Returns the full text of a name node
	if reduction.Count()==3: #Name Node contains Identifier and <Name>
		return reduction[0].Data.Parent.Text(False) + GetTextFromNameNode(reduction[2])
	else:
		return reduction[0].Data.Parent.Text(False)
def GenerateArgumentsListFromNode(reduction,lis):
	#Generates a lis of argument expression from the ArgumentList node.
	lis.append(reduction[0].Data)
	if reduction.Count>1:
		GenerateArgumentsListFromNode(reduction[2].Data,lis)
def CheckNameNodeIdentifiers(reduction,scope,ignoreLast=False):
	#Check that the name from a name node, such as Cat.Foot.Nail, exists in the current scope.
	#Returns the variable
	#Get text of Identifier
	p=reduction[0].Data
	q=reduction.Count()
	if not(p in scope) and not(q==1 and ignoreLast==True): RaiseSyntaxError("Could not find identifier %s" % p)
	if q==3:
		#The "scope" of the next identifier in the sequence is that of the previous variable. Check the scope of Foot against Cat, Nail agaisnt Foot, etc. It won't check that Cat has Nail because it's using a Variable object's Type rather than an actual Scope object.
		return CheckNameNodeIdentifiers(reduction[3].Data,scope[p],ignoreLast)
	else:
		return (p,scope)
		

def EvaluateExpression(expression,scope):
	CompileTree(expression,scope) #Checks the expression node's validity and pushes its return type to stack and IL
	
def fixStringLiteral(literal):
	#Deals with escaped characters in string literals.
	new=""
	prev=""
	for c in literal:
		if prev=="\\":
			if c=="n":
				new+="\n"
			elif c=="t":
				new+="\t"
			elif c=="\\":
				new+="\\"
			elif c=="\"":
				new+="\""
			elif c=="\'":
				new+="\'"
		elif c=="\\": pass
		else:
			new+=c
		prev=c
	return new
#-------------------------------------------------------------------------------
#Compiler Reduction Handlers
#-------------------------------------------------------------------------------
def Ignore(reduction,scope): pass

def PassOn(reduction,scope):
	CompileTree(reduction,scope)
	
def IdentifierHandle(reduction,scope):
	#Handles:
	#"<UnaryExpressionNotPlusMinus> ::= <Name>"
	ident=reduction[0].Data
	vname, vscope=CheckNameNodeIdentifiers(ident,scope)
	vvar=vscope[vname]
	var.TypeStack.append(vvar.type)
	var.emit.il.Emit(Emit.OpCodes.Ldloc,vvar.ILAddress)
	
def StringLiteralHandle(reduction,scope):
	#Handles:
	#"<Literal> ::= StringLiteral"
	var.TypeStack.append("str")
	d=fixStringLiteral(reduction[0].Data[1:][:-1])
	var.emit.il.Emit(Emit.OpCodes.Ldstr, d)
	
def FloatLiteralHandle(reduction,scope):
	#Handles:
	#"<NumberLiteral> ::= <FloatPointLiteral>"
	var.TypeStack.append("real")
	var.emit.il.Emit(Emit.OpCodes.Ldc_R4,float(reduction[0].Data))
	
def DecimalIntegerLiteralHandle(reduction,scope):
	#Handles:
	#"<IntegerLiteral> ::= <DecimalIntegerLiteral>"
	var.TypeStack.append("int")
	var.emit.il.Emit(Emit.OpCodes.Ldc_I4,int(reduction[0].Data[0].Data))
	
def HexIntegerLiteralHandle(reduction,scope):
	#Handles:
	#"<IntegerLiteral> ::= HexIntegerLiteral"
	var.TypeStack.append("int")
	var.emit.il.Emit(Emit.OpCodes.Ldc_I4,int(reduction[0].Data[2:],16))
	
def OctalIntegerLiteralHandle(reduction,scope):
	#Handles:
	#"<IntegerLiteral> ::= OctalIntegerLiteral"
	var.TypeStack.append("int")
	var.emit.il.Emit(Emit.OpCodes.Ldc_I4,int(reduction[0].Data[2:],8))
	
def RepeatHandle(reduction,scope):
	#Handles:
	#"<RepeatStatement> ::= repeat <Expression> ':' <nl> <IndentedBlock>"
	#Evaluate expression and push to stack
	print("RepeatHandle")
	EvaluateExpression(reduction[1].Data,scope)
	ltype=var.TypeStack.pop()
	if ltype=="real": pass
	elif ltype=="int": pass
	elif ltype=="int64": pass
	else:
		RaiseSyntaxError("Expected value of type real, int, or int64.")
	#Store loop maximum
	loopMax=var.emit.il.DeclareLocal(System.Int32)
	var.emit.il.Emit(Emit.OpCodes.Stloc,loopMax)
	#Create loop counter, init to 0
	var.emit.il.Emit(Emit.OpCodes.Ldc_I4_0)
	loopCounter=var.emit.il.DeclareLocal(System.Int32)
	var.emit.il.Emit(Emit.OpCodes.Stloc,loopCounter)
	repeatTest= var.emit.il.DefineLabel()
	#Emit GOTO Test
	var.emit.il.Emit(Emit.OpCodes.Br, repeatTest)
	#Loop body
	repeatBody=var.emit.il.DefineLabel()
	var.emit.il.MarkLabel(repeatBody)
	#Body statements
	CompileTree(reduction[4].Data,scope)
	#Increment counter
	#First load to stack
	var.emit.il.Emit(Emit.OpCodes.Ldloc, loopCounter)
	var.emit.il.Emit(Emit.OpCodes.Ldc_I4_1)
	var.emit.il.Emit(Emit.OpCodes.Add)
	var.emit.il.Emit(Emit.OpCodes.Stloc, loopCounter)
	#Test whether x < repeat
	var.emit.il.MarkLabel(repeatTest)
	var.emit.il.Emit(Emit.OpCodes.Ldloc, loopCounter)
	var.emit.il.Emit(Emit.OpCodes.Ldloc, loopMax)
	var.emit.il.Emit(Emit.OpCodes.Blt, repeatBody)
	#Repeat loop done! Yaaaaay
	
def SetVariableUntypedHandle(reduction,scope):
	#Handles:
	#"<SetVariableStatement> ::= <Name> '=' <Expression>"
	#Check to see that <Name> reduces to a valid identifier in the current scope, and get the scope of name
	vname,vscope=CheckNameNodeIdentifiers(reduction[0].Data,scope,ignoreLast=True)
	EvaluateExpression(reduction[2].Data,scope)
	vtype=var.TypeStack.pop()
	if vname in vscope.dict:
		if vscope.dict[vname].type!=vtype:
			#I'm afraid I can't let you do that, Dave
			raise SyntaxError("Attempted to assign value of type %s to identifier %s of type %s" % (vtype,vname,vscope.dict[vname].type))
	else:
		#We generate declaration code
		vscope[vname]=Variable(vtype,var.emit.il.DeclareLocal(var.Types[vtype].CILType))
	#We generate assignment code
	var.emit.il.Emit(Emit.OpCodes.Stloc, vscope[vname].ILAddress)

def MethodInvocationHandle(reduction,scope):
	#Handles:
	#"<MethodInvocation> ::= <Name> '(' <ArgumentList> ')'"
	#"<MethodInvocation> ::= <Name> '(' ')'"
	#Check to see that the <Name> reduces to a valid identifier in the current scope
	vname,vscope=CheckNameNodeIdentifiers(reduction[0].Data,scope)
	vvar=vscope[vname]
	#Var has to be a function to be invokable.
	if vvar.type != "function" or hasattr(vvar,"functionLocation")!=True:
		RaiseSyntaxError("%s is not a function and thus cannot be called." % vname)
	#Check to see if reduction has an argument list, I.E. it has more than 1 nonterminal below it
	if reduction.Count()<=1: #There is no arguments list
		arguments=[]
	else:
		#We need to generate the arguments list. This results in a list of expressions.
		arguments=[]
		GenerateArgumentsListFromNode(reduction[2].Data,arguments)
	#Check for the correct number of arguments!
	if not(len(arguments)==0 and hasattr(vvar,"arguments")==False) and len(arguments) != len(vvar.arguments):
		RaiseSyntaxError("Not enough arguments to call %s" % vname)
	i=0
	#Check types
	for l in arguments:
		EvaluateExpression(l,scope)
		ltype=var.TypeStack.pop()
		if ltype!=vvar.arguments[i]:
			RaiseSyntaxError("Passed argument %s when expected argument %s." % (ltype,vvar.arguments[i]))
		i+=1
	var.emit.il.Emit(Emit.OpCodes.Call, vvar.functionLocation)
	#
def IfStatementHandle(reduction,scope):
	#Handles:
	#"<IfElifStatement> ::= 'if' <Expression> ':' <nl> <IndentedBlock>"
	pass
#-------------------------------------------------------------------------------
#Setup
#-------------------------------------------------------------------------------
SYMBOLS={
"<MethodInvocation> ::= <Name> '(' <ArgumentList> ')'":MethodInvocationHandle,
"<MethodInvocation> ::= <Name> '(' ')'":MethodInvocationHandle,
"<UnaryExpressionNotPlusMinus> ::= <Name>":IdentifierHandle,
"<Literal> ::= StringLiteral":StringLiteralHandle,
"<NumberLiteral> ::= <FloatPointLiteral>":FloatLiteralHandle,
"<IntegerLiteral> ::= <DecimalIntegerLiteral>":DecimalIntegerLiteralHandle,
"<IntegerLiteral> ::= HexIntegerLiteral":HexIntegerLiteralHandle,
"<IntegerLiteral> ::= OctalIntegerLiteral":OctalIntegerLiteralHandle,
"<SetVariableStatement> ::= <Name> '=' <Expression>":SetVariableUntypedHandle,
"<RepeatStatement> ::= repeat <Expression> ':' <nl> <IndentedBlock>":RepeatHandle,
"<IfElifStatement> ::= 'if' <Expression> ':' <nl> <IndentedBlock>":IfStatementHandle
}
#The following are all handled by simply ignoring them
VS=["<nl opt> ::= ","<nl opt> ::= NewLine <nl opt>","<nl> ::= NewLine <nl>","<nl> ::= NewLine"]
for v in VS: SYMBOLS["<ValidStatement> ::= <" + v + ">"]=Ignore
#For sanity's sake, <ValidStatement> ::= [StatementName] is autogenerated to pass on
VS=["IfStatement","WhileStatement","UntilStatement","RepeatStatement","ForStatement","WithStatement","SetVariableStatement","MethodInvocation","ClassDeclaration","InterfaceDeclaration","BreakStatement","ContinueStatement","DoStatement","ImportDeclaration","Raise","ReturnStatement","TryStatement","Assignment"]
for v in VS: SYMBOLS["<ValidStatement> ::= <" + v + ">"]=PassOn
#The following are all handled by the PassOn method
VS=["<Statements> ::= <Statement>","<Statements> ::= <Statement> <Statements>","<Statement> ::= <ValidStatement> <nl>","<Expression> ::= <InclusiveOrExpression>","<InclusiveOrExpression> ::= <ExclusiveOrExpression>","<ExclusiveOrExpression> ::= <AndExpression>","<AndExpression> ::= <EqualityExpression>","<EqualityExpression> ::= <RelationalExpression>","<RelationalExpression> ::= <AdditiveExpression>","<AdditiveExpression> ::= <MultiplicativeExpression>","<MultiplicativeExpression> ::= <UnaryExpression>","<UnaryExpression> ::= <UnaryExpressionNotPlusMinus>","<UnaryExpressionNotPlusMinus> ::= <Primary>","<Primary> ::= <Literal>","<Literal> ::= <NumberLiteral>","<NumberLiteral> ::= <IntegerLiteral>","<IndentedBlock> ::= IndentInc <Block> IndentDec","<Block> ::= <Statement>","<Block> ::= <Statement> <Block>","<IfStatement> ::= <IfElifStatement>"]
for v in VS: SYMBOLS[v]=PassOn



def CompileTree(reduction, scope):
	"""When CompileTree is calledon a node, it looks at every node under that node and calls the proper handler for it."""
	for n in range(reduction.Count()):
		o=reduction[n]
		q=o.Data
		if o.Type()==GOLD.SymbolType.Nonterminal:
			#We have received a reduction, and call its handler
			#Line below renders the branch into <NonterminalName> format
			branch=q.Parent.Text(False)
			if branch in SYMBOLS:
				print("Handled nonterminal -%s-" % branch)
				SYMBOLS[branch](q,scope)
			else:
				print("Unhandled nonterminal -%s-" % branch)
		else:
			#We have received a terminal, nothing to do with it
			pass