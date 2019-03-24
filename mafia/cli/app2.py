"""Alternative CLI app (non-fullscreen).

Far from being implemented.
"""

import sys
from prompt_toolkit import (
    PromptSession, print_formatted_text as print, 
)
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator


class CliApp(object):
    """"""

    def __init__(self):
        pass

    def main(self, args=None):
        """Main loop."""
        if args is None:
            args = sys.argv[1:]

        options = ['quit']

        p = PromptSession(
            message="\n" "> ",
            completer=WordCompleter(options),            
            validator=Validator.from_callable(lambda x: x in options),
        )

        while True:
            try:
                print(options)
                r = p.prompt()
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            else:
                if r == 'quit':
                    return
                else:
                    print(r)


if __name__ == "__main__":
    app = CliApp()
    app.main()
