import argparse, random
from colorama import Style, just_fix_windows_console

just_fix_windows_console()


def random_str(length=8, charset=None):
    res = ''
    for i in range(length):
        res += random.choice(charset or 'abcdedghijklmnopqrstuvwxyz_')
    return res


def find_line_with(lines, text):
    for i in range(len(lines)):
        if text in lines[i]:
            return i
    return len(lines) - 1


def get_lines_between(lines, start, end):
    return lines[start+1:end-1]


def count_lines(text):
    return text.strip().count('\n')+1


def remove_empty_lines(lines):
    return [x for x in lines if x]


def typeof(val):
    val = val.strip()
    if val[0] == '@':
        return 'const'
    if val[0] == val[-1] and val[0] == '"':
        return 'string'
    try:
        float(i)
        return "number"
    finally:
        return "var"


def compile_value(val):
    val = val.strip()
    if val[0] == '@':
        return val
    try:
        return float(i)
    finally:
        return val


def compile_cond(cond):
    cond = cond.strip()
    if cond == 'always':
        return 'always false false'
    cond = cond.split()
    oper = cond[1]
    a = cond[0]
    b = cond[2]
    return {
        '==': 'equal',
        '!=': 'notEqual',
        '===': 'strictEqual',
        '>': 'greaterThan',
        '<': 'lessThan',
        '>=': 'greaterThanEq',
        '<=': 'lessThanEq'
    }.get(oper, 'always') + f' {a} {b}'


# Convert things like '"str1"+"str2"+var' to
# ['"str1"','"str2"','var']
#
# TODO: Improve accuracy
def split_expr(expr):
    return [compile_value(x) for x in expr.split('+')]


def compile(code, offset=0):
    code = code.strip()
    result = ''
    lines = remove_empty_lines(code.split('\n'))
    stack = []
    jumps = {}
    functions = ''
    
    i = 0
    while i < len(lines):
        line = lines[i]
        cmd = line.split(' ')[0]
        args = line.split(' ')[1:]
        arg = ' '.join(args)
        while '\n\n' in result:
            result = result.replace('\n\n', '\n')
        result = result.strip() + '\n'

        if cmd == 'mlog':
            result += arg
        elif cmd == 'if':
            stack.append(f'if({i})')
            end = len(lines)
            j = i+1
            while j < end:
                if lines[j].startswith('if'):
                    stack.append(f'if({j})')
                if lines[j].startswith('while'):
                    stack.append(f'while({j})')
                elif lines[j] == 'endif':
                    if len(stack) <= 1:
                        end = j+1
                    stack = stack[:-1]
                j += 1
            content = compile('\n'.join(get_lines_between(lines, i, end)), i+2).strip()
            start_line = count_lines(result)
            end_line = start_line + count_lines(content) + 2
            content_line = start_line + 2
            result += f'jump {content_line+offset} {compile_cond(arg)}\njump {end_line+offset} always false false\n{content}'
            i = end-1
            stack = stack[:-1]
        elif cmd == 'endif':
            break
        elif cmd == 'while':
            stack.append(f'while({i})')
            end = len(lines)
            j = i+1
            while j < end:
                if lines[j].startswith('if'):
                    stack.append(f'if({j})')
                if lines[j].startswith('while'):
                    stack.append(f'while({j})')
                elif lines[j] == 'endwhile':
                    if len(stack) <= 1:
                        end = j+1
                    stack = stack[:-1]
                j += 1
            content = compile('\n'.join(get_lines_between(lines, i, end)), i+1).strip()
            start_line = count_lines(result)
            result += f'{content}\njump {start_line+offset} {compile_cond(arg)}'
            i = end-1
            stack = stack[:-1]
        elif cmd == 'endwhile':
            break
        # Basic
        elif cmd == 'printf':
            contents = split_expr(' '.join(args[1:]))
            for c in contents:
                result += f'print {c}'
            result += f'print flush {args[0]}'
        elif cmd == 'print':
            result += 'print ' + arg
        elif cmd == 'set':
            result += f'set {args[0]} {args[1]}'
        elif cmd == 'jump':
            id = random_str()
            result += f'jump [__jump_{id}]'
            jumps[id] = int(arg)
        elif cmd == 'end':
            result += 'end'
        # Advanced
        elif cmd == 'def':
            stack.append(f'fn({i})')
            end = len(lines)
            j = i+1
            while j < end:
                if lines[j].startswith('if'):
                    stack.append(f'if({j})')
                if lines[j].startswith('while'):
                    stack.append(f'while({j})')
                elif lines[j] == 'endfn':
                    if len(stack) <= 1:
                        end = j+1
                    stack = stack[:-1]
                j += 1
            content = compile('\n'.join(get_lines_between(lines, i, end)), i+2).strip()
            functions += f'fn_{arg}:\n{content}\nset @counter __return'
            i = end-1
            stack = stack[:-1]
        elif cmd == 'endfn':
            pass
        elif cmd == 'call':
            result += f'set __return @counter\nop add __return 2\njump fn_{args[0]}'
            # TODO
        # World
        elif cmd == 'radar':
            result += 'radar ' + arg
        elif cmd == 'control':
            result += 'control ' + arg
        elif cmd == 'sensor':
            result += 'sensor ' + arg
        # Unit control
        elif cmd == 'ubind':
            result += 'ubind ' + arg
        elif cmd == 'ucontrol':
            result += 'ucontrol ' + arg
        elif cmd == 'uradar':
            result += 'uradar ' + arg
        elif cmd == 'ulocate':
            result += 'ulocate ' + arg
        # Debug
        elif cmd == 'setstatus':
            result += f'set __status {arg}'
        # Command not found
        else:
            result += f'set __status "Unknown command "{cmd}" on line {i+offset}"'
        
        i += 1
        result += ' //__line'+str(i)
        
        
    print(result)
    
    result += '\n' + functions
    
    for i, j in enumerate(jumps):
        result = result.replace(f'[__jump_{j}]', str(find_line_with(result.split('\n'), '//__line'+str(jumps[j]))))
            
    #breakpoint()
    return '\n'.join([x.split('//__line')[0] for x in result.split('\n')])



def main():
    argparser = argparse.ArgumentParser(
        prog='MindL compiler',
        description='MindL is a programming language for Mindustry',
        usage='python3 main.py [file] [output]',
    )

    argparser.add_argument('-i', '--input', help='File to compile. Defaults to script.mlx if not specified.', default='script.mlx', required=False)
    argparser.add_argument('-o', '--output', help='Output file. Defaults to stdout if not specified.', required=False)
    argparser.add_argument('-f', '--format', help='Add line numbers to output (only in console)', action='store_false')

    args = argparser.parse_args()

    with open(args.input, 'r') as f:
        code = f.read()
    
    result = compile(code)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(result)
    else:
        print(f'Compiled from {args.input}:\n')
        if args.format:
            lines = result.split('\n')
            for i in range(len(lines)):
                print(Style.DIM + f'{str(i):>3} | ' + Style.RESET_ALL + lines[i])
        else:
            print(result)

if __name__ == '__main__':
    main()