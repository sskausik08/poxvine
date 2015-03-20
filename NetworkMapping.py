class NetworkMapping(object) :
	""" This class is used to provide the physical network paths between the subnets. """
	
	def __init__(self, phyTopo, virtTopo):
		self.virtualTopology = virtTopo
		self.physicalTopology = phyTopo
		self.networkPaths = []
		self.hostMappings = []

	def readFromFile(self):
		f1 = open(self.virtualTopology.getName() + "-net/host-maps", 'r')
		maps = f1.readlines()

		for line in maps :
			map = line.split()
			self.hostMappings.append(map)
		

		f1 = open(self.virtualTopology.getName() + "-net/net-paths", 'r')
		paths = f1.readlines()

		for line in paths :
			path = line.split()
			self.networkPaths.append(path)


class Route(object) :
	""" This class is used to provide information of the route between two subnets with the routeTags."""

	def __init__(self):
		self.route = [] # Store the switch sequence 
		self.routeTags = [] # For every corresponding switch, store whether a routeTag change is required or not.
		self.routeIndex = 0

	def addSrcSubnet(self, subnet):
		self.srcSubnet = subnet

	def addDstSubnet(self, subnet):
		self.dstSubnet = subnet

	def addNextSwitch(self, sw, routeTag = False):
		self.route.append(sw)
		self.routeTags.append(routeTag)

	def getFirstSwitch(self) :
		return self.route[0]
	
	def getCurrentSwitch(self) : 
		""" Increment Route Index and return switch. Not to be used for first switch. """
		self.routeIndex += 1
		if self.routeIndex >= len(self.route) :
			# End of route. 
			return None
		else :
			return self.route[self.routeIndex]

	def getNextSwitch(self) :
		if self.routeIndex + 1 >= len(self.route) :
			return None
		else :
			return self.route[self.routeIndex + 1]

	def getCurrentRouteTag(self):
		""" Returns current Route Tag. Usage to be done after calling getCurrentSwitch() """
		if self.routeIndex >= len(self.route) :
			# End of route.  
			return False
		else :
			return self.routeTags[self.routeIndex]

	def isLastSwitch(self) :
		if self.routeIndex == len(self.route) - 1 :
			return True
		else :
			return False











		

