# -*- encoding:utf-8 -*-

import sys
import os
import cv2
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class football_img_handler:
    def __init__(self, prop_out, image_path, annotation_path, marker_path):
        self.prop_out = prop_out
        
        self.padding = 100
        self.prop_out['width'] += self.padding

        self.prop_out['dpi'] = math.gcd(self.prop_out['width'], self.prop_out['height'])
        self.prop_out['width0'] = self.prop_out['width']/self.prop_out['dpi']
        self.prop_out['height0'] = self.prop_out['height']/self.prop_out['dpi']
        
        self.read_image(image_path)
        self.read_annotation(annotation_path, sep='\t', header=0, index_col=0)
        self.read_marker(marker_path, sep='\t', header=0)
        
        
    def read_image(self, image_path):
        self.image = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)
        self.prop = {}
        self.prop['height'] = self.image.shape[0]
        self.prop['width'] = self.image.shape[1]
        
        return self.image, self.prop
    
    def read_annotation(self, anno_path, sep=' ', header=None, index_col=0):
        self.annotation_data = pd.read_csv(anno_path, sep=sep, header=header, index_col=0)
        
        self.annotation_data['cx'] = self.annotation_data['cx0'] * self.prop['width']
        self.annotation_data['cy'] = self.annotation_data['cy0'] * self.prop['height']

        self.annotation_data['width'] = self.annotation_data['width0'] * self.prop['width']
        self.annotation_data['height'] = self.annotation_data['height0'] * self.prop['height']

        self.annotation_data['xmin'] = self.annotation_data['cx'] - self.annotation_data['width']/2.0
        self.annotation_data['ymin'] = self.annotation_data['cy'] - self.annotation_data['height']/2.0

        self.annotation_data['x_player'] = self.annotation_data['cx']
        self.annotation_data['y_player'] = self.annotation_data['cy'] + self.annotation_data['height']/2.0

        self.color_list_players = self.annotation_data['class'].tolist()
        self.color_dict_players = {'judge': 'black', 'team1': 'blue', 'team2': 'red', 'audience': 'gray'}
        
        return self.annotation_data

    def read_marker(self, marker_path, sep=' ', header=None):
        self.marker_data = pd.read_csv(marker_path, sep=sep, header=header)
        self.marker_data['wx'] = self.marker_data['wx'] + self.padding
        selected_markers = self.marker_data[self.marker_data['flg_marker'] == 1]
        
        self.marker_pixel = selected_markers[['cx', 'cy']].values.astype(np.float32)
        self.marker_xy = selected_markers[['wx', 'wy']].values.astype(np.float32)
        
        return self.marker_data
    
    def reverse_point(self, point):
        return (point[0], self.prop_out['height']-point[1])

    def transform_points(self, point_data):
        ones = np.array([[1]*point_data.shape[0]])
        
        point_data_homog = np.concatenate([point_data, ones.T], axis=1)
        transformed_points_homog = np.dot(self.transform_matrix, point_data_homog.T).T
        
        x = np.array([transformed_points_homog[:, 0]/(transformed_points_homog[:, 2]+1e-8)])
        y = np.array([transformed_points_homog[:, 1]/(transformed_points_homog[: ,2]+1e-8)])
        
        return np.concatenate([x.T, y.T], axis=1)

    def output_image(self, display_players=True, display_markers=True, img_path_out='tmp.jpg'):
        fig = plt.figure(dpi=120, figsize=(16, 9))
        ax = fig.add_subplot(1, 1, 1)
        ax.imshow(self.image)
        
        if display_players is True:
            for idx, row in self.annotation_data.iterrows():
                rec = patches.Rectangle(xy=(row['xmin'], row['ymin']), width=row['width'], height=row['height'], color=self.color_dict_players[row['class']], fill=False)
                ax.add_patch(rec)

                cir = patches.Circle(xy=(row['x_player'], row['y_player']), radius=3, color='black', fill=False)
                ax.add_patch(cir)

        if display_markers is True:
            for idx, row in self.marker_data.iterrows():
                if row['flg_marker'] == 1:
                    cir = patches.Circle(xy=(row['cx'], row['cy']), radius=10, color='blue', fill=True)
                    ax.add_patch(cir)
        
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

        if img_path_out is not None:
            plt.savefig(img_path_out)
        else:
            plt.show()
        
    def output_transformed_image(self, draw_image=True, display_players=True, display_markers=True, draw_court=True, img_path_out='tmp.jpg'):
        self.transform_matrix = cv2.getPerspectiveTransform(self.marker_pixel, self.marker_xy)
        
        markers_xy = self.marker_data[['wx', 'wy']].values
        #markers_xy = self.transform_points(self.marker_data[['cx', 'cy']].values)
        
        players = self.transform_points(self.annotation_data[['x_player', 'y_player']].values)
        
        self.transformed_image = cv2.warpPerspective(self.image, self.transform_matrix, (self.prop_out['width'], self.prop_out['height']))
        
        fig = plt.figure(dpi=self.prop_out['dpi'], figsize=(self.prop_out['width0'], self.prop_out['height0']))
        ax = fig.add_subplot(1, 1, 1)
        
        if draw_image is True:
            ax.imshow(self.transformed_image)

        # draw markers
        if display_markers:
            for idx in range(markers_xy.shape[0]):
                if self.marker_data.iat[idx, 9] == 1:
                    point = self.reverse_point([markers_xy[idx][0], markers_xy[idx][1]])
                    cir = patches.Circle(xy=point, radius=7, color='blue', fill=True)
                    ax.add_patch(cir)

        # draw court
        if draw_court is True:
            linewidth = 5
            ax.plot([0, self.prop_out['width']], [0, 0], color='black', linewidth=linewidth)
            ax.plot([self.prop_out['width'], self.prop_out['width']], [0, self.prop_out['height']], color='black', linewidth=linewidth)
            ax.plot([0, self.prop_out['width']], [self.prop_out['height'], self.prop_out['height']], color='black', linewidth=linewidth)
            ax.plot([markers_xy[0][0], markers_xy[2][0]], [markers_xy[0][1], markers_xy[2][1]], color='black', linewidth=linewidth)

            point = (markers_xy[3][0], markers_xy[3][1])
            rec = patches.Rectangle(xy=point, width=(self.prop_out['width']-markers_xy[3][0]), height=(markers_xy[5][1]-markers_xy[3][1]), color='black', linewidth=linewidth, fill=False)
            ax.add_patch(rec)

            point = (markers_xy[7][0], markers_xy[7][1])
            rec = patches.Rectangle(xy=point, width=(self.prop_out['width']-markers_xy[7][0]), height=(markers_xy[9][1]-markers_xy[7][1]), color='black', linewidth=linewidth, fill=False)
            ax.add_patch(rec)

            radius = (markers_xy[14][1]-markers_xy[13][1])
            point = (markers_xy[13][0], markers_xy[13][1])
            cir = patches.Circle(xy=point, radius=radius, color='black', linewidth=linewidth, fill=False)
            ax.add_patch(cir)

            point = (markers_xy[16][0], markers_xy[16][1])
            arc = patches.Arc(xy=point, width=radius*2, height=radius*2, theta1=-53, theta2=53, color='black', linewidth=linewidth, fill=False)
            ax.add_patch(arc)
                    
        # draw players
        if display_players:
            for idx in range(players.shape[0]):
                if players[idx][1] < self.prop_out['height']:
                    point = self.reverse_point([players[idx][0], players[idx][1]])
                    cir = patches.Circle(xy=point, radius=3, color=self.color_dict_players[self.color_list_players[idx]], fill=True)
                    ax.add_patch(cir)

        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

        if img_path_out is not None:
            plt.savefig(img_path_out)
        else:
            plt.show()
        
def main():
    data_dir = sys.argv[1]
    
    image_path = os.path.join(data_dir, 'cd987c_9_8_png.rf.c2c8b4943b1d37db357ae80c08d33f3c.jpg')
    annotation_path = os.path.join(data_dir, 'annotation.txt')
    marker_path = os.path.join(data_dir, 'marker.txt')
    prop_out = {'width': 525, 'height': 680}

    hd = football_img_handler(prop_out, image_path, annotation_path, marker_path)
    
    hd.output_image(display_players=True, display_markers=True, img_path_out='players_with_bbox.jpg')
    hd.output_transformed_image(draw_image=False, display_players=True, display_markers=False, draw_court=True, img_path_out='players_xy.jpg')
    
if __name__ == '__main__':
    main()
    
