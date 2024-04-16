import cv2 as cv
import numpy as np
from hsvfilter import HsvFilter

class Vision:
    # constant 
    TRACKBAR_WINDOW = "Trackbars"
    
    def __init__(self, target_image_path, method = cv.TM_CCOEFF_NORMED):
        self.target = cv.imread(target_image_path, cv.IMREAD_UNCHANGED) #haystack image
        
        #get dimensions of the target(palladium) image
        self.palladium_w = self.target.shape[0]
        self.palladium_h = self.target.shape[1]
        self.method = method

    def find(self, scene, threshold = .5):
        result = cv.matchTemplate(self.target, scene, self.method)

        locations = np.where(result >= threshold)
        locations = list(zip(*locations[::-1]))

        #creating the list of [x, y, w, h] rectangles
        rectangles = []
        for loc in locations:
            rect = [int(loc[0]), int(loc[1]), self.palladium_w, self.palladium_h]
            rectangles.append(rect)
            rectangles.append(rect)
            
        rectangles, weights = cv.groupRectangles(rectangles, 1, 0.5)
        #print(rectangles)
        
        return rectangles
    def get_click_positions(self, rectangles):
        
        #get best match positoin
        points = []
        for (x, y, w, h) in rectangles:
            center_x = int(x + w / 2) 
            center_y = int(y + h / 2)
                
            points.append((center_x, center_y))
            
        return points
        
    def draw_rectangles(self, scene, rectangles):
        for (x, y, w, h) in rectangles:
            top_left = (x, y)
            bottom_right = (x + w, y + h)
            
            cv.rectangle(scene, top_left, bottom_right, color=(0, 255, 0), thickness=2, lineType=cv.LINE_4)
        
        return scene
    
    def draw_cross(self, scene, points):
        marker_type =  cv.MARKER_CROSS
        marker_color = (0, 255, 0)
        for (center_x, center_y) in points:
                
            cv.drawMarker(scene, (center_x, center_y), marker_color, marker_type)
            
        return scene
    
    def init_control_gui(self):
        cv.namedWindow(self.TRACKBAR_WINDOW, cv.WINDOW_NORMAL)
        cv.resizeWindow(self.TRACKBAR_WINDOW, 350, 700)
        
        def nothing():
            pass
        
        cv.createTrackbar('HMin', self.TRACKBAR_WINDOW, 0, 179, nothing)
        cv.createTrackbar('SMin', self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv.createTrackbar('VMin', self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv.createTrackbar('HMax', self.TRACKBAR_WINDOW, 0, 179, nothing)
        cv.createTrackbar('SMax', self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv.createTrackbar('VMax', self.TRACKBAR_WINDOW, 0, 255, nothing)
        
        cv.setTrackbarPos('HMax', self.TRACKBAR_WINDOW, 179)
        cv.setTrackbarPos('SMax', self.TRACKBAR_WINDOW, 255)
        cv.setTrackbarPos('VMax', self.TRACKBAR_WINDOW, 255)
        
        cv.createTrackbar('SAdd', self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv.createTrackbar('SSub', self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv.createTrackbar('VAdd', self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv.createTrackbar('VSub', self.TRACKBAR_WINDOW, 0, 255, nothing)
    
    def get_hsl_filter_from_controlls(self):
        hsl_filter = HsvFilter()
        hsl_filter.hMin = cv.getTrackbarPos('HMin', self.TRACKBAR_WINDOW)
        hsl_filter.sMin = cv.getTrackbarPos('SMin', self.TRACKBAR_WINDOW)
        hsl_filter.vMin = cv.getTrackbarPos('VMin', self.TRACKBAR_WINDOW)
        hsl_filter.hMax = cv.getTrackbarPos('HMax', self.TRACKBAR_WINDOW)
        hsl_filter.sMax = cv.getTrackbarPos('SMax', self.TRACKBAR_WINDOW)
        hsl_filter.vMax = cv.getTrackbarPos('VMax', self.TRACKBAR_WINDOW)
        hsl_filter.sAdd = cv.getTrackbarPos('SAdd', self.TRACKBAR_WINDOW)
        hsl_filter.sSub = cv.getTrackbarPos('SSub', self.TRACKBAR_WINDOW)
        hsl_filter.vAdd = cv.getTrackbarPos('VAdd', self.TRACKBAR_WINDOW)
        hsl_filter.vSub = cv.getTrackbarPos('VSub', self.TRACKBAR_WINDOW)
        return hsl_filter
    
    def aply_hsl_filter(self, ooriginal_image, hsv_filter = None):
        hsv = cv.cvtColor(ooriginal_image, cv.COLOR_BGR2HSV)
        
        if not hsv_filter:
            hsv_filter = self.get_hsl_filter_from_controlls()
            
        h, s, v = cv.split(hsv)
        s = self.shift_chanel(s, hsv_filter.sAdd)
        s = self.shift_chanel(s, -hsv_filter.sSub)
        v = self.shift_chanel(v, hsv_filter.vAdd)
        v = self.shift_chanel(v, -hsv_filter.vSub)
        hsv = cv.merge([h, s, v])
        
        lower = np.array([hsv_filter.hMin, hsv_filter.sMin, hsv_filter.vMin])
        upper = np.array([hsv_filter.hMax, hsv_filter.sMax, hsv_filter.vMax])
        
        mask = cv.inRange(hsv, lower, upper)
        result = cv.bitwise_and(hsv, hsv, mask=mask)
        
        img = cv.cvtColor(result, cv.COLOR_HSV2BGR)

        return img

    def shift_chanel(self, c, amount):
        if amount > 0:
            lim = 255 - amount
            c[c >= lim] = 255
            c[c < lim] += amount
        elif amount < 0:
            amount = -amount
            lim = amount
            c[c <= lim] = 0
            c[c > lim ] -= amount
        return c
            