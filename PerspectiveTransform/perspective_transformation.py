import sys
import cv2
import numpy as np
from annotation_reader import annotation_reader

class perspective_transformation:
  #####
  def __init__(self, pixel_point_path, world_point_path):
    self.pixel_points = self.read_marker(pixel_point_path)
    self.world_points = self.read_marker(world_point_path)
    
  #####
  def read_marker(self, marker_path):
    marker = []
    with open(marker_path, 'r') as fp:
      header = fp.readline()
      for line in fp:
        data = line[:-1].split('\t')
        x = float(data[0])
        y = float(data[1])
        marker.append([x,y])

    marker = np.array(marker).astype(np.float32)

    return marker
  
  #####
  def get_transform_matrix(self, pixel_points=None, world_points=None):
    if pixel_points is None:
      pixel_points = self.pixel_points
    if world_points is None:
      world_points = self.world_points
      
    self.transformation_matrix = cv2.getPerspectiveTransform(pixel_points, world_points)
    
  # input:
  # - location: numpy(#points, 2)
  # - transform_matrix (3,3)
  # output:
  # - result: numpy(#points, 2)
  def transform(self, location):
    this_array = np.array([[1] * location.shape[0]], np.float32)
    location_proj = np.concatenate((location.T, this_array), axis=0)
    result_proj = np.dot(self.transformation_matrix, location_proj)
    
    result = []
    for loop in range(result_proj.shape[1]):
      result.append([result_proj[0][loop]/(result_proj[2][loop]+1e-8), result_proj[1][loop]/(result_proj[2][loop]+1e-8)])

    return np.array(result)

  def transform_image(self, img, width, height):
    img_transformed = cv2.warpPerspective(img, self.transformation_matrix, (width, height))

    return img_transformed
    
def transform_annotation_data():
  pixel_point_path = sys.argv[1]
  world_point_path = sys.argv[2]
  annotation_path = sys.argv[3]
    
  columns = ['frame_no', 'class_no', 'x', 'y']
  print('\t'.join(columns))
  
  ### init perspective_transformation
  geo_hd = perspective_transformation(pixel_point_path, world_point_path)
  geo_hd.get_transform_matrix()

  # init annotation handler
  anno_hd = annotation_reader(annotation_path)

  # process each frame
  while True:
    frmae_no, data_list = anno_hd.get_annotation()
    if data_list is None:
      break
    class_list, point_list = anno_hd.xyxy2point()
    xy_point_list = geo_hd.transform(np.array(point_list))

    for idx in range(len(data_list)):
      print(frame_no, class_list[idx], xy_point_list[idx][0], xy_point_list[idx][1], sep="\t")

if __name__ == '__main__':
  transform_annotation_data()



