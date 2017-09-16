import pickle
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import glob

class Lane():
    def __init__(self):

        # parameters used for window sliding lane finding method
        self.margin = 80
        self.minpix = 50
        self.nwindows = 9
        #polynomial coefficients for the most recent fit
        self.left_fit = np.array([0.,0.,0.], dtype='float')
        self.right_fit = np.array([0.,0.,0.], dtype='float')
        # perspective transform matrix M and inverse of M
        self.M = None
        self.Minv = None
        # was the line detected in the last iteration?
        self.detected = False 

        # x values of the last n fits of the line
        self.recent_xfitted = [] 
        #average x values of the fitted line over the last n iterations
        self.bestx = None     
        #polynomial coefficients averaged over the last n iterations
        self.best_fit = None
        #radius of curvature of the line in some units
        self.radius_of_curvature = None 
        #distance in meters of vehicle center from the line
        self.line_base_pos = None 
        #difference in fit coefficients between last and new fits
        self.diffs = np.array([0,0,0], dtype='float') 
        #x values for detected line pixels
        self.allx = None  
        #y values for detected line pixels
        self.ally = None


    def initialLaneCalibration(self, binary_warped):
        """
        it reads the image, binary_warped, and finds the lane curves
        :param np.array bainary_warped : 2D-np.array of 0 and 1s
        return left_fit, right_fit, leftx, lefty, rightx, righty
        """
        nwindows = self.nwindows
        margin = self.margin
        minpix = self.minpix

        histogram = np.sum(binary_warped[int(binary_warped.shape[0]/2):,:], axis=0)
        # Create an output image to draw on and  visualize the result
        # out_img = np.dstack((binary_warped, binary_warped, binary_warped))*255
        # Find the peak of the left and right halves of the histogram
        # These will be the starting point for the left and right lines
        midpoint = np.int(histogram.shape[0]/2)
        leftx_base = np.argmax(histogram[:midpoint])
        rightx_base = np.argmax(histogram[midpoint:]) + midpoint

        # Set height of windows
        window_height = np.int(binary_warped.shape[0]/nwindows)
        # Identify the x and y positions of all nonzero pixels in the image
        nonzero = binary_warped.nonzero()
        nonzeroy = np.array(nonzero[0])
        nonzerox = np.array(nonzero[1])
        # Current positions to be updated for each window
        leftx_current = leftx_base
        rightx_current = rightx_base

        # Create empty lists to receive left and right lane pixel indices
        left_lane_inds = []
        right_lane_inds = []

        # Step through the windows one by one
        for window in range(nwindows):
            # Identify window boundaries in x and y (and right and left)
            win_y_low = binary_warped.shape[0] - (window+1)*window_height
            win_y_high = binary_warped.shape[0] - window*window_height
            win_xleft_low = leftx_current - margin
            win_xleft_high = leftx_current + margin
            win_xright_low = rightx_current - margin
            win_xright_high = rightx_current + margin

            # Identify the nonzero pixels in x and y within the window
            good_left_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) & 
            (nonzerox >= win_xleft_low) &  (nonzerox < win_xleft_high)).nonzero()[0]
            good_right_inds = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) & 
            (nonzerox >= win_xright_low) &  (nonzerox < win_xright_high)).nonzero()[0]
            # Append these indices to the lists
            left_lane_inds.append(good_left_inds)
            right_lane_inds.append(good_right_inds)
            # If you found > minpix pixels, recenter next window on their mean position
            if len(good_left_inds) > minpix:
                leftx_current = np.int(np.mean(nonzerox[good_left_inds]))
            if len(good_right_inds) > minpix:        
                rightx_current = np.int(np.mean(nonzerox[good_right_inds]))

        # Concatenate the arrays of indices
        left_lane_inds = np.concatenate(left_lane_inds)
        right_lane_inds = np.concatenate(right_lane_inds)

        # Extract left and right line pixel positions
        leftx = nonzerox[left_lane_inds]
        lefty = nonzeroy[left_lane_inds] 
        rightx = nonzerox[right_lane_inds]
        righty = nonzeroy[right_lane_inds] 

        # Fit a second order polynomial to each
        left_fit = np.polyfit(lefty, leftx, 2)
        right_fit = np.polyfit(righty, rightx, 2)

        return left_fit, right_fit, leftx, lefty, rightx, righty

    def updateLaneCalibration(self, binary_warped):
        """
        it reads the image, binary_warped, and finds the lane curves
        unlike initialize lane calibration, this function assums that
        lane.left_fit and right_fit are not None, i.e. already found
        :param np.array bainary_warped : 2D-np.array of 0 and 1s
        return left_fit, right_fit, leftx, lefty, rightx, righty
        """
        margin = self.margin
        left_fit = self.left_fit
        right_fit = self.right_fit

        if (left_fit is None) or (right_fit is None):
            raise ValueError('No initail values for left and/or right fit coefficients')

        nonzero = binary_warped.nonzero()
        nonzeroy = np.array(nonzero[0])
        nonzerox = np.array(nonzero[1])
        margin = 100
        left_lane_inds = ((nonzerox > (left_fit[0]*(nonzeroy**2) + left_fit[1]*nonzeroy + 
                        left_fit[2] - margin)) & (nonzerox < (left_fit[0]*(nonzeroy**2) + 
                        left_fit[1]*nonzeroy + left_fit[2] + margin))) 

        right_lane_inds = ((nonzerox > (right_fit[0]*(nonzeroy**2) + right_fit[1]*nonzeroy + 
                        right_fit[2] - margin)) & (nonzerox < (right_fit[0]*(nonzeroy**2) + 
                        right_fit[1]*nonzeroy + right_fit[2] + margin)))  

        # Again, extract left and right line pixel positions
        leftx = nonzerox[left_lane_inds]
        lefty = nonzeroy[left_lane_inds] 
        rightx = nonzerox[right_lane_inds]
        righty = nonzeroy[right_lane_inds]
        
        # Fit and update second order polynomial to each
        left_fit = np.polyfit(lefty, leftx, 2)
        right_fit = np.polyfit(righty, rightx, 2)

        return left_fit, right_fit, leftx, lefty, rightx, righty
    
    def LaneCalibration(self, binary_warped):
        """
        it reads the image, binary_warped, and finds the lane curves
        unlike initialize lane calibration, this function assums that
        lane.left_fit and right_fit are not None, i.e. already found
        :param np.array bainary_warped : 2D-np.array of 0 and 1s
        return left_fit, right_fit, leftx, lefty, rightx, righty
        """
        
        if (self.detected):
            left_fit, right_fit, leftx, lefty, rightx, righty = self.updateLaneCalibration(binary_warped)

        else:
            left_fit, right_fit, leftx, lefty, rightx, righty = self.initialLaneCalibration(binary_warped)

        self.diffs = np.vstack((left_fit - self.left_fit, 
                                right_fit - self.right_fit))
        # if diffs is too big, then do something
        self.detected = True
        self.left_fit = left_fit
        self.right_fit = right_fit
        self.allx = [leftx, rightx]
        self.ally = [lefty, righty]

    def computeCurvature(self):

        y_eval= max(self.ally)
        left_fit = self.left_fit
        right_fit = self.right_fit
        left_curvature = ((1 + (2*left_fit[0]*y_eval + left_fit[1])**2)**1.5) / np.absolute(2*left_fit[0])
        right_curvature = ((1 + (2*right_fit[0]*y_eval + right_fit[1])**2)**1.5) / np.absolute(2*right_fit[0])
        
        self.radius_of_curvature = [left_curvature, right_curvature]
        return

    def visualizeLane(self, binary_warped, original_img): 
        left_fit = self.left_fit
        right_fit = self.right_fit
        Minv = self.Minv

        warped = binary_warped
        image = original_img
        # Create an image to draw the lines on
        warp_zero = np.zeros_like(warped).astype(np.uint8)
        color_warp = np.dstack((warp_zero, warp_zero, warp_zero))
        
        # Generate x and y values for plotting
        ploty = np.linspace(0, binary_warped.shape[0]-1, binary_warped.shape[0])
        left_fitx = left_fit[0]*ploty**2 + left_fit[1]*ploty + left_fit[2]
        right_fitx = right_fit[0]*ploty**2 + right_fit[1]*ploty + right_fit[2]

        # Recast the x and y points into usable format for cv2.fillPoly()
        pts_left = np.array([np.transpose(np.vstack([left_fitx, ploty]))])
        pts_right = np.array([np.flipud(np.transpose(np.vstack([right_fitx, ploty])))])
        pts = np.hstack((pts_left, pts_right))

        # Draw the lane onto the warped blank image
        cv2.fillPoly(color_warp, np.int_([pts]), (0,255, 0))
        
        # TO DO: Draw the lanes in color, width 10 pixels

        # Warp the blank back to original image space using inverse perspective matrix (Minv)
        newwarp = cv2.warpPerspective(color_warp, Minv, (image.shape[1], image.shape[0])) 
        # Combine the result with the original image
        result = cv2.addWeighted(image, 1, newwarp, 0.3, 0)

        return result