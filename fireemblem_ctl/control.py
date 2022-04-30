import logging
from time import sleep

from vba import VBA
from fireemblem import FireEmblem


logging.basicConfig(level=logging.DEBUG)

"""
image_name = "window.png"
image = cv2.imread(image_name)
print("unedited:", pytesseract.image_to_string(image).strip())
exit(0)
"""

with VBA("tools\VisualBoyAdvance.exe", "tools\Fire Emblem (U).gba") as vba:
    vba.disable_layers()
    vba.reset_game()

    fe = FireEmblem(vba)
    fe.go_to_chapter_options()
    chapter_title: str = fe.restart_chapter()
    fe.setup_chapter()

    image = vba.screenshot_window("window.png")
    sleep(3)
