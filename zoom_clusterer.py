# coding: utf-8
from __future__ import division
import math

"""
Clustering cities on different zooms, and define a main city for each cluster
(this city is visible on map with given zoom level).
Clustering algorithm: https://developers.google.com/maps/articles/toomanymarkers#markerclusterer
Some useful formulas: http://www.movable-type.co.uk/scripts/latlong.html
"""

R = 6371  # Earth's radius


def distance(p1, p2):
    """
    Distance between points using haversine formula
    """
    dlat = (p2[0] - p1[0])*math.pi/180.0
    dlng = (p2[1] - p1[1])*math.pi/180.0
    a = math.sin(dlat/2)**2 + math.cos(p1[0]*math.pi/180.0)*math.cos(p2[0]*math.pi/180.0)*(math.sin(dlng/2)**2)
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R*c
    return d


def destination_point(point, dist, bearing):
    """
    Finding destination point from the given point with given distance and direction (bearing)
    """
    point, bearing = (math.radians(point[0]), math.radians(point[1])), math.radians(bearing)
    lat = math.asin(math.sin(point[0])*math.cos(dist/R) + math.cos(point[0])*math.sin(dist/R)*math.cos(bearing))
    lng = point[1] + math.atan2(math.sin(bearing)*math.sin(dist/R)*math.cos(point[0]), math.cos(dist/R) - math.sin(point[0])*math.sin(lat))
    return math.degrees(lat), (math.degrees(lng)+540)%360-180


class Cluster(object):
    """
    Cluster object
    """

    _items = []
    _center = None
    _bounds = None

    def __init__(self, center, size):
        self._items = []
        self._center = center
        halfsize = size / 2
        n = destination_point(center, halfsize, 0)
        e = destination_point(center, halfsize, 90)
        s = destination_point(center, halfsize, 180)
        w = destination_point(center, halfsize, 270)
        self._bounds = ((s[0], w[1]), (n[0], e[1]))

    def get_center(self):
        return self._center

    def get_bounds(self):
        return self._bounds

    def contains(self, point):
        if self._bounds[0][0] <= point[0] <= self._bounds[1][0] and self._bounds[0][1] <= point[1] <= self._bounds[1][1]:
            return True
        return False

    def add_item(self, item):
        self._items.append(item)

    def items(self):
        return self._items


class ZoomLevelClusterer():

    _min_zoom = 3
    _max_zoom = 9
    _cluster_size = {
        3: 1400,
        4: 700,
        5: 350,
        6: 175,
        7: 88,
        8: 44,
    }
    
    def __init__(self, min_zoom=None, max_zoom=None, cluster_size=None):
        if min_zoom:
            self._min_zoom = min_zoom
        if max_zoom:
            self._max_zoom = max_zoom
        if cluster_size:
            self._cluster_size = cluster_size

    def execute(self, data):
        """
        data - list of dictionaries, including following fields (+ any other fields):
        {
            'lat': [latitude]
            'lon': [longitude]
            'is_capital': [is country capital, boolean] 
            'popularity': [some popularity value]
        }
        Adding 'zoom_level' to returned  dictionary
        """
        for item in data:
            item['zoom_level'] = self._max_zoom

        for zoom in range(self._min_zoom, self._max_zoom):
            print('Processing zoom %s' % zoom)
            clusters = []
            data = sorted(data, key=lambda x: (-x['is_capital'], -x['popularity']))
            for city in data:
                coords = (city['lat'], city['lon'])
                cluster_to_add = None
                for cluster in clusters:
                    if cluster.contains(coords):
                        cluster_to_add = cluster
                        break
                if cluster_to_add:
                    cluster_to_add.add_item(city)
                else:
                    new_cluster = Cluster(coords, self._cluster_size[zoom])
                    new_cluster.add_item(city)
                    clusters.append(new_cluster)

            for i, cluster in enumerate(clusters):
                if len(cluster.items()) > 0:
                    main_city = cluster.items()[0]
                    if main_city['zoom_level'] > zoom:
                        main_city['zoom_level'] = zoom
                        
        return data
