
#!/usr/bin/env python3
import os
import shlex
import sys

ALIASES = {
    "list": "ls", "show": "cat", "copy": "cp", "move": "mv",
    "del": "rm", "newdir": "mkdir", "newfile": "touch",
}
BUILTINS = ["go", "quit", "path", "say", "info", "past", "osinfo"]

class Opsh:
    def __init__(self):
        self.last_status = 0
        self.history = []

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
argv = shlex.split(text, posix=True)
        if argv and argv[0] in ALIASES:
            argv[0] = ALIASES[argv[0]]
        return argv

    def builtin(self, argv):
        cmd, args = argv[0], argv[1:]
        if cmd == "go":
            target = args[0] if args else os.path.expanduser("~")
            try:
                os.chdir(os.path.expanduser(target))
            except OSError as e:
                print(f"go: {target}: {e.strerror}", file=sys.stderr)
                return 1
        elif cmd == "quit":
            sys.exit(int(args[0]) if args else 0)
        elif cmd == "path":
            print(os.getcwd())
        elif cmd == "say":
            print(" ".join(args))
        elif cmd == "osinfo":
            print("Systèmes d'Exploitation -- UIR/ESIN")
        elif cmd == "info":
            print("builtins : " + ", ".join(BUILTINS))
            print("aliases  : " + ", ".join(f"{k}={v}" for k, v in ALIASES.items()))
            print("pipe : cmd1 -> cmd2")
        elif cmd == "past":
            for n, h in enumerate(self.history, 1):
                print(f"{n:>4}  {h}")
        return 0
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
         if argv[0] in BUILTINS:
            self.last_status = self.builtin(argv)
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
        if line.strip():
                self.history.append(line)
        self.run_line(line)
   def main():
    shell = Opsh()
    shell.repl()

   if __name__ == "__main__":
    main()
