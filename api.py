commands = {}

def command(name):
	def wrapper(func):
		commands[name] = func
		return func
	return wrapper