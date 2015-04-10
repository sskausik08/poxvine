from VNSTopology import *
class NetworkMapping(object) :
	""" This class is used to provide the physical network paths between the subnets. """
	
	def __init__(self, phyTopo = None, virtTopo = None):
		self.virtualTopology = virtTopo
		self.physicalTopology = phyTopo
		self.networkRoutes = []
		self.hostMappings = []


	def read(self) :
		f1 = open("./pox/virtnetsim/" + self.virtualTopology.getName() + "-map/host-maps", 'r')
		hostMaps = f1.readlines()

		for line in hostMaps :
			map = line.split()
			# 0 : hostname 1 : virtual switch 2 : physical switch.
			self.physicalTopology.addSwitch(map[1])
			self.physicalTopology.addLinkStr(map[1], map[2], 10)

		f2 = open("./pox/virtnetsim/" + self.virtualTopology.getName() + "-map/switch-maps", 'r')
		swMaps = f2.readlines()

		for line in swMaps :
			map = line.split()
			# 0 : hostname 1 : virtual switch 2 : physical switch.
			self.physicalTopology.addSwitch(map[0])
			self.physicalTopology.addLinkStr(map[0], map[1], 10)


		virtRoute = self.virtualTopology.getRoute("s50", "s51")
		phyRoute = self.physicalTopology.getCompleteRoute(virtRoute)
		phyRoute.printRoute()


		"""
		virtRoute = Route()
		virtRoute.addSrcSubnet("10.0.0.0")
		virtRoute.addDstSubnet("10.1.0.0")
		virtRoute.addNextSwitch("s50")
		virtRoute.addNextSwitch("s100")
		virtRoute.addNextSwitch("s101")
		virtRoute.addNextSwitch("s51")

		phyRoute = self.physicalTopology.getCompleteRoute(virtRoute)
		phyRoute.printRoute()
		"""
			





	def readFromFile(self):
		f1 = open("./pox/virtnetsim/" + self.virtualTopology.getName() + "-map/host-maps", 'r')
		maps = f1.readlines()

		for line in maps :
			map = line.split()
			self.hostMappings.append(map)
		

		f1 = open("./pox/virtnetsim/" + self.virtualTopology.getName() + "-map/net-paths", 'r')
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

			self.networkRoutes.append(route)

	def getNetworkRoutes(self) :
		return self.networkRoutes

	def printMapping(self) :
		print "Network Routes : "
		for route in self.networkRoutes :
			route.printRoute()

			"""
			# First switch
			sw = route.getFirstSwitch()
			print sw
			sw_next = route.getNextRouteTagSwitch()
			print sw_next
			"""



virtTopo = Topology("tenant1")
phyTopo = Topology("phy")
NMap = NetworkMapping(phyTopo = phyTopo, virtTopo = virtTopo)
NMap.read()
NMap.printMapping()



class SwitchDatabase(object) :
	""" Database to match the switch to the topology """

	def __init__(self) :
		self.switchMap = dict()
		self.switchNumber = 1


	def getSwitchName(self, swName, topologyName) :
		key = topologyName + "-" + swName
		if key in self.switchMap : 
			return self.switchMap[key]
		else :
			""" Does not exist, add it in Database """
			name = "s" + str(self.switchNumber)
			self.switchNumber += 1
			self.switchMap[key] = name 


	def isPhysical(self, sw) :
		for key in self.switchMap.keys() :
			if self.switchMap[key] == sw and key.split("-")[0] == "phy":
				return True
		
		return False
				

	











		

