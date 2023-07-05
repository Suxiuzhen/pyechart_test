import cv2
from matplotlib import pyplot as plt

img_path = './ng_image/dog.jpg'


img = cv2.imread(img_path)
plt.imshow(img)
plt.show()
# cv2.imshow('my_pic', img)
#
# gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# cv2.imshow('gray_pic', gray_img)
# #
# equalized_img = cv2.equalizeHist(gray_img)
# cv2.imshow('equalized_pic', equalized_img)
#
# minmax_img = cv2.normalize(gray_img, None, 0, 255, cv2.NORM_MINMAX)
# cv2.imshow('minmax_img', minmax_img)
#
# color_enhanced_img = cv2.cvtColor(minmax_img, cv2.COLOR_GRAY2BGR)
# cv2.imshow('enhanced_img', color_enhanced_img)

cv2.waitKey()







