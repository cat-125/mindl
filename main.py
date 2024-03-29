import argparse
import random
import re
import mappings
from colorama import Fore, Style, just_fix_windows_console


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
    if debug:
        print(f'not found {text} in {lines}')
    return len(lines)-1


def find_line_by_number(lines, number):
    for i in range(len(lines)-1):
        if lines[i]['source_line'] == number:
            return i
    if debug:
        print(f'not found line {number} in {lines}')
    return len(lines)-1


def get_lines_between(lines, start, end):
    result = []
    print(lines, start, end)
    i = start+1
    while i < end:
        result.append(lines[i])
        i += 1
    return result


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
    return mappings.COMPARSION.get(oper, 'always') + f' {a} {b}'


# Convert things like '"str1"+@const+var' to
# ['"str1"','@const','var']
#
# TODO: Improve accuracy
def split_expr(expr):
    return [compile_value(x) for x in expr.split('+')]


def compile(code, offset=0):
    code = code.strip()
    result = []
    lines = code.split('\n')
    stack = []
    functions = ''

    i = 0
    while i < len(lines):
        source_line = lines[i].strip()
        if source_line == '':
            i += 1
            continue
        cmd = source_line.split(' ')[0]
        args = source_line.split(' ')[1:]
        arg = ' '.join(args)
        line = ''

        # Basic
        if cmd == 'mlog':
            line = arg
        elif cmd == 'printf':
            contents = split_expr(' '.join(args[1:]))
            for c in contents:
                line += f'print {c}\n'
            line += f'printflush {args[0]}'
        elif cmd == 'print':
            line = 'print ' + arg
        elif cmd == 'printflush':
            line = 'printflush ' + arg
        elif cmd == 'set':
            line = f'set {arg}'
        # Flow control
        elif cmd == 'jump':
            line = 'jump ${line' + \
                args[0] + '} ' + compile_cond(" ".join(args[1:]))
        elif cmd == 'if':
            stack.append(f'if({i})')
            end = len(lines)
            j = i+1
            while j < end:
                if lines[j].startswith('if'):
                    stack.append(f'if@{j}')
                elif lines[j].startswith('ifnot'):
                    stack.append(f'ifnot@{j}')
                elif lines[j].startswith('while'):
                    stack.append(f'while@{j}')
                elif lines[j] == 'endif':
                    if len(stack) <= 1:
                        end = j+1
                    stack = stack[:-1]
                j += 1
            content = compile(
                '\n'.join(get_lines_between(lines, i, end)), i+2).strip()
            start_line = len(result)
            end_line = start_line + count_lines(content) + 2
            content_line = start_line + 2
            line = f'jump {content_line+offset} {compile_cond(arg)}\njump {end_line+offset} always false false\n{content}'
            i = end-1
            stack = stack[:-1]
        elif cmd == 'ifnot':
            stack.append(f'ifnot@{i}')
            end = len(lines)
            j = i+1
            while j < end:
                if lines[j].startswith('if'):
                    stack.append(f'if@{j}')
                elif lines[j].startswith('ifnot'):
                    stack.append(f'ifnot@{j}')
                elif lines[j].startswith('while'):
                    stack.append(f'while@{j}')
                elif lines[j] == 'endif':
                    if len(stack) <= 1:
                        end = j+1
                    stack = stack[:-1]
                j += 1
            content = compile(
                '\n'.join(get_lines_between(lines, i, end)), i+1).strip()
            start_line = len(result)
            end_line = start_line + count_lines(content) + 1
            line = f'jump {end_line+offset} {compile_cond(arg)}\n{content}'
            i = end-1
            stack = stack[:-1]
        elif cmd == 'while':
            stack.append(f'while@{i}')
            end = len(lines)
            j = i+1
            while j < end:
                if lines[j].startswith('if'):
                    stack.append(f'if@{j}')
                elif lines[j].startswith('ifnot'):
                    stack.append(f'ifnot@{j}')
                elif lines[j].startswith('while'):
                    stack.append(f'while@{j}')
                elif lines[j] == 'endwhile':
                    if len(stack) <= 1:
                        end = j+1
                    stack = stack[:-1]
                j += 1
            content = compile(
                '\n'.join(get_lines_between(lines, i, end)), i+1).strip()
            start_line = len(result)
            line = f'{content}\njump {start_line+offset} {compile_cond(arg)}'
            i = end-1
            stack = stack[:-1]
        elif cmd == 'def':
            stack.append(f'fn@{i}')
            end = len(lines)
            j = i+1
            while j < end:
                if lines[j].startswith('if'):
                    stack.append(f'if@{j}')
                elif lines[j].startswith('ifnot'):
                    stack.append(f'ifnot@{j}')
                elif lines[j].startswith('while'):
                    stack.append(f'while@{j}')
                elif lines[j] == 'endfn':
                    if len(stack) <= 1:
                        end = j+1
                    stack = stack[:-1]
                j += 1
            source = '\n'.join(get_lines_between(lines, i, end))
            content = compile(source, i+1)
            functions += f'fn_{arg}:\n{content}\nset @counter __return\n'
            i = end-1
            stack = stack[:-1]
        elif cmd in ('endif', 'endwhile', 'endfn'):
            break
        elif cmd == 'call':
            line = f'set __return @counter\nop add __return 2\njump fn_{args[0]}'
        elif cmd == 'end':
            line = 'end'
        # World
        elif cmd == 'radar':
            line = 'radar ' + arg
        elif cmd == 'control':
            line = 'control ' + arg
        elif cmd == 'sensor':
            line = 'sensor ' + arg
        # Unit control
        elif cmd == 'ubind':
            line = 'ubind ' + arg
        elif cmd == 'ucontrol':
            line = 'ucontrol ' + arg
        elif cmd == 'uradar':
            line = 'uradar ' + arg
        elif cmd == 'ulocate':
            line = 'ulocate ' + arg
        # Debugging
        elif cmd == 'setstatus':
            line = f'set __status {arg}'
        # Command not found
        else:
            line = f'set __status "Unknown command "{cmd}" on line {i+offset}"'
            print(Fore.YELLOW + f'WARNING: Unknown command "{cmd}" on line {i+offset}' + Style.RESET_ALL)

        i += 1
        if line:
            result.append({
                'text': line,
                'source_line': i
            })
    
    if debug:
        print(result, end='\n\n')
    
    output = ''

    for line in result:
        line['text'] = re.sub(LINE_REGEX, lambda x: str(
            find_line_by_number(result, int(x.group(1)))), line['text'])
        if debug:
            output += line['text'] + ' // from line ' + str(line['source_line'] + offset) + '\n'
        else:
            output += line['text'] + '\n'

    if functions:
        output += '\nend\n' + functions

    # breakpoint()
    return output


def main():
    global debug
    argparser = argparse.ArgumentParser(
        prog='MindL compiler',
        description='MindL is a programming language for Mindustry',
        usage='python3 main.py [file] [output]',
    )

    argparser.add_argument(
        '-i', '--input', help='File to compile. Defaults to script.mlx if not specified.', default='script.mlx', required=False)
    argparser.add_argument(
        '-o', '--output', help='Output file. Defaults to stdout if not specified.', required=False)
    argparser.add_argument(
        '-f', '--format', help='Add line numbers to output (only in console)', action='store_false')
    argparser.add_argument(
        '-d', '--debug', help='Debug mode', action='store_false')

    args = argparser.parse_args()

    debug = args.debug

    with open(args.input, 'r') as f:
        code = f.read()

    result = compile(code)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(result)
    else:
        print(f'Compiled from {args.input}:\n\n' + '-' * 32)
        if args.format:
            lines = result.split('\n')
            for i in range(len(lines)):
                print(Style.DIM + f'{str(i):>3} | ' +
                      Style.RESET_ALL + lines[i])
        else:
            print(result)
        print('-' * 32)


if __name__ == '__main__':
    main()
