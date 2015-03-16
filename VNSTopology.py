import heapq

class Topology(object):
	"Class for a Topology"
	def __init__(self, name="topo-0"):
		self.name = name
		self.racks = []

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



