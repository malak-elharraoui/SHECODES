#!/usr/bin/env python3
import sys


def repl():
    while True:
        try:
            line = input("opsh> ")
        except EOFError:
            print()
            break
        if line.strip() == "quit":
            break
        if line.strip():
            print("tu as tapé :", line)


if __name__ == "__main__":
    repl()
