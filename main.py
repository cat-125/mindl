import argparse, random, re
from colorama import Style, just_fix_windows_console


LINE_REGEX = re.compile(r"\$\{line(\d+)\}")
debug = False

just_fix_windows_console()

def random_str(length=8, charset=None):
    res = ''
    for _ in range(length):
        res += random.choice(charset or 'abcdedghijklmnopqrstuvwxyz_')
    return res


def find_line_with(lines, text):
    for i in range(len(lines)-1):
        if text in lines[i]+'\n':
            return i
    print(f'not found {text} in {lines}')
    return len(lines)-1


def get_lines_between(lines, start, end):
    return lines[start+1:end-1]


def count_lines(text):
    return text.strip().count('\n')+1


def remove_empty_lines(lines):
    return [x for x in lines if x]


def insert_line_before(text, line, i):
    lines = text.split('\n')
    lines.insert(i, line)
    return '\n'.join(lines)


def typeof(val):
    val = val.strip()
    if val[0] == '@':
        return 'const'
    if val[0] == val[-1] and val[0] == '"':
        return 'string'
    try:
        float(val)
        return "number"
    except Exception:
        return "var"


def compile_value(val):
    val = val.strip()
    if val[0] == '@':
        return val
    try:
        return float(val)
    except Exception:
        return val


def compile_cond(cond):
    cond = cond.strip()
    if cond == 'always' or cond == '':
        return 'always false false'
    cond = cond.split()
    a = cond[0]
    if len(cond) == 1:
        return f'notEqual {a} null'
    oper = cond[1]
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


# Convert things like '"str1"+@const+var' to
# ['"str1"','@const','var']
#
# TODO: Improve accuracy
def split_expr(expr):
    return [compile_value(x) for x in expr.split('+')]


def compile(code, offset=0):
    code = code.strip()
    result = ''
    lines = code.split('\n')
    stack = []
    functions = ''
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line == '':
            i += 1
            continue
        cmd = line.split(' ')[0]
        args = line.split(' ')[1:]
        arg = ' '.join(args)
        while '\n\n' in result:
            result = result.replace('\n\n', '\n')
        result = result.strip() + '\n'

        # Basic
        if cmd == 'mlog':
            result += arg
        elif cmd == 'printf':
            contents = split_expr(' '.join(args[1:]))
            for c in contents:
                result += f'print {c}\n'
            result += f'print flush {args[0]}'
        elif cmd == 'print':
            result += 'print ' + arg
        elif cmd == 'set':
            result += f'set {args[0]} {args[1]}'
        elif cmd == 'end':
            result += 'end'
        # Flow control
        elif cmd == 'jump':
            t = int(args[0])
            result += 'jump ${line' + str(t) + f'}} {compile_cond(" ".join(args[1:]))}'
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
            content = compile('\n'.join(get_lines_between(lines, i+1, end)), i+2).strip()
            functions += f'fn_{arg}:\n{content}\nset @counter __return'
            i = end-1
            stack = stack[:-1]
        elif cmd in ('endif', 'endwhile', 'endfn'):
            break
        elif cmd == 'call':
            result += f'set __return @counter\nop add __return 2\njump fn_{args[0]}'
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
    
    if functions:
        result += '\nend\n' + functions
    
    lines = result.split('\n')
    for i in range(len(lines)):
        lines[i] = re.sub(LINE_REGEX, lambda x: str(find_line_with(lines, '//__line'+x.group(1))), lines[i])
    
    #breakpoint()
    if debug:
        return '\n'.join(lines)
    else:
        return '\n'.join([x.split('//__line')[0] for x in lines if x])



def main():
    global debug
    argparser = argparse.ArgumentParser(
        prog='MindL compiler',
        description='MindL is a programming language for Mindustry',
        usage='python3 main.py [file] [output]',
    )

    argparser.add_argument('-i', '--input', help='File to compile. Defaults to script.mlx if not specified.', default='script.mlx', required=False)
    argparser.add_argument('-o', '--output', help='Output file. Defaults to stdout if not specified.', required=False)
    argparser.add_argument('-f', '--format', help='Add line numbers to output (only in console)', action='store_true')
    argparser.add_argument('-d', '--debug', help='Debug mode', action='store_true')

    args = argparser.parse_args()

    debug = args.debug

    with open(args.input, 'r') as f:
        code = f.read()
    
    result = compile(code)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(result)
    else:
        print(f'Compiled from {args.input}:\n\n----------------')
        if args.format:
            lines = result.split('\n')
            for i in range(len(lines)):
                print(Style.DIM + f'{str(i):>3} | ' + Style.RESET_ALL + lines[i])
        else:
            print(result)
        print('----------------')

if __name__ == '__main__':
    main()