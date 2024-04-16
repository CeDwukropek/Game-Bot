import cv2 as cv
import pyautogui
import math
from time import sleep, time
from threading import Thread, Lock


class BotState:
    INITIALIZING = 0;
    SEARCHING = 1;
    MOVING = 2
    MINING = 3
    BACKTRACKING = 4
    
class AlbionBot:
    INITIALIZING_SECONDS = 3
    MINIG_SECONDS = 1.5
    MOVEMENT_STOPPED_THRESHOLD = .975
    IGNORE_RADIUS = 10
    
    stopped = True
    lock = None
    
    state = None
    targets = []
    screenshot = None
    timestamp = None
    movement_screenshot = None
    window_offset = (0, 0)
    window_w = 0
    window_h = 0
    click_history = []
    
    def __init__(self, window_offset, window_size):
        self.lock = Lock()
        
        self.state = BotState.INITIALIZING
        self.timestamp = time()
        
        self.window_offset = window_offset
        self.window_w = window_size[0]
        self.window_h = window_size[1]
    
    def click_next_target(self):
        target = self.targets_ordered_by_distance(self.targets)
        
        found_palladium = False
        while not found_palladium:
            if self.stopped:
                break
        
        target_pos = target
        screen_x, screen_y = self.get_screen_position(target_pos)
        
        print('Moving mouse to x:{} y:{}'.format(screen_x, screen_y))
        
        found_palladium = True
        pyautogui.moveTo(x=screen_x, y=screen_y)
        pyautogui.cick()
        self.click_history.append(target_pos)
        
        return found_palladium
    
    def click_backtrack(self):
        last_click = self.click_history.pop()
        
        my_pos = (self.window_w / 2, self.window_h / 2)
        mirrored_click_x = my_pos[0] - (last_click[0] - my_pos[0])
        mirrored_click_y = my_pos[1] - (last_click[1] - my_pos[1])
        
        screen_x, screen_y = self.get_screen_position((mirrored_click_x, mirrored_click_y))
        print('Backtracking to x:{} y:{}'.format(screen_x, screen_y))
        pyautogui.moveTo(x=screen_x, y=screen_y)
        
        sleep(.05)
        pyautogui.click()
    
    def have_stopped_moving(self):
        if self.movement_screenshot is None:
            self.movement_screenshot = self.screenshot.copy()
            return False
        
        result = cv.matchTemplate(self.screenshot, self.movement_screenshot, cv.TM_CCOEFF_NORMED)
        similarity = result[0][0]
        print('Movement detection similarity: {}'.format(similarity))
        
        if similarity >= self.MOVEMENT_STOPPED_THRESHOLD:
            print('Movement detected stop')
            return True
    
    def targets_ordered_by_distance(self, targets):
        my_pos = (self.window_w / 2, self.window_h / 2)
        
        def pythagorean_distance(pos):
            return math.sqrt((pos[0] - my_pos[0])**2 + (pos[1] - my_pos[1])**2)
        targets = [t for t in targets if pythagorean_distance(t) > self.IGNORE_RADIUS]
        
        return targets[0]
    
    def get_screen_position(self, pos):
        return(pos[0] + self.window_offset[0], pos[1] + self.window_offset[1])
    
    def update_targets(self, targets):
        self.lock.acquire()
        self.targets = targets
        self.lock.release()
        
    def update_screenshot(self, screenshot):
        self.lock.acquire()
        self.screenshot = screenshot
        self.lock.release()
        
    def start(self):
        self.stopped = False
        t = Thread(target=self.run)
        t.start()
        
    def stop(self):
        self.stopped = True
        
    
    def run(self):
        while not self.stopped:
            if self.state == BotState.INITIALIZING:
                if time() > self.timestamp + self.INITIALIZING_SECONDS:
                    self.lock.acquire()
                    self.state = BotState.SEARCHING
                    self.lock.release()
                    
                elif self.state == BotState.SEARCHING:
                    
                    success = self.click_next_target()
                    
                    if not success:
                        success = self.click_next_target()
                    
                    if success:
                        self.lock.acquire()
                        self.state = BotState.SEARCHING
                        self.lock.release()
                    elif len(self.click_history) > 0:
                        self.click_backtrack()
                        self.lock.acquire()
                        self.state = BotState.BACKTRACKING
                        self.lock.release()
                    else:
                        pass
                
                elif self.state == BotState.MOVING:
                    if not self.have_stopped_moving():
                        sleep(1)
                    else:
                        self.lock.acquire()
                        self.timestamp = time()
                        self.state = BotState.MINING
                        self.lock.release()
                elif self.state == BotState.MINING:
                    if time() > self.timestamp + self.MINIG_SECONDS:
                        self.lock.acquire()
                        self.state = BotState.SEARCHING
                        self.lock.release()