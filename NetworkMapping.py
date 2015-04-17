from VNSTopology import *
class NetworkMapping(object) :
	""" This class is used to provide the physical network paths between the subnets. """
	
	def __init__(self, phyTopo, virtTopo, swDatabase):
		self.virtualTopology = virtTopo
		self.physicalTopology = phyTopo
		self.swDatabase = swDatabase
		self.networkRoutes = []
		self.hostMappings = []
		self.endPoints = []


	def read(self) :
		f1 = open("./pox/virtnetsim/" + self.virtualTopology.getName() + "-map/host-maps", 'r')
		hostMaps = f1.readlines()

		for line in hostMaps :
			map = line.split()
			# 0 : hostname 1 : virtual switch 2 : physical switch.
			sw1 = self.swDatabase.getSwitchName(map[1], self.virtualTopology.getName())
			self.physicalTopology.addSwitch(sw1)
			sw2 = self.swDatabase.getSwitchName(map[2], self.physicalTopology.getName())
			self.physicalTopology.addLinkStr(sw1, sw2, 10)

			self.endPoints.append([sw1, map[0]])


		f2 = open("./pox/virtnetsim/" + self.virtualTopology.getName() + "-map/switch-maps", 'r')
		swMaps = f2.readlines()

		for line in swMaps :
			map = line.split()
			# 0 : hostname 1 : virtual switch 2 : physical switch.
			sw1 = self.swDatabase.getSwitchName(map[0], self.virtualTopology.getName())
			self.physicalTopology.addSwitch(sw1)
			sw2 = self.swDatabase.getSwitchName(map[1], self.physicalTopology.getName())
			self.physicalTopology.addLinkStr(sw1, sw2, 10)



		# Get Routes between end Points. 
		# {TODO} : Possibility of no paths.
		for sw1 in self.endPoints :
			for sw2 in self.endPoints :
				if not sw1[0] == sw2[0] :
					virtRoute = self.virtualTopology.getRoute(sw1[0], sw2[0])
					virtRoute.addSrcSubnet(sw1[1])
					virtRoute.addDstSubnet(sw2[1])
					phyRoute = self.physicalTopology.getCompleteRoute(virtRoute)
					phyRoute.setRouteTags(self.swDatabase)
					phyRoute.printRoute(self.swDatabase)

					self.networkRoutes.append(phyRoute)	






		#virtRoute = self.virtualTopology.getRoute("s50", "s51")
		#phyRoute = self.physicalTopology.getCompleteRoute(virtRoute)
		#phyRoute.printRoute()


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


"""
virtTopo = Topology("tenant1")
phyTopo = Topology("phy")
NMap = NetworkMapping(phyTopo = phyTopo, virtTopo = virtTopo)
NMap.read()
NMap.printMapping()
"""



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
			return name

	def getSwitchKey(self, sw) :
		for key in self.switchMap.keys() :
			if self.switchMap[key] == sw :
				return key
		return "None"

	def isPhysical(self, sw) :
		for key in self.switchMap.keys() :
			if self.switchMap[key] == sw and key.split("-")[0] == "phy":
				return True
		
		return False
				

	











		

