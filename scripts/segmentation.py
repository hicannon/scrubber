#!/usr/bin/env python
import roslib
roslib.load_manifest('scrubber')
import sys
import rospy
import cv
import cv2
import numpy as np
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError

class Segment:

  def __init__(self):
    self.image_pub = rospy.Publisher("outpy",Image)

    cv2.namedWindow("Image window", flags=cv2.CV_WINDOW_AUTOSIZE)
    self.bridge = CvBridge()
    self.image_sub = rospy.Subscriber("/head_mount_kinect/rgb/image_raw",Image,self.callback)

  def callback(self,data):
    try:
      cv_image = self.bridge.imgmsg_to_cv(data, "bgr8")
      cv_image = np.array(cv_image, dtype=np.uint8)
    except CvBridgeError, e:
      print e
    #print "Got callback"
    #(cols,rows) = cv2.GetSize(cv_image)
    #if cols > 60 and rows > 60 :
    #  cv.Circle(cv_image, (50,50), 10, 255)

#    cv.ShowImage("Image window", cv_image)
    #cv.WaitKey(3)
    
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    ret,thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    
    fg = cv2.erode(thresh,None,iterations = 2)
    bgt = cv2.dilate(thresh,None,iterations = 3)
    ret,bg = cv2.threshold(bgt,1,128,1)
    
    marker = cv2.add(fg,bg)
    marker32 = np.int32(marker)
    
    cv2.watershed(cv_image,marker32)
    m = cv2.convertScaleAbs(marker32)
    cv2.imshow("Image window", m)
    cv.WaitKey(5)
    try:
      temp = self.bridge.cv_to_imgmsg(cv.fromarray(m), "mono8")
      temp.header.frame_id = data.header.frame_id
      self.image_pub.publish(temp)
      print "Published callback", temp.header.frame_id
    except CvBridgeError, e:
      print e

def main(args):
  ic = Segment()
  rospy.init_node('segmentation', anonymous=True)
  try:
    rospy.spin()
  except KeyboardInterrupt:
    print "Shutting down"
  cv.DestroyAllWindows()

if __name__ == '__main__':
    main(sys.argv)
