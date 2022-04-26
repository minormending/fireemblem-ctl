
import subprocess
from dataclasses import dataclass
from time import sleep
import pyautogui


@dataclass
class VBA:
    EXECUTABLE: str = None
    game: str = None

    _process: subprocess.Popen = None

    def __enter__(self) -> 'VBA':
        self._process = subprocess.Popen([self.EXECUTABLE, self.game],stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        self._process.terminate()


    def _find_window(self) -> None:
        window = next(filter(lambda w: "VisualBoyAdvance" in w.title, pyautogui.getAllWindows()))
        print(window)
        #bounds = win32gui.GetWindowRect(window)
        #print(bounds)

    def send_keys(self, keys: str, delay: float = 0.5) -> None:
        for key in keys:
            print("sending key:", key)
            try:
                self._process.communicate(key.encode())
            except subprocess.TimeoutExpired:
                pass
            sleep(delay)


with VBA("tools\VisualBoyAdvance.exe", "tools\Fire Emblem (U).gba") as vba:
    print("in context")
    sleep(2)

    vba._find_window()
    #vba.send_keys("\n")
    #vba.send_keys("zz", 1)
    sleep(10)
