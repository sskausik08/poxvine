from VNSTopology import Topology
class NetworkMapping(object) :
	""" This class is used to provide the physical network paths between the subnets. """
	
	def __init__(self, phyTopo = None, virtTopo = None):
		self.virtualTopology = virtTopo
		self.physicalTopology = phyTopo
		self.networkPaths = []
		self.hostMappings = []

	def readFromFile(self):
		f1 = open(self.virtualTopology.getName() + "-map/host-maps", 'r')
		maps = f1.readlines()

		for line in maps :
			map = line.split()
			self.hostMappings.append(map)
		

		f1 = open(self.virtualTopology.getName() + "-map/net-paths", 'r')
		paths = f1.readlines()

		for line in paths :
			fields = line.split()
			route = Route()
			route.addSrcSubnet(fields[0], int(fields[1]))
			route.addDstSubnet(fields[2], int(fields[3]))

			# from 4 to end : sw rt sw rt .....
			i = 4
			while i < len(fields) :
				if fields[i + 1] == "t" :
					route.addNextSwitch(fields[i], True)
				else :
					route.addNextSwitch(fields[i], False)
				i += 2

			self.networkPaths.append(route)

	def printMapping(self) :
		print "Network Paths : "
		for route in self.networkPaths :
			route.printRoute()






class Route(object) :
	""" This class is used to provide information of the route between two subnets with the routeTags."""

	def __init__(self):
		self.route = [] # Store the switch sequence 
		self.routeTags = [] # For every corresponding switch, store whether a routeTag change is required or not.
		self.routeIndex = 0

	def addSrcSubnet(self, subnet, prefixlen = 24):
		self.srcSubnet = subnet
		self.srcPrefixLen = prefixlen

	def addDstSubnet(self, subnet, prefixlen = 24):
		self.dstSubnet = subnet
		self.dstPrefixLen = prefixlen

	def addNextSwitch(self, sw, routeTag = False):
		self.route.append(sw)
		self.routeTags.append(routeTag)

	def printRoute(self) :
		print "Route: " + self.srcSubnet + " -> " + self.dstSubnet
		i = 0
		while i < len(self.route):
			print self.route[i] + " " + str(self.routeTags[i])
			i += 1


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



virtTopo = Topology("tenant1")
NMap = NetworkMapping(virtTopo = virtTopo)
NMap.readFromFile()
NMap.printMapping()








		

