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




		

