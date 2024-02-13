from api import command

@command('print')
def print(arg, args):
	content = ' '.join(args[1:])
	return f'print {content}\nprint flush {args[0]}\n'