"""
This fixes an issue using Rich's Console.input() method, where the prompt
is deleted if a backspace is typed. The problematic method in the base
Console class is overridden.

Bug:
  https://github.com/Textualize/rich/issues/2293

The fix is extracted from the commit that introduces the bug:
  https://github.com/Textualize/rich/commit/568b9517b63282ac781a907d82b0c2965242be54
"""

from typing import Optional, TextIO

try:
    import readline
except ImportError:
    pass

from getpass import getpass

from rich.console import Console
from rich.text import TextType


class ConsoleWithInputBackspaceFixed(Console):

    def input(
        self,
        prompt: TextType = "",
        *,
        markup: bool = True,
        emoji: bool = True,
        password: bool = False,
        stream: Optional[TextIO] = None,
    ) -> str:
        prompt_str = ""
        if prompt:
            with self.capture() as capture:
                self.print(prompt, markup=markup, emoji=emoji, end="")
            prompt_str = capture.get()
        if self.legacy_windows:
            self.file.write(prompt_str)
            prompt_str = ""
        if password:
            result = getpass(prompt_str, stream=stream)
        else:
            if stream:
                self.file.write(prompt_str)
                result = stream.readline()
            else:
                result = input(prompt_str)
        return result
