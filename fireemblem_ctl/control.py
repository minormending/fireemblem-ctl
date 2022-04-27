from collections import namedtuple
import logging
import subprocess
from dataclasses import dataclass
from time import sleep
from typing import List, Union

from pyautogui import Window
from PIL import Image
import pyautogui

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
        window.resizeTo(496, 379)
        return window

    def send_keys(self, keys: Union[str, List[str]], delay: float = 1.0) -> None:
        """Duplicates pyautogui.press() because VBA does not recognize press() keys."""
        #window: Window = self._find_window() # ensure window is at the correct location
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
        image = image.convert("L") # grayscale
        return pytesseract.image_to_string(image).strip()

    def screenshot_window(self, image_name: str = None) -> Image:
        window: Window = self._find_window()
        return self.screenshot(0, 0, window.width, window.height - self.header.height, image_name)


logging.basicConfig(level=logging.DEBUG)
with VBA("tools\VisualBoyAdvance.exe", "tools\Fire Emblem (U).gba") as vba:
    pyautogui.hotkey("ctrl", "1") # 
    pyautogui.hotkey("ctrl", "2") # 
    pyautogui.hotkey("ctrl", "3") # 
    pyautogui.hotkey("ctrl", "4") # 
    pyautogui.hotkey("ctrl", "r", interval=1.0) # reset game
    vba.send_keys(["enter", "enter"]) # go to chapter menu

    #sleep(1)
    vba.send_keys(["down", "down", "down"]) # ocr for highlighted option is bad.
    #pyautogui.press("up")
    #restart_loc = pyautogui.locate('images/restart_chapter.png', vba.screenshot_window("window.png"), grayscale=True)
    #print(restart_loc)
    options = vba.get_text(130, 0, 230, 350, "box.png")
    options = list(filter(None, [s.strip() for s in options.split("\n")]))
    print(options)
    #print(pytesseract.image_to_string(vba.screenshot_window("window.png").convert("L")).strip())
    sleep(3)
    exit(1)

    text: str = vba.get_text(130, 30, 230, 38, "restart.png")
    if "restart chapter" not in text.lower():
        logging.warn("At chapter menu and do not understand the options.")
        exit(1)

    vba.send_keys("z") # select "Restart Chapter"

    chapter_tite: str = vba.get_text(75, 75, 350, 40, "chapter_name.png")
    logging.info(f"Detected chapter: {chapter_tite}")

    vba.send_keys("z") # start chapter
    sleep(5) # wait for chapter intro animation
    vba.send_keys("enter") # skip dialog

    while True:
        dialog_loc = pyautogui.locate('images/dialog_cursor.png', vba.screenshot_window(), grayscale=True)
        if dialog_loc:
            logging.debug(f"Detected character dialog, trying to skip.")
            vba.send_keys("enter")
            sleep(2) # wait for dialog to stream to screen, not instant
        else:
            logging.debug(f"Did NOT find character dialog, finished!")
            break

    image = vba.screenshot_window("window.png")
    #print(pytesseract.image_to_string(image.convert("L")).strip())


    sleep(3)
