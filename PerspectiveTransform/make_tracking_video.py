# -*- encoding:utf-8 -*-

import sys
import io
import os
import math
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from annotation_reader import annotation_reader

class make_tracking_video:
  ###############
  def __init__(self, annotation_path, out_video_path, prop_out):
    self.out_video_path = out_video_path
    self.prop_out = prop_out
    self.annotation_path = annotation_path
    self.color_map = {0: 'red', 1: 'pink', 2: 'yellow', 3: 'green', 4: 'blue'}
    self.dpi = 288
    self.frames = 21
    
  ###############
  def make_video(self):
    # init annotation_reader
    self.anno_hd = annotation_reader(self.annotation_path)

    fig = plt.figure(dpi=self.dpi)
    plt.axes().set_aspect('equal')

    ani = FuncAnimation(fig, self.draw, interval = 100, frames = range(self.frames))
    ani.save(self.out_video_path)

  ###############
  def draw(self, frame_no):
    print("# ", frame_no)
    plt.cla()
    plt.xlim(0, self.prop_out['width'])
    plt.ylim(0, self.prop_out['height'])
    plt.subplots_adjust(left=0, right=1, bottom=0, top=1)
    plt.axis("off")
    
    frame_no, data_list = self.anno_hd.get_annotation()
    if data_list is not None:
      color_data = []
      point_data = []
      for point in data_list:
        color_data.append(self.color_map[point[1]])
        point_data.append([point[2], point[3]])
      point_data = self.reverse_coordinate('y', point_data, self.prop_out['height'])
      point_data = self.transpose(point_data)

      plt.scatter(point_data[0], point_data[1], color= color_data, edgecolors=color_data, s=30)
  
  ###############
  def reverse_coordinate(self, direction, this_list, max_len):
    new_list = []
    if direction == 'x':
      resid = 0
    else:
      resid = 1

    for item in this_list:
      new_item = []
      for loop in range(len(item)):
        if loop % 2 == resid:
          new_item.append(max_len - item[loop])
        else:
          new_item.append(item[loop])
      new_list.append(new_item)
    
    return new_list

  ###############
  def transpose(self, this_list):
    new_list = []
    dim = len(this_list[0])
    
    for loop in range(dim):
      new_item = []
      for item in this_list:
        new_item.append(item[loop])
      new_list.append(new_item)
    
    return new_list

#######################################################################################
#                                                                                     #
#                                                                                     #
#                                                                                     #
#######################################################################################
def track():
  if len(sys.argv) < 3:
    sys.stderr.write('Usage: python make_tracking_video.py annotation_path out_video_path\n')
    sys.exit(1)
      
  annotation_path = sys.argv[1]
  out_video_path = sys.argv[2]

  prop_out = {}
  prop_out['width'] = 120
  prop_out['height'] = 120

  hd = make_tracking_video(annotation_path, out_video_path, prop_out)  
  hd.make_video()

if __name__ == '__main__':
    track()
