#!/usr/bin/env python

###############################################################################
# Copyright 2017 The Apollo Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###############################################################################

import os
import rospy
import argparse
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from map import Map
from localization import Localization
from modules.planning.proto import planning_pb2
from modules.localization.proto import localization_pb2
from planning import Planning

planning = Planning()
localization = Localization()

path_line_pool = []
path_line_pool_size = 4

speed_line_pool = []
speed_line_pool_size = 4

vehicle_position_line = None
vehicle_polygon_line = None

st_line_pool = []
st_line_pool_size = 2

obstacle_line_pool = []
obstacle_annotation_pool = []
obstacle_line_pool_size = 10


def localization_callback(localization_pb):
    localization.update_localization_pb(localization_pb)


def planning_callback(planning_pb):
    planning.update_planning_pb(planning_pb)
    planning.compute_path_data()
    planning.compute_speed_data()
    planning.compute_st_data()


def add_listener():
    rospy.init_node('plot_planning', anonymous=True)
    rospy.Subscriber('/apollo/planning',
                     planning_pb2.ADCTrajectory,
                     planning_callback)
    rospy.Subscriber('/apollo/localization/pose',
                     localization_pb2.LocalizationEstimate,
                     localization_callback)


def update(frame_number):
    for line in speed_line_pool:
        line.set_visible(False)
        line.set_label(None)
    for line in path_line_pool:
        line.set_visible(False)
        line.set_label(None)
    for line in obstacle_line_pool:
        line.set_visible(False)
    for line in st_line_pool:
        line.set_visible(False)
        line.set_label(None)
    for line in obstacle_annotation_pool:
        line.set_visible(False)

    vehicle_position_line.set_visible(False)
    vehicle_polygon_line.set_visible(False)

    planning.replot_path_data(path_line_pool)
    planning.replot_speed_data(speed_line_pool)

    planning.replot_st_data(obstacle_line_pool, st_line_pool, obstacle_annotation_pool)
    localization.replot_vehicle(vehicle_position_line, vehicle_polygon_line)
    ax.relim()
    ax.autoscale_view()
    ax.legend(loc="upper left")
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, 1.1))
    ax2.legend(loc="upper center", bbox_to_anchor=(0.5, 1.1))
    return obstacle_annotation_pool[0]


def init_line_pool(central_x, central_y):
    global vehicle_position_line, vehicle_polygon_line, s_speed_line
    global obstacle_line_pool, st_line_pool
    colors = ['b', 'g', 'r', 'k']

    for i in range(path_line_pool_size):
        line, = ax.plot([central_x], [central_y],
                        colors[i % len(colors)], lw=3, alpha=0.5)
        path_line_pool.append(line)

    for i in range(speed_line_pool_size):
        line, = ax1.plot([central_x], [central_y],
                        colors[i % len(colors)]+".", lw=3, alpha=0.5)
        speed_line_pool.append(line)

    for i in range(st_line_pool_size):
        line, = ax2.plot([0], [0],
                         colors[i % len(colors)]+".", lw=3, alpha=0.5)
        st_line_pool.append(line)

    for i in range(obstacle_line_pool_size):
        line, = ax2.plot([0], [0],
                         'r-', lw=3, alpha=0.5)
        anno = ax2.text(0, 0, "")
        obstacle_line_pool.append(line)
        obstacle_annotation_pool.append(anno)

    ax2.set_xlim(-1, 9)
    ax2.set_ylim(-1,90)

    vehicle_position_line, = ax.plot([central_x], [central_y], 'go', alpha=0.3)
    vehicle_polygon_line, = ax.plot([central_x], [central_y], 'g-')


if __name__ == '__main__':
    default_map_path = os.path.dirname(os.path.realpath(__file__))
    default_map_path += "/../../map/data/base_map.txt"

    parser = argparse.ArgumentParser(
        description="plot_planning is a tool to display "
                    "planning trajs on a map.",
        prog="plot_planning.py")
    parser.add_argument(
        "-m", "--map", action="store", type=str, required=False,
        default=default_map_path,
        help="Specify the map file in txt or binary format")
    args = parser.parse_args()

    add_listener()
    fig = plt.figure()
    ax = plt.subplot2grid((2, 3), (0, 0), rowspan=2, colspan=2)
    ax1 = plt.subplot2grid((2, 3), (0, 2))
    ax2 = plt.subplot2grid((2, 3), (1, 2))
    ax1.set_xlabel("t (second)")
    ax1.set_xlim([-2, 10])
    ax1.set_ylim([-1, 10])
    ax1.set_ylabel("speed (m/s)")

    map = Map()
    map.load(args.map)
    map.draw_lanes(ax, False, [])
    central_y = sum(ax.get_ylim())/2
    central_x = sum(ax.get_xlim())/2

    init_line_pool(central_x, central_y)

    ani = animation.FuncAnimation(fig, update, interval=100)

    ax.legend(loc="upper left")
    ax.axis('equal')
    plt.show()
