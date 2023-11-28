"""pywwb - Windows Without Borders

Script-friendly tool for forcing matching windows into
borderless-fullscreen mode.
"""

import re
import sys
from argparse import ArgumentParser

import win32api as api
import win32con as con
import win32gui as gui

# work on cmdline by specifying window params to look up, e.g. window title, cmdline, process name, etc
#   - works on demand or in "watch" mode, waiting for the appearance of a matching window/proces
#
# alternatively, act as a wrapper to an executable, passing all given arguments to the wrapped exe,
# waiting for it to spawn a window (can specify criteria somehow), then making it borderless

# NOTE: Even though game windows (to my knowledge) have no child windows, most
#       borderless-fullscreen implementations set WS_CLIPCHILDREN anyway.
#       The "POPUP" style is the important bit here.
BORDERLESS_STYLE = con.WS_VISIBLE | con.WS_POPUP | con.WS_CLIPCHILDREN


def get_windows(patterns: list[re.Pattern], all_matches: bool = False) -> list[int]:
    """Get any window handles that match the given pattern(s)."""
    windows = []

    def _callback(hwnd, ctx):
        if gui.IsWindowVisible(hwnd):
            title = gui.GetWindowText(hwnd)
            if any(pattern.search(title) for pattern in patterns):
                windows.append(hwnd)
                if not all_matches:
                    raise StopIteration

    try:
        gui.EnumWindows(_callback, None)
    except StopIteration:
        pass
    return windows


def get_monitor(hwnd) -> dict:
    return api.GetMonitorInfo(api.MonitorFromWindow(hwnd, con.MONITOR_DEFAULTTONEAREST))


# TODO: Find other things to strip, like maybe status bars and/or scrollbars
def strip_decorations(hwnd):
    """Remove additional window decorations.

    Typically not necessary, but might be useful when making more exotic
    and/or non-game windows fullscreen. Removes things like the menu bar and
    anything else that might hang around after a fullscreening.
    """
    gui.SetMenu(hwnd, None)


def make_fullscreen(hwnd):
    """Make the target window borderless-fullscreen."""
    gui.SetWindowLong(hwnd, con.GWL_STYLE, BORDERLESS_STYLE)
    width, height = get_monitor(hwnd)["Monitor"][2:]
    gui.SetWindowPos(
        hwnd,
        con.HWND_TOP,
        0,
        0,
        width,
        height,
        con.SWP_FRAMECHANGED | con.SWP_SHOWWINDOW,
    )


def main(args) -> int:
    patterns = [re.compile(pat, re.I if args.case_insensitive else 0) for pat in args.patterns]
    matches = get_windows(patterns, args.all_matches)
    print(matches)
    for window in matches:
        make_fullscreen(window)

    return 0


# TODO: Add a switch that tries to limit pattern matches to game windows.
#       Some heuristics for this could be checking for DirectX, OpenGL, or
#       Vulkan. Could also check for steam DLLs, etc.
if __name__ == "__main__":
    parser = ArgumentParser(
        description=(
            "Windows Without Borders — Script-friendly tool for forcing matching windows into borderless fullscreen"
            " mode."
        ),
        allow_abbrev=False,
    )
    parser.add_argument(
        "patterns",
        nargs="+",
        metavar="pattern",
        help="One or more Python regular expressions to match against window titles",
    )
    parser.add_argument(
        "-a",
        "--all-matches",
        action="store_true",
        help="Select all matching windows instead of just the first",
    )
    parser.add_argument(
        "-i",
        "--case-insensitive",
        action="store_true",
        help="Make patterns implicitly case-insensitive",
    )
    # TODO: Implement this
    parser.add_argument(
        "-m",
        "--monitor",
        type=int,
        default=0,
        metavar="NUM",
        help=(
            "Move the window to a specific monitor; `1` is the primary monitor and `0` (default) is the monitor that"
            " the window is already on"
        ),
    )
    parser.add_argument(
        "-d",
        "--remove-decorations",
        action="store_true",
        help="Remove additional window decorations, e.g. menu bars",
    )
    sys.exit(main(parser.parse_args()))
