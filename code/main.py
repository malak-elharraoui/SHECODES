
#!/usr/bin/env python3
import os
import re
import shlex
import signal
import sys

try:
    import readline
except ImportError:
    readli@staticmethodne = None


ALIASES = {
    "list": "ls", "show": "cat", "copy": "cp", "move": "mv",
    "del": "rm", "newdir": "mkdir", "newfile": "touch",
}
BUILTINS = ["go", "quit", "path", "say", "info", "past", "osinfo", "export","jobs", "fg"]

HISTORY_FILE = os.path.expanduser("~/.opsh_history")
RC_FILE = os.path.expanduser("~/.opshrc")

class Opsh:
    def __init__(self):
        self.vars = {}
        self.last_status = 0
        self.last_bg_pid = "" 
        self.history = []
        self.jobs = {}         
        self.next_job = 1 
        signal.signal(signal.SIGCHLD, self.on_sigchld)

    def on_sigchld(self, signum, frame):
        for num, (pids, cmd) in list(self.jobs.items()):
            alive = []
            for pid in pids:
                try:
                    done, status = os.waitpid(pid, os.WNOHANG)
                except ChildProcessError:
                    done = pid
                if done != pid:
                    alive.append(pid)
            if alive:
                self.jobs[num] = (alive, cmd)
            else:
                print(f"\n[{num}]+ Done {cmd}")
                del self.jobs[num]


    def get_var(self, name):
        if name == "?":
            return str(self.last_status)
        if name == "!":
            return str(self.last_bg_pid)
        if name == "$":
            return str(os.getpid())
        return self.vars.get(name, os.environ.get(name, ""))

    def expand(self, line):
        out, i, quote = "", 0, None
        while i < len(line):
            c = line[i]
            if c == "'" and quote != '"':
                quote = None if quote == "'" else "'"
                out += c
                i += 1
            elif c == '"' and quote != "'":
                quote = None if quote == '"' else '"'
                out += c
                i += 1
            elif quote == "'":
                out += c
                i += 1
            elif line.startswith("$((", i):
                end = line.index("))", i)
                expr = self.expand(line[i + 3:end])
                expr = re.sub(r"[A-Za-z_][A-Za-z0-9_]*",
                              lambda v: self.get_var(v.group()) or "0", expr)
                out += self.arith(expr)
                i = end + 2
            elif line.startswith("$(", i):
                end = self.matching_paren(line, i + 1)
                out += self.capture(line[i + 2:end])
                i = end + 1
            elif c == "`":
                end = line.index("`", i + 1)
                out += self.capture(line[i + 1:end])
                i = end + 1
            elif line.startswith("${", i):
                end = line.index("}", i)
                out += self.get_var(line[i + 2:end])
                i = end + 1
            elif c == "$" and i + 1 < len(line):
                m = re.match(r"[A-Za-z_][A-Za-z0-9_]*|[?!$]", line[i + 1:])
                if m:
                    out += self.get_var(m.group())
                    i += 1 + len(m.group())
                else:
                    out += c
                    i += 1
            else:
                out += c
                i += 1
        return out

    @staticmethod
    def matching_paren(s, start):
        depth = 0
        for j in range(start, len(s)):
            depth += {"(": 1, ")": -1}.get(s[j], 0)
            if depth == 0:
                return j
        raise SyntaxError("missing )")

    @staticmethod
    def arith(expr):
        if not re.fullmatch(r"[\d\s+\-*/%()]*", expr):
            raise SyntaxError(f"bad arithmetic: {expr}")
        return str(int(eval(expr.replace("/", "//"))))

    def capture(self, cmdline):
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            signal.signal(signal.SIGCHLD, signal.SIG_DFL)
            os.close(r)
            os.dup2(w, 1)
os.close(w)
            self.run_line(cmdline)
            sys.stdout.flush()
            os._exit(self.last_status)
        os.close(w)
        with os.fdopen(r) as f:
            data = f.read()
        os.waitpid(pid, 0)
        return data.rstrip("\n")
   

@staticmethod
    def split_pipes(line):
        """Split on '->' but not inside quotes."""
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
        lex = shlex.shlex(text, posix=True, punctuation_chars="<>&")
        lex.whitespace_split = True
        tokens = list(lex)
        argv, infile, outfile, append, bg = [], None, None, False, False
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t in (">", ">>"):
                outfile, append = tokens[i + 1], t == ">>"
                i += 2
            elif t == "<":
               infile = tokens[i + 1]
                i += 2
            elif t == "&":
                bg = True
                i += 1
            else:
                argv.append(t)
                i += 1
        if argv and argv[0] in ALIASES:
            argv[0] = ALIASES[argv[0]]
        return argv, infile, outfile, append, bg



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
            self.save_history()
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
            print("pipe : cmd1 -> cmd2   redirections: > >> <   background: &")
        elif cmd == "past":
            for n, h in enumerate(self.history, 1):
                print(f"{n:>4}  {h}")
        elif cmd == "export":
            for a in args:
                name, _, value = a.partition("=")
                os.environ[name] = value if "=" in a else self.vars.get(name, "")
        elif cmd == "jobs":
            for num, (pids, c) in self.jobs.items():
                print(f"[{num}] {pids[-1]} Running {c}")
        elif cmd == "fg":
            num = int(args[0].lstrip("%")) if args else max(self.jobs, default=None)
            if num not in self.jobs:
                print("fg: no such job", file=sys.stderr)
                return 1
            pids, c = self.jobs.pop(num)
            print(c)
            signal.signal(signal.SIGINT, lambda s, f: [os.kill(p, s) for p in pids])
            try:
                return self.wait_for(pids)
            finally:
                signal.signal(signal.SIGINT, signal.default_int_handler)
        return 0



 def run_line(self, line):
        line = line.strip()
        if not line or line.startswith("#"):
            return
        try:
            line = self.expand(line)
            m = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)", line)
            if m:
                self.vars[m.group(1)] = shlex.split(m.group(2))[0] if m.group(2) else ""
                if m.group(1) in os.environ:
                    os.environ[m.group(1)] = self.vars[m.group(1)]
                self.last_status = 0
                return
            commands = [self.parse_command(p) for p in self.split_pipes(line)]
        except (SyntaxError, ValueError, IndexError, ZeroDivisionError) as e: 
         print(f"opsh: syntax error: {e}", file=sys.stderr)
         self.last_status = 2
            return

        if any(not c[0] for c in commands):
            print("opsh: syntax error near '->'", file=sys.stderr)
            self.last_status = 2
            return

        self.last_status = self.run_pipeline(commands, line)
 
    def run_pipeline(self, commands, text):         
        background = commands[-1][4] 
        if len(commands) == 1 and commands[0][0][0] in BUILTINS and not background:
             return self.run_builtin_redirected(commands[0])
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        try: 
             return self.fork_pipeline(commands, text, background)
        finally:
            signal.signal(signal.SIGINT, signal.default_int_handler)
 
  def fork_pipeline(self, commands, text, background): 
      pids, prev_read = [], None 
      for idx, (argv, infile, outfile, append, _) in enumerate(commands): 
          last = idx == len(commands) - 1 
          if not last: 
              r, w = os.pipe() 
          pid = os.fork() 
          if pid == 0:
              signal.signal(signal.SIGINT, signal.SIG_DFL)
              signal.signal(signal.SIGCHLD, signal.SIG_DFL)
              if background:                     
                  os.setpgid(0, 0)
              if prev_read is not None:      
                  os.dup2(prev_read, 0)                     
                  os.close(prev_read)
              if not last: 
                  os.close(r)
                  os.dup2(w, 1)
                  os.close(w)
                try:
                    self.apply_redirections(infile, outfile, append)
                    if argv[0] in BUILTINS:
                        status = self.builtin(argv)
                        sys.stdout.flush()
                        os._exit(status)
                    os.execvp(argv[0], argv)
                except FileNotFoundError as e:
                    print(f"opsh: {e.filename + ': no such file' if e.filename else 'command not found: ' + argv[0]}", file=sys.stderr)
                    os._exit(127)
                except OSError as e:
                    print(f"opsh: {e.filename or argv[0]}: {e.strerror}", file=sys.stderr)
                    os._exit(126)
            pids.append(pid)
            if prev_read is not None:
                os.close(prev_read)
            if not last:
                os.close(w)
                prev_read = r
        if background:
            num = self.next_job
            self.next_job += 1
            self.jobs[num] = (list(pids), text.rstrip("& "))
            self.last_bg_pid = pids[-1]
            print(f"[{num}] {pids[-1]}")
            return 0
        return self.wait_for(pids)

    def wait_for(self, pids):
        status = 0
        for pid in pids:
            try:
                _, st = os.waitpid(pid, 0)
            except ChildProcessError:
                continue
            status = os.waitstatus_to_exitcode(st)
            if status < 0:
                print()
                status = 128 - status
        return status

