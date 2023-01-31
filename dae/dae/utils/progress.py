import sys


def progress(text=".", verbose=1):
    if verbose:
        sys.stderr.write(text)


def progress_nl(verbose=1):
    if verbose:
        sys.stderr.write("\n")


RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[1;34m"
CYAN = "\033[1;36m"
RESET = "\033[0;0m"
BOLD = "\033[;1m"
REVERSE = "\033[;7m"


def red_print(message):
    sys.stdout.write(RED)
    sys.stdout.write(message)
    sys.stdout.write(RESET)
    sys.stdout.write("\n")
