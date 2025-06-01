# -*- encoding:utf-8 -*-
import sys

class annotation_reader:
  def __init__(self, annotation_path):
    self.annotation_path = annotation_path

    self.frame_no = -1
    self.next_frame_no = -1
    self.data_list = []
    self.next_data_list = []

    self.init()
  
  def init(self):
    self.fp_anno = open(self.annotation_path, 'r')
    self.eof = False
    
    # header
    header = self.fp_anno.readline()
    
    line = self.fp_anno.readline()
    data = line[:-1].split('\t')
    data = self.pretty_annotation(data)
    self.next_frame_no = data[0]
    self.next_data_list.append(data)

  # output: frame_no(int), data_list(list)
  # where data_list = [[frame_no0, class_no0, xmin0, ymin0, xmax0, ymax0],
  #                    [frame_no1, class_no1, xmin1, ymin1, xmax1, ymax1],
  #                   ...]
  def get_annotation(self):
    if self.eof:
      return None, None
      
    self.frame_no = self.next_frame_no
    self.data_list = self.next_data_list
    self.next_data_list = []
    
    # input:
    # 0: frame_no (0, 1, 2, ...)
    # 1: class_no (0, 1, 2, ...)
    # 2: xmin(pixel)
    # 3: ymin(pixel)
    # 4: xmax(pixel)
    # 5: ymax(pixel)
    while True:
      line = self.fp_anno.readline()
      if not line:
        self.eof = True
        return self.frame_no, self.data_list
        
      data = line[:-1].split('\t')
      data = self.pretty_annotation(data)

      if data[0] == self.frame_no:
        self.data_list.append(data)
      else:
        self.next_frame_no = data[0]
        self.next_data_list.append(data)

        return self.frame_no, self.data_list
    
  def xyxy2point(self):
    class_list = []
    point_list = []
    for data in self.data_list:
      class_list.append(data[1])
      point_list.append([(data[2]+data[4])/2.0, data[5]])
      
    return class_list, point_list
    
  def pretty_annotation(self, data):
    new_data = []
    new_data.append(int(data[0]))
    new_data.append(int(data[1]))
    for loop in range(2, len(data)):
      new_data.append(float(data[loop]))
    
    return new_data

  def close_fp(self):
    self.fp_anno.close()
    