@staticmethod
    def apply_redirections(infile, outfile, append):
        if infile:
            fd = os.open(infile, os.O_RDONLY)
            os.dup2(fd, 0)
            os.close(fd)
        if outfile:
            flags = os.O_WRONLY | os.O_CREAT | (os.O_APPEND if append else os.O_TRUNC)
            fd = os.open(outfile, flags, 0o644)
            os.dup2(fd, 1)
            os.close(fd)
    
def run_builtin_redirected(self, cmd):
        argv, infile, outfile, append, _ = cmd
        saved = os.dup(0), os.dup(1)
        try:
            sys.stdout.flush()
            self.apply_redirections(infile, outfile, append)
            status = self.builtin(argv)
            sys.stdout.flush()
        except (OSError, ValueError) as e:
            print(f"opsh: {e}", file=sys.stderr)
            status = 1
        finally:
            os.dup2(saved[0], 0)
            os.dup2(saved[1], 1)
            os.close(saved[0])
            os.close(saved[1])
        return status

def parse_block(self, lines, i, ends):
        nodes = []
        while i < len(lines):
            line = lines[i].strip()
            word = line.split()[0] if line else ""
            if word in ends:
                return nodes, i
            if word == "if":
                cond = line[2:].strip()
                then_part, i = self.parse_block(lines, i + 2, ("else", "fi"))
                else_part = []
                if lines[i].strip() == "else":
                    else_part, i = self.parse_block(lines, i + 1, ("fi",))
                nodes.append(("if", cond, then_part, else_part))
            elif word == "for":
                parts = line.split()
                body, i = self.parse_block(lines, i + 2, ("done",))
                nodes.append(("for", parts[1], " ".join(parts[3:]), body))
            elif word == "while":
                body, i = self.parse_block(lines, i + 2, ("done",))
                nodes.append(("while", line[5:].strip(), body))
            elif line and not line.startswith("#"):
                nodes.append(("cmd", line))
            i += 1
        return nodes, i

def run_nodes(self, nodes):
        for node in nodes:
            kind = node[0]
            if kind == "cmd":
                self.run_line(node[1])
            elif kind == "if":
                self.run_line(node[1])
                self.run_nodes(node[2] if self.last_status == 0 else node[3])
            elif kind == "for":
                for value in shlex.split(self.expand(node[2])):
                    self.vars[node[1]] = value
                    self.run_nodes(node[3])
            elif kind == "while":
                while True:
                    self.run_line(node[1])
                    if self.last_status != 0:
                        break
                    self.run_nodes(node[2])

 def run_script(self, path):
        with open(path) as f:
            text = f.read()
        text = re.sub(r";\s*(then|do)\b", r"\n\1", text)
        nodes, _ = self.parse_block(text.splitlines(), 0, ())
        self.run_nodes(nodes)
        return self.last_status

 def setup_readline(self):
        if not readline:
            return
        try:
            readline.read_history_file(HISTORY_FILE)
            self.history = [readline.get_history_item(i)
                            for i in range(1, readline.get_current_history_length() + 1)]
        except OSError:
            pass
        words = BUILTINS + list(ALIASES)

        def complete(text, state):
            if readline.get_line_buffer().split()[:1] in ([], [text]):
                options = [w for w in words if w.startswith(text)]
            else:
                d, base = os.path.split(text)
                try:
                    options = [os.path.join(d, f) + ("/" if os.path.isdir(os.path.join(d or ".", f)) else "")
                               for f in os.listdir(d or ".") if f.startswith(base)]
                except OSError:
                    options = []
            return options[state] if state < len(options) else None

        readline.set_completer(complete)
        readline.set_completer_delims(" \t")
        readline.parse_and_bind("bind ^I rl_complete" if "libedit" in (readline.__doc__ or "") else "tab: complete")

    def save_history(self):
        if readline:
            try:
                readline.write_history_file(HISTORY_FILE)
            except OSError:
                pass

    def load_rc(self):
        if os.path.exists(RC_FILE):
            with open(RC_FILE) as f:
                for line in f:
                    self.run_line(line)

   def repl(self):
        self.setup_readline()
        self.load_rc()
        while True:
             try:
                 line = input("opsh> ")
             except KeyboardInterrupt:
                print()
                continue
             except EOFError:
                 print()
                  break
             if line.strip():
                self.history.append(line)
             self.run_line(line)
           self.save_history()

   def main():
       shell = Opsh()
       if len(sys.argv) > 1:
           sys.exit(shell.run_script(sys.argv[1]))
       shell.repl()


   if __name__ == "__main__":
    main()
