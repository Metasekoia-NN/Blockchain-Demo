class ansi:
    FAIL = '\033[91m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    OKBLUE = '\033[94m'
    OKPINK = '\033[95m'
    OKCYAN = '\033[96m'


    ENDC = '\033[0m'
    BOLD = '\033[1m'

def debug_info(func_name, content):
    print('{}{} -> {}{}'.format(ansi.OKBLUE, func_name, content, ansi.ENDC))

def debug_error(func_name, content):
    print('{}{} -> {}{}'.format(ansi.FAIL, func_name, content, ansi.ENDC))

def debug_warning(func_name, content):
    print('{}{} -> {}{}'.format(ansi.WARNING, func_name, content, ansi.ENDC))
