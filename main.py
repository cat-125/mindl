import argparse

from api import commands
import commands as _commands

def compile(code):
	result = ''
	lines = code.split('\n')

	for i in range(len(lines)):
		line = lines[i]
		cmd = line.split(' ')[0]
		args = line.split(' ')[1:]
		arg = ' '.join(args)

		result += commands[cmd](arg, args)
	
	return result



def main():
	argparser = argparse.ArgumentParser(
		prog='MindL compiler',
		description='Programming language for Mindustry',
		usage='python3 main.py [file] [output]',
	)

	argparser.add_argument('--file', help='File to compile. Defaults to script.mlx if not specified.', default='script.mlx', required=False)
	argparser.add_argument('--output', help='Output file. Defaults to stdout if not specified.', required=False)

	args = argparser.parse_args()

	with open(args.file, 'r') as f:
		code = f.read()
	
	result = compile(code)

	if args.output:
		with open(args.output, 'w') as f:
			f.write(result)
	else:
		print(result)

if __name__ == '__main__':
	main()