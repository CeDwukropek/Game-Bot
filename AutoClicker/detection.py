import cv2 as cv
from threading import Thread, Lock

class Detection:
    # threading properties
    stopped = True
    lock = None
    rectangles = []
    # properties
    vision = None
    screenshot = None
    
    def __init__(self, vision):
        self.lock = Lock()
        self.vision = vision
    
    def update(self, screenshot):
        self.lock.acquire()
        self.screenshot = screenshot
        self.lock.release()
    
    def start(self):
        self.stopped = False
        t = Thread(target = self.run)
        t.start()
        
    def stop(self):
        self.stopped = True
        
    def run(self):
        # TODO 
        while not self.stopped:
            if not self.screenshot is None:
                rectangles = self.vision.find(self.screenshot, .5)
                
                self.lock.acquire()
                self.rectangles = rectangles
                self.lock.release()