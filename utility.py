from compiler import var

def ProgramEnd():
	"""Ends the compilation, optionally pausing to allow user to review output."""
	if "pause" in var.opts:
		raw_input("Press enter to exit...")
	exit()
	
def FormatError(parser,expecting=False):
	"""Returns Line/column/read token/expected token information for use in error messages."""
	message = "Line " + str(parser.CurrentPosition().Line) + ", column " + str(parser.CurrentPosition().Column) + ":\n" + "Read: "+str(parser.CurrentToken().Data)
	if expecting:
		message+="\nExpecting: " + parser.ExpectedSymbols().Text()
	return message
def RaiseSyntaxError(reason=""):
	"""Raises a syntax error and ends the program."""
	print("SYNTAX ERROR " + reason + "\n" + FormatError(var.mirParser))
	ProgramEnd()