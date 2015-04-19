class Switch(object) :
	def __init__(self, name = "sw0", size = 1024):
		self.name = name
		self.flowTableSize=size
		self.neighbours = []

		# Used for routing.
		self.parent = None

	def addLink(self, dst, bw) :
		self.neighbours.append(dst)

	def getName(self) :
		return self.name

	def getFlowTableSize(self) :
		return self.flowTableSize

	def getNeighbours(self) :
		return self.neighbours

	def getParent(self) :
		return self.parent

	def setParent(self, parent) :
		self.parent = parent


class Topology(object):
	"Class for a Topology"
	def __init__(self, name, netDatabase, tenantID = 0):
		self.name = name
		self.racks = []
		self.switches = dict()
		self.hosts = dict()
		self.tenantID = tenantID
		self.netDatabase = netDatabase
		
		# Initialise from configuration files.
		self.readFromFile()

	def getName(self) :
		return self.name

	def addRack(self, rack) :
		self.racks.append(rack)

	def getRack(self, rackName) :
		for rack in self.racks :
			if rack.getName() == rackName  :
				return rack
		return None

	def getHost(self, hostName) :
		for rack in self.racks :
			host = rack.getHost(hostName)
			if not host == None :
				return host
		return None

	def display(self) :
		print "Topology " + self.name + ":"
		for rack in self.racks :
			rack.display()

	def displayMapping(self) :
		print "Topology " + self.name + " Mapping Info:"
		for rack in self.racks :
			rack.displayMapping()

	def mapSubnet(self, subnet) :
		""" Map virtual subnet onto the physical Topology. """

		for rack in self.racks :
			mapFlag = rack.mapSubnet(subnet)
			if mapFlag == True :
				""" Mapping possible on rack. Commit the mapping """
				rack.commitMapping()
				return
			else :
				""" Mapping not possible on rack. Reset the uncommitted mapping """
				rack.resetMapping()

	def addSwitch(self, name, size=1024) :
		sw = Switch(name, size)
		self.switches[name] = sw

	def createHost(self, name, capacity, ip, sw) :
		h = Host(name = name, ip = ip, capacity = capacity)
		h.setSwitch(sw)
		self.hosts[name] = h

	def addHost(self, host) :
		self.hosts[host.getName()] = host

	def getHosts(self) :
		return self.hosts

	def addLink(self, src, dst, bw) :
		src.addLink(dst,bw)
		dst.addLink(src,bw)

	def addLinkStr(self, srcStr, dstStr, bw) :
		src = self.switches[srcStr]
		dst = self.switches[dstStr]
		self.addLink(src = src, dst = dst, bw = bw)

	def readFromFile(self) :
		# Read the switches
		f1 = open("./pox/virtnetsim/" + self.name + "/" + self.name + "-switches", 'r')
		switches = f1.readlines()

		for line in switches :
			fields = line.split()
			sw = self.netDatabase.getSwitchName(fields[0], self.name)
			self.addSwitch(sw, int(fields[1]))

		# Read the Hosts for virtual topologies.
		if not self.name == "phy" :
	 		f2 = open("./pox/virtnetsim/" + self.name + "/" + self.name + "-hosts", 'r')
			hosts = f2.readlines()

			for line in hosts :
				fields = line.split()
				sw = self.netDatabase.getSwitchName(fields[4], self.name)
				hostName = self.netDatabase.getHostName(fields[0], self.name)
				self.createHost(hostName, int(fields[2]), fields[3], self.switches[sw])

		# Read the links
		f3 = open("./pox/virtnetsim/" + self.name + "/" + self.name + "-links", 'r')
		links = f3.readlines()

		for line in links :
			fields = line.split()
			sw1 = self.netDatabase.getSwitchName(fields[0], self.name)
			sw2 = self.netDatabase.getSwitchName(fields[1], self.name)
			self.addLink(src=self.switches[sw1], dst=self.switches[sw2], bw=int(fields[2]))

	def writeToFile(self) :
		f1 = open("./pox/virtnetsim/virtnetsim-mininet-files/" + self.name + "-switches", 'w')

		for swName in self.switches.iterkeys() :
			sw = self.switches[swName]
			f1.write(sw.getName() + " " + str(sw.getFlowTableSize()) + "\n")

		f2 = open("./pox/virtnetsim/virtnetsim-mininet-files/" + self.name + "-links", 'w')

		for swName in self.switches.iterkeys() :
			sw = self.switches[swName]
			neighbours = sw.getNeighbours()	

			for node in neighbours :
				if sw.getName() < node.getName() :
					f2.write(sw.getName() + " " + node.getName() + " 10\n")

		
		f3 = open("./pox/virtnetsim/virtnetsim-mininet-files/" + self.name + "-hosts", 'w')

		for hostName in self.hosts.iterkeys() :
			host = self.hosts[hostName]
			f3.write(host.getName() + " " + str(host.capacity()) + " " + host.getIP() + " " + host.getSwitch().getName() + "\n")


	def getNeighbour(self, src, dst) :
		# Breadth First Search from src to dst.
		srcSw = self.switches[src]
		dstSw = self.switches[dst]
		next = [srcSw]

		while dstSw not in next:
			for node in next:
				neighbours = node.getNeighbours()
				for n in neighbours:
					if n not in next :
						next.append(n)
						n.setParent(node)

		# Backtrack from dstSw to srcSw to find neighbour.
		parent = dstSw

		while not parent.getParent() == srcSw :
			parent = parent.getParent()

		return parent.getName()

	def getRoute(self, src, dst) :
		# Breadth First Search from src to dst.
		srcSw = self.switches[src]
		dstSw = self.switches[dst]
		next = [srcSw]

		while dstSw not in next:
			for node in next:
				neighbours = node.getNeighbours()
				for n in neighbours:
					if n not in next :
						next.append(n)
						n.setParent(node)

		# Backtrack from dstSw to srcSw to find neighbour.
		route = Route()
		route.addNextSwitch(dstSw.getName())
		parent = dstSw.getParent()

		while not parent == srcSw :
			route.addNextSwitch(parent.getName())
			parent = parent.getParent()

		route.addNextSwitch(srcSw.getName())
		route.reverse()

		route.setTenantID(self.tenantID)
		return route

	def getCompleteRoute(self, route):
		""" Finds complete route from next node info """

		completeRoute = Route()
		completeRoute.addSrcSubnet(route.getSrcSubnet())
		completeRoute.addDstSubnet(route.getDstSubnet())
		completeRoute.setTenantID(route.getTenantID())
		sw = route.getFirstSwitch()
		sw_next = route.getCurrentSwitch()

		completeRoute.addRoute(self.getRoute(sw, sw_next))
		

		sw = sw_next
		while not route.isLastSwitch():
			sw_next = route.getCurrentSwitch()

			completeRoute.removeLastSwitch()
			completeRoute.addRoute(self.getRoute(sw, sw_next))

			sw = sw_next

		return completeRoute




class Rack(object):
	"Class for a Rack."

	def __init__(self, name):
		self.hostlist = []
		self.name = name
		self.countMappedHosts = 0


	def display(self) :
		for host in self.hostlist : 
			host.display() 

	def displayMapping(self) :
		print "Mapping for Rack " + self.name
		for host in self.hostlist : 
			host.displayMapping() 

	def getName(self) :
		return self.name

	def addHost(self, host) :
		self.hostlist.append(host)

	def getHost(self, hostName) :
		for host in hostlist :
			if(host.getName() == hostName) :
				return host
		return None

	def capacityLeft(self) :
		
		remainingCapacity = 0
		for host in self.hostlist :
			remainingCapacity += host.capacityLeft()

		return remainingCapacity

	def totalCapacity(self) :

		totCapacity = 0
		for host in self.hostlist :
			totCapacity += host.capacity()

		return totCapacity

	def mapSubnet(self, subnet) :
		""" This function is used to map a complete subnet to a rack. This will return false if it cannot map the entire subnet """

		canMapSubnet = True
		if(subnet.totalCapacity() > self.capacityLeft()) :
			canMapSubnet = False
			print "capacity not sufficient"
		else :
			""" Rack capacity exceeds subnet capacity. Find a mapping if possible"""
			while not subnet.isSubnetMapped() :
				vm1 = subnet.getLargestUnmappedHost()
				# print "Largest VM is" 
				# vm1.display()
				h1 = self.getLargestUnmappedHost()
				#print "Largest host is"
				#h1.display()
				if vm1.capacity() > h1.capacityLeft() :
					# Largest VM cannot fit on the largest physical host.
					canMapSubnet = False
					break
				else :
					# Mapping possible. Map vm1 to h1.
					h1.mapVM(vm1)
					# increment mapped host count of subnet.
					subnet.incrementMappedHostCount()

			# Subnet Mapped.
		return canMapSubnet

	def commitMapping(self) :
		""" Commit the pending mappings on each of the hosts. """
		for host in self.hostlist :
			host.commitMappedVM()

	def resetMapping(self) :
		""" Reset the pending mappings on each of the hosts. """
		for host in self.hostlist :
			host.resetMappedVM()


	def getLargestUnmappedHost(self) :
		""" Returns largest unmapped host for a virtual subnet 
			Returns largest physical host for a real rack (because host will be unmapped for a physical host)"""

		maxcap = 0
		maxhost = self.hostlist[0]
		for host in self.hostlist :
			if host.capacityLeft() > maxcap and host.isMapped() == False :
				# For a virtual host, capacityLeft and capacity is the same.

				maxcap = host.capacityLeft()
				maxhost = host

		return maxhost

	def incrementMappedHostCount(self) :
		self.countMappedHosts = self.countMappedHosts + 1

	def isSubnetMapped(self) : 
		""" Returns true if the hosts in the subnet have been mapped """
		if self.countMappedHosts == len(self.hostlist) :
			# print "Subnet is mapped"
			return True
		else :
			#print "Subnet is not mapped"
			return False


		
