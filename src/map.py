import numpy as np

class MapRegion(object):
	"""
	A region of the map
	"""
	def __init__(self, name, xmin, xmax, ymin, ymax):
		self.name = name
		self.objects = []
		self.xmin = xmin
		self.xmax = xmax
		self.ymin = ymin
		self.ymax = ymax

	def get_name(self):
		return self.name

	def get_objects(self):
		return self.objects

	def add_object(self, obj):
		"""Add an object to this region (e.g. bomb or hostage)"""
		self.objects.append(obj)

	def set_objects(self, obj_list):
		self.objects = obj_list

	def delete_object(self, obj):
		self.objects.remove(obj)

	def contains_point(self, point):
		"""Return True if given point is inside the region
		params:
		point: a list of float [x, y, z]
		"""
		threshold = 0.6
		x = point[0]
		y = point[1]
		if (x >= (self.xmin - threshold) and x <= (self.xmax + threshold) and
			y >= (self.ymin - threshold) and y <= (self.ymax + threshold)):
		    return True
		return False

	def get_random_point(self):
		"""Return a random point from this region"""
		x = np.random.uniform(self.xmin, self.xmax)
		y = np.random.uniform(self.ymin, self.ymax)
		return [x, y, 0.0]

class Map(object):
	def __init__(self):
		self.regions = []

	def add_region(self, region):
		if not isinstance(region, MapRegion):
			raise Exception("Can't add region as it's not an instance of MapRegion.")

		self.regions.append(region)

	def get_regions(self):
		return self.regions

	def get_region(self, region_name):
		for region in self.regions:
			if region.get_name() == region_name:
				return region
		return None

	def get_region_names(self):
		names = []
		for region in self.regions:
			names.append(region.get_name())
		return names

	def get_region_from_point(self, point):
		for region in self.regions:
			if region.contains_point(point):
				return region
		return None