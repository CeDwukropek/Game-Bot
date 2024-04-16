import pyautogui
import cv2 as cv
import os
from threading import Thread
from time import time, sleep

from windowcapture import WindowCapture
from vision import Vision
from hsvfilter import HsvFilter
from detection import Detection
from bot import AlbionBot, BotState

os.chdir(os.path.dirname(os.path.abspath(__file__)))

wincap = WindowCapture('Dark Orbit')

vision_limestone = Vision('target_processed.jpg')

bot = AlbionBot((wincap.offset_x, wincap.offset_y), (wincap.w, wincap.h))

detector = Detection(vision_limestone)

hsv = HsvFilter(98, 67, 37, 179, 255, 255, 0, 0, 0, 0)

is_bot_in_action = False

def bot_actions(rectangles):
    if len(rectangles) > 0 :
        targets = vision_limestone.get_click_positions(rectangles)
        target = wincap.get_screen_position(targets[0])
        pyautogui.moveTo(x = target[0], y = target[1])
        pyautogui.click()
        sleep(1)
    
    global is_bot_in_action
    is_bot_in_action = False

wincap.start()
detector.start()
bot.start()

loop_time = time()
while True:
    if wincap.screenshot is None:
        continue
    
    # pre-proscess
    processed_image = vision_limestone.aply_hsl_filter(wincap.screenshot, hsv)
    
    # do object detection
    detector.update(processed_image)
    
    if bot.state == BotState.INITIALIZING:
        targets = vision_limestone.get_click_positions(detector.rectangles)
        bot.update_targets(targets)
    elif bot.state == BotState.SEARCHING:
        targets = vision_limestone.get_click_positions(detector.rectangles)
        bot.update_targets(targets)
        bot.update_screenshot(wincap.screenshot)
    elif bot.state == BotState.MOVING:
        bot.update_screenshot(wincap.screenshot)
    elif bot.state == BotState.MINING:
        pass
    
    # draw the detection result onto the original omage
    output_image = vision_limestone.draw_rectangles(wincap.screenshot, detector.rectangles)
    # display the processed image
    cv.imshow('Matches', output_image)
    
    if not is_bot_in_action:
        is_bot_in_action = True
        t = Thread(target=bot_actions, args = (detector.rectangles,))
        t.start()

    # print('FPS {}'.format(1 / (time() - loop_time)))
    loop_time = time()

    key = cv.waitKey(1)
    if key == ord('q'):
        wincap.stop()
        detector.stop()
        bot.stop()
        cv.destroyAllWindows()
        break

print('Done')