

r"""


C:\analytics\projects\git\lexi\demos\venv\Scripts\python.exe

import runpy ; temp = runpy._run_module_as_main("jnkaa")


"""


import re
import sys
import win32clipboard
from markdownify import markdownify as md


def get_clipboard_html():
    win32clipboard.OpenClipboard()
    try:
        data = win32clipboard.GetClipboardData(win32clipboard.RegisterClipboardFormat("HTML Format"))
    finally:
        win32clipboard.CloseClipboard()

    text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data

    start_match = re.search(r"StartHTML:(\d+)", text)
    end_match = re.search(r"EndHTML:(\d+)", text)

    if not start_match or not end_match:
        return text

    start = int(start_match.group(1))
    end = int(end_match.group(1))
    return text[start:end]


def main():
    html = get_clipboard_html()
    markdown = md(html, heading_style="ATX")
    sys.stdout.write(markdown)


if __name__ == "__main__":
    main()