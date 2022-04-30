from collections import namedtuple
import logging
import subprocess
from dataclasses import dataclass
from time import sleep
from typing import List, Union

from pyautogui import Window
from PIL import Image
import pyautogui
import pydirectinput
import cv2
import numpy as np
import pytesseract


@dataclass
class VBA:
    EXECUTABLE: str = None
    game: str = None

    def __init__(self, exe, game) -> None:
        self.EXECUTABLE, self.game = exe, game
        self._process: subprocess.Popen = None

        VBAHeaderSize = namedtuple("VBAHeaderSize", "width height")
        self.header: 'VBAHeaderSize' = VBAHeaderSize(496, 50)

    def __enter__(self) -> 'VBA':
        self._process = subprocess.Popen([self.EXECUTABLE, self.game],stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        sleep(1)
        self._find_window() # normalize window size and position
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        self._process.terminate()

    def _find_window(self) -> Window:
        window: Window = next(filter(lambda w: "VisualBoyAdvance" in w.title, pyautogui.getAllWindows()))
        window.activate()
        window.moveTo(5, 50)
        #window.resizeTo(496, 379)
        self.scale = 2
        window.resizeTo(int(496 * self.scale), int(379 * self.scale))
        return window

    def send_keys(self, keys: Union[str, List[str]], delay: float = 1.0) -> None:
        """Duplicates pyautogui.press() because VBA does not recognize press() keys."""
        window: Window = self._find_window() # ensure window is at the correct location
        keys = [keys] if isinstance(keys, str) else keys
        for key in keys:
            print("sending:", key)
            pyautogui.keyDown(key)
            sleep(0.5)
            pyautogui.keyUp(key)
            sleep(delay)

    def screenshot(self, left: int, top: int, width: int, height: int, image_name: str = None) -> Image:
        window: Window = self._find_window()
        region = (window.left + left, window.top + self.header.height + top, width, height)
        return pyautogui.screenshot(image_name, region=region)

    def get_text(self, left: int, top: int, width: int, height: int, image_name: str = None) -> str:
        image: Image = self.screenshot(left, top, width, height, image_name)
        unedited_text: str = pytesseract.image_to_string(image).strip()

        image = image.convert('RGB')
        image_arr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR) # convert PIL image to openCV
        image_arr = cv2.bitwise_not(image_arr) # change text from white to black
        image_arr = cv2.cvtColor(image_arr, cv2.COLOR_BGR2GRAY) # grayscale
        cv2.imwrite(f"edited-{image_name}", image_arr)
        edited_text: str = pytesseract.image_to_string(image_arr).strip()

        if not edited_text and unedited_text:
            return unedited_text
        return edited_text

    def screenshot_window(self, image_name: str = None) -> Image:
        window: Window = self._find_window()
        return self.screenshot(0, 0, window.width, window.height - self.header.height, image_name)

    def disable_layers(self) -> None:
        #pyautogui.hotkey("ctrl", "1") # 
        # pyautogui.hotkey("ctrl", "2") # needed for chapter reset Start/Quit
        #pyautogui.hotkey("ctrl", "3") # 
        #pyautogui.hotkey("ctrl", "4") # 
        pass

    def reset_game(self) -> None:
        pyautogui.hotkey("ctrl", "r", interval=1.0)

    def ctl_start(self, delay: float = 1.0) -> None:
        pydirectinput.press("enter")
        sleep(delay)

    def ctl_up(self, delay: float = 1.0) -> None:
        pydirectinput.press("w")
        sleep(delay)
        
    def ctl_down(self, delay: float = 1.0) -> None:
        pydirectinput.press("s")
        sleep(delay)
        
    def ctl_left(self, delay: float = 1.0) -> None:
        pydirectinput.press("a")
        sleep(delay)
        
    def ctl_right(self, delay: float = 1.0) -> None:
        pydirectinput.press("d")
        sleep(delay)

    def ctl_a(self, delay: float = 1.0) -> None:
        pydirectinput.press("z")
        sleep(delay)
        
    def ctl_b(self, delay: float = 1.0) -> None:
        pydirectinput.press("x")
        sleep(delay)

