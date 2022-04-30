import logging
from dataclasses import dataclass
from time import sleep
from typing import List, Union

from PIL import Image
import cv2
import numpy as np

from vba import VBA


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
        left = int(130 * self.vba.scale)
        width = window.width - 2 * left
        options = self.vba.get_text(left, 0, width, window.height - self.vba.header.height - 20, "box.png")
        options = list(filter(None, [s.strip().lower() for s in options.split("\n")]))
        print(options)

        restart_idx: int = None
        restart_option: str = None
        for idx, option in enumerate(options):
            if "restart" in option:
                restart_idx = idx
                restart_option = option
        
        if restart_idx is None:
            logging.warning("At chapter menu and do not understand the options.")
            exit(1)

        logging.debug(f"Going to select option ({restart_idx}) {restart_option}")
        cursor_down = restart_idx + 1 # we are on last option, so + 1
        list([self.vba.ctl_down() for i in range(cursor_down)])

        self.vba.ctl_a() # Click "Restart Chapter"

        chapter_tite: str = self.vba.get_text(70 * self.vba.scale, 85 * self.vba.scale, 360 * self.vba.scale, 40 * self.vba.scale, "chapter_name.png")
        logging.info(f"Detected chapter: {chapter_tite}")

        self.vba.ctl_a() # start chapter

        chapter_suspend: str = self.vba.get_text(110 * self.vba.scale, 115 * self.vba.scale, 270 * self.vba.scale, 85 * self.vba.scale, "chapter_suspend.png")
        chapter_suspend = chapter_suspend.replace("\n", " ").strip().lower()
        if "suspended data will be lost" in chapter_suspend:
            logging.debug(f"Suspended chapter data already exists, choosing to delete previous data. msg: {chapter_suspend}")
            self.vba.ctl_left() # move cursor to "Start"
            self.vba.ctl_a() # select "Start"

        return chapter_tite

    def setup_chapter(self) -> None:
        sleep(10) # wait for chapter intro animation
        logging.debug("Skipping chapter start dialog.")
        self.vba.ctl_start() # skip chapter dialog
        sleep(5)

        while self.is_dialog_on_screen():
            logging.debug(f"Detected character dialog, trying to skip.")
            self.vba.ctl_start()
            sleep(3) # wait for dialog to stream to screen, not instant
        
        logging.debug(f"Reached combat start!")

    def is_dialog_on_screen(self) -> bool:
        image: Image = self.vba.screenshot_window("dialog.png")
        image = image.convert('RGB')
        image_arr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR) # convert PIL image to openCV
        #image_arr = cv2.cvtColor(image_arr, cv2.COLOR_BGR2GRAY) # grayscale
        #cv2.imwrite(f"edited-dialog.png", image_arr)

        template = cv2.imread('images/dialog_cursor.png')
        #template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY) # grayscale
        #cv2.imwrite(f"template-dialog.png", template)

        match_arr = cv2.matchTemplate(image_arr, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match_arr)
        #print(min_val, max_val, min_loc, max_loc)
        #w, h = template.shape[:-1]
        #bottom_right = (max_loc[0] + w, max_loc[1] + h)
        #img = cv2.rectangle(image_arr, max_loc, bottom_right, 255, 2)
        #cv2.imwrite(f"match-dialog.png", img)

        if max_val > 0.8:
            return True
        return False
