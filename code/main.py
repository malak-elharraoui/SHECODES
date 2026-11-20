#!/usr/bin/env python3
import os
import shlex
import sys

class Opsh:
    def __init__(self):
        self.last_status = 0

@staticmethod
 def split_pipes(line):
        parts, cur, quote, i = [], "", None, 0
        while i < len(line):
            c = line[i]
            if c in "'\"":
                quote = None if quote == c else (c if quote is None else quote)
            if quote is None and line.startswith("->", i):
                parts.append(cur)
                cur, i = "", i + 2
                continue
            cur += c
            i += 1
        parts.append(cur)
        return [p.strip() for p in parts]

    @staticmethod
    def parse_command(text):
        return shlex.split(text, posix=True)
    def run_line(self, line):
        line = line.strip()
        if not line or line.startswith("#"):
            return
try:
            commands = [self.parse_command(p) for p in self.split_pipes(line)]
        except ValueError as e:
            print(f"opsh: syntax error: {e}", file=sys.stderr)
            self.last_status = 2
            return
        if any(not argv for argv in commands):
            print("opsh: syntax error near '->'", file=sys.stderr)
            self.last_status = 2
            return
        argv = commands[0]
        pid = os.fork()
        if pid == 0:
            try:
                os.execvp(argv[0], argv)
            except FileNotFoundError:
                print(f"opsh: command not found: {argv[0]}", file=sys.stderr)
                os._exit(127)
        _, st = os.waitpid(pid, 0)
        self.last_status = os.waitstatus_to_exitcode(st)


     def repl(self):
         while True:
             try:
                 line = input("opsh> ")
             except EOFError:
                 print()
                  break
        self.run_line(line)
   def main():
    shell = Opsh()
    shell.repl()


if __name__ == "__main__":
    main()
