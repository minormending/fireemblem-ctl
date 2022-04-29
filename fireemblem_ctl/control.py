from collections import namedtuple
import logging
from string import punctuation
import subprocess
from dataclasses import dataclass
from time import sleep
from typing import List, Union
from unittest import result

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
        print(pytesseract.image_to_string(image).strip())

        image_arr = np.array(image)
        #image = image.convert("L") # grayscale
        cv2.imwrite("gray0-" + image_name, image_arr)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        cv2.imwrite("gray1-" + image_name, image)
        print(pytesseract.image_to_string(image).strip())
        #thresh = cv2.threshold(image,105, 255, cv2.THRESH_BINARY_INV)[1]
        #cv2.imwrite("gray2-" + image_name, image)
        #print(pytesseract.image_to_string(thresh).strip())
        #thresh = 255 - thresh

        #kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
        #result = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

        result = cv2.threshold(image, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY_INV)[1]

        #image = cv2.bitwise_not(image)
        #image = cv2.Canny(image, threshold1=400, threshold2=410)
        cv2.imwrite("gray-" + image_name, result)
        return pytesseract.image_to_string(result).strip()

    def screenshot_window(self, image_name: str = None) -> Image:
        window: Window = self._find_window()
        return self.screenshot(0, 0, window.width, window.height - self.header.height, image_name)

    def disable_layers(self) -> None:
        pyautogui.hotkey("ctrl", "1") # 
        # pyautogui.hotkey("ctrl", "2") # needed for chapter reset Start/Quit
        pyautogui.hotkey("ctrl", "3") # 
        pyautogui.hotkey("ctrl", "4") # 

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

    def ctl_a(self, delay: float = 1.0) -> None:
        pydirectinput.press("z")
        sleep(delay)
        
    def ctl_b(self, delay: float = 1.0) -> None:
        pydirectinput.press("x")
        sleep(delay)


@dataclass
class FireEmblem:
    vba: VBA = None

    def go_to_chapter_options(self) -> None:
        self.vba.ctl_start(delay=2) # skip intro movie
        logging.debug("Skipped intro movie.")
        self.vba.ctl_start(delay=2) # go to menu
        logging.debug("Clicked through to the chapter options.")
        self.vba.ctl_up(delay=1) # ocr for highlighted option is bad.

    def restart_chapter(self) -> str:
        logging.debug("Going to OCR chapter options.")

        window = self.vba._find_window()
        left = int(130 * vba.scale)
        width = window.width - 2 * left
        options = self.vba.get_text(left, 0, width, window.height - vba.header.height - 20, "box.png")
        options = list(filter(None, [s.strip().lower() for s in options.split("\n")]))
        print(options)

        restart_idx: int = None
        restart_option: str = None
        for idx, option in enumerate(options):
            if "restart" in option:
                restart_idx = idx
                restart_option = option
        
        if restart_idx is None:
            logging.warn("At chapter menu and do not understand the options.")
            exit(1)

        logging.debug(f"Going to select option ({restart_idx}) {restart_option}")
        cursor_down = restart_idx + 1 # we are on last option, so + 1
        list([self.vba.ctl_down() for i in range(cursor_down)])

        self.vba.ctl_a() # Click restart chapter

        chapter_tite: str = self.vba.get_text(70 * self.vba.scale, 80 * self.vba.scale, 360 * self.vba.scale, 40 * self.vba.scale, "chapter_name.png")
        logging.info(f"Detected chapter: {chapter_tite}")

        self.vba.send_keys("z") # start chapter


        return chapter_tite


logging.basicConfig(level=logging.DEBUG)

image_name = "box.png"
image = cv2.imread("box.png")
print("unedited:", pytesseract.image_to_string(image).strip())

#print(image.shape)
#image = image[:,:,0]
#cv2.imwrite("gray0-" + image_name, image)
#print("blue:", pytesseract.image_to_string(image).strip())

image = cv2.bitwise_not(image)
cv2.imwrite("inverted-" + image_name, image)
print("inverted:", pytesseract.image_to_string(image).strip())


image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
cv2.imwrite("gray-" + image_name, image)
print("grayscale:", pytesseract.image_to_string(image).strip())


#cv2.imwrite("gray1-" + image_name, image)
#print(pytesseract.image_to_string(image).strip())
#thresh = cv2.threshold(image,105, 255, cv2.THRESH_BINARY_INV)[1]
#cv2.imwrite("gray2-" + image_name, image)
#print(pytesseract.image_to_string(thresh).strip())
#thresh = 255 - thresh

#kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
#result = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

image = cv2.threshold(image, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY_INV)[1]
print("stuff:", pytesseract.image_to_string(image).strip())

exit(0)

with VBA("tools\VisualBoyAdvance.exe", "tools\Fire Emblem (U).gba") as vba:
    vba.disable_layers()
    vba.reset_game()

    fe = FireEmblem(vba)
    fe.go_to_chapter_options()
    chapter_title: str = fe.restart_chapter()


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
