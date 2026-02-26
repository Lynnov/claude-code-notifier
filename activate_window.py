"""
Claude Code Notifier - Window Activator
Invoked by Windows when user clicks a toast notification.
Usage: pythonw.exe activate_window.py "claude-code-notifier://activate?pid=12345"
"""
import sys
import ctypes
import ctypes.wintypes
from urllib.parse import urlparse, parse_qs


def find_window_by_pid(target_pid):
    """Find the main visible window belonging to a given PID."""
    user32 = ctypes.windll.user32
    result = []

    WNDENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM
    )

    def enum_callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == target_pid and user32.GetWindowTextLengthW(hwnd) > 0:
            result.append(hwnd)
        return True

    user32.EnumWindows(WNDENUMPROC(enum_callback), 0)
    return result[0] if result else None


def activate_window(hwnd):
    """Bring a window to the foreground."""
    user32 = ctypes.windll.user32
    SW_RESTORE = 9

    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)

    user32.SetForegroundWindow(hwnd)


def main():
    if len(sys.argv) < 2:
        return

    parsed = urlparse(sys.argv[1])
    params = parse_qs(parsed.query)
    pid_str = params.get("pid", [None])[0]
    if not pid_str:
        return

    try:
        pid = int(pid_str)
    except ValueError:
        return

    # Check if process is still alive
    kernel32 = ctypes.windll.kernel32
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return
    kernel32.CloseHandle(handle)

    hwnd = find_window_by_pid(pid)
    if hwnd:
        activate_window(hwnd)


if __name__ == "__main__":
    main()