class Host(object):
	"The Host class can be used to represent both the physical and virtual hosts"
	def __init__(self, name = "h0", capacity = "0", ip = "0.0.0.0"):
		self.name = name
		self.ip = ip
		self.totalCapacity = capacity;
		self.uncommittedRemainingCapacity = capacity;
		self.committedRemainingCapacity = capacity; 
		self.committedVMList = []
		self.uncommittedVMList = []
		self.isMappedFlag = False

	def display(self) :
		print(self.name + " " + str(self.totalCapacity) + " " + str(self.committedRemainingCapacity) + " " + str(self.uncommittedRemainingCapacity)) 

	def displayMapping(self) :
		print "Mapping Info for host " + self.name
		print "Total Capacity:" + str(self.totalCapacity) + " remainingCapacity:" + str(self.committedRemainingCapacity)
		print "Mapping on the host are ->"
		for vm in self.committedVMList :
			vm.display()

	def capacityLeft(self) :
		return self.uncommittedRemainingCapacity

	def mapVM(self, vm) :
		# For physical hosts.
		self.uncommittedRemainingCapacity = self.uncommittedRemainingCapacity - vm.capacity()
		# print self.name + " has capacity left " + str(self.uncommittedRemainingCapacity)
		self.uncommittedVMList.append(vm)
		vm.setMapped(True)

	def commitMappedVM(self) :
		#Commit the VMs in the uncommitted list.
		self.committedVMList.extend(self.uncommittedVMList)
		self.committedRemainingCapacity = self.uncommittedRemainingCapacity
		self.uncommittedVMList = []

	def resetMappedVM(self) :
		# reset the uncommitted VMs. 
		for vm in self.uncommittedVMList :
			vm.setMapped(False)
		self.uncommittedVMList[:] = []
		self.uncommittedRemainingCapacity = self.committedRemainingCapacity

	def capacity(self) :
		return self.totalCapacity;

	def setMapped(self, flag) :
		self.isMappedFlag = flag

	def isMapped(self) :
		return self.isMappedFlag

	def getName(self) :
		return self.name

	def getIP(self) :
		return self.ip

	def getSwitch(self) :
		return self.switch

	def setSwitch(self, sw) :
		# Switch connected to host.
		self.switch = sw


class Route(object) :
	""" This class is used to provide information of the route between two subnets with the routeTags.
	Important Convention : The First and Last switch must have RouteTag True.
	setRouteTags function ensures the above convention"""

	def __init__(self):
		self.route = [] # Store the switch sequence 
		self.routeTags = [] # For every corresponding switch, store whether a routeTag change is required or not.
		self.routeIndex = 0
		self.tenantID = 0
		self.srcSubnet = "0.0.0.0"
		self.dstSubnet = "0.0.0.0"

	def addSrcSubnet(self, subnet, prefixlen = 24):
		self.srcSubnet = subnet
		self.srcPrefixLen = prefixlen

	def addDstSubnet(self, subnet, prefixlen = 24):
		self.dstSubnet = subnet
		self.dstPrefixLen = prefixlen

	def getSrcSubnet(self):
		return self.srcSubnet

	def getDstSubnet(self):
		return self.dstSubnet

	def getTenantID(self) :
		return self.tenantID

	def setTenantID(self, tenantID) :
		self.tenantID = tenantID

	def addNextSwitch(self, sw, routeTag = False):
		self.route.append(sw)
		self.routeTags.append(routeTag)

	def removeLastSwitch(self) :
		self.route.pop()
		self.routeTags.pop()

	def addRoute(self, route) :
		self.route.extend(route.getSwitches())
		self.routeTags.extend(route.getRouteTags())

	def getSwitches(self) :
		return self.route

	def getRouteTags(self) :
		return self.routeTags 

	def setRouteTags(self, netDatabase) :
		""" Setting the route Tags """
		i = 0
		while i < len(self.route):
			if i == 0 or i == len(self.route) - 1 :
				self.routeTags[i] = True
			elif not netDatabase.isPhysical(self.route[i]) :
				# i - 1 and i + 1 are both physical switches
				self.routeTags[i] = True
				self.routeTags[i - 1] = True
				self.routeTags[i + 1] = True
			i = i + 1

	def printRoute(self, netDatabase = None) :
		print "Tenant " + str(self.tenantID) + " Route: " + self.srcSubnet + " -> " + self.dstSubnet 
		i = 0
		if netDatabase == None :
			while i < len(self.route):
				print self.route[i] + " " + str(self.routeTags[i])
				i += 1
		else :
			while i < len(self.route):
				print netDatabase.getSwitchKey(self.route[i]) + " " + str(self.routeTags[i])
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

	def getNextRouteTagSwitch(self) :
		""" Increment Route Index and return switch with Routetag. Not to be used for first switch. """
		self.routeIndex += 1
		while not self.routeTags[self.routeIndex] :
			self.routeIndex += 1

		if self.routeIndex >= len(self.route) :
			return None
		else :
			return self.route[self.routeIndex]


	def getNextSwitch(self) :
		if self.routeIndex + 1 >= len(self.route) :
			return None
		else :
			return self.route[self.routeIndex + 1]

	def getPrevSwitch(self) :
		if self.routeIndex - 1 < 0 :
			return None
		else :
			return self.route[self.routeIndex - 1]

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

	def reverse(self) :
		self.route.reverse()
		self.routeTags.reverse()



