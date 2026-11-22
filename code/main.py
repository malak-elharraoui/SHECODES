
#!/usr/bin/env python3
import os
import shlex
import signal
import sys

ALIASES = {
    "list": "ls", "show": "cat", "copy": "cp", "move": "mv",
    "del": "rm", "newdir": "mkdir", "newfile": "touch",
}
BUILTINS = ["go", "quit", "path", "say", "info", "past", "osinfo"]


class Opsh:
    def __init__(self):
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
                    done, _ = os.waitpid(pid, os.WNOHANG)
                except ChildProcessError:
                    done = pid
                if done != pid:
                    alive.append(pid)
            if alive:
                self.jobs[num] = (alive, cmd)
            else:
                print(f"\n[{num}]+ Done {cmd}")
                del self.jobs[num]

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
        lex = shlex.shlex(text, posix=True, punctuation_chars="<>&")
        lex.whitespace_split = True
        tokens = list(lex)
        argv, infile, outfile, append,bg = [], None, None, False, False
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
        return 0


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
  
   def repl(self):
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
   def main():
    shell = Opsh()
    shell.repl()

   if __name__ == "__main__":
    main()
