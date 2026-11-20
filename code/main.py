#!/usr/bin/env python3
import os
import shlex
import sys

class Opsh:
    def __init__(self):
        self.last_status = 0

    def run_line(self, line):
        line = line.strip()
        if not line or line.startswith("#"):
            return
        argv = shlex.split(line, posix=True)
        if not argv:
            return
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
