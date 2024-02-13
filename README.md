# MindL Compiler

MindL Compiler is a Python script designed to compile code written in MindL, a custom programming language for the game Mindustry. The script provides features like converting conditional statements, looping structures, and handling various commands specific to the game's logic. It includes a set of utility functions for string manipulation, line searching, and expression evaluation.

## Features

- Compile MindL code into an executable format for Mindustry.
- Handle conditional expressions and loops (`if`, `while`).
- Provide utility functions for string operations and type checking.
- Support for Mindustry-specific commands (`print`, `radar`, `control`, `sensor`, `ubind`, `ucontrol`, `uradar`, `ulocate`).
- Debugging feature to set status messages in the compiled output.
- Command-line interface for specifying input and output files.

## Usage

The script can be invoked from the command line with optional arguments to specify the input and output files.

### Command-line Arguments

- `-i`, `--input`: Specify the file to compile. Defaults to `script.mlx` if not provided.
- `-o`, `--output`: Specify the output file. If not provided, the result is printed to stdout.
- `-f`, `--format`: Add line numbers to the output when printing to the console.

### Example

```shell
python3 main.py -i my_script.mlx -o compiled.txt
```
This will compile the my_script.mlx file and save the output to compiled.txt.

## Dependencies

- `argparse`: For parsing command-line options.
- `random`: To generate random strings.
- `colorama`: For handling console output formatting.

Before running the script, ensure that colorama is installed and the console is configured for proper output.

## Contributions

Contributions are welcome. Please feel free to report issues or submit pull requests on the repository.

## License

This project is open-sourced under the GPL-3.0 License.
