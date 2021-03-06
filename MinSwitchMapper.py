###################################
#Create the host mapping. As a heuristic, we try to minimise the number of switches 
#involved in a mapping a virtual topology. A basis of this heuristic is that we can divide the
#physical topology into disjoint components, the rules of each topology will be contained 
#in its component. 
#
# Each Mapper will take as input a Physical Topology and Virtual Topology 
# and create the mapping files needed for the NetworkMapping object.  
###################################

import copy
import random
from VNSTopology import *
from NetworkMapping import NetworkDatabase, TenantDatabase

class MinSwitchMapper(object) :
	def __init__(self, phyTopo, virtTopo, netDatabase, tenantDatabase) :
		self.physicalTopology = phyTopo
		self.mappingTopology = copy.deepcopy(phyTopo) # Creating a deep copy of the physical topology for mapping purposes.
		self.virtualTopology = virtTopo

		self.tenantDatabase = tenantDatabase
		self.netDatabase = netDatabase

		self.switchMap = dict()

	def findTotalCapacity(self, hosts) :
		totalcap = 0
		for hname in hosts.iterkeys(): 
			totalcap += hosts[hname].capacityLeft()
		return totalcap

	def mapLargestPhysicalHost(self, hosts, vhost) :
		size = 0
		largestHost = None
		for host in hosts :
			if host.capacityLeft() > size :
				size = host.capacityLeft()
				largestHost = host
		
		if size < vhost.capacity() :
			return False
		else :
			# map vhost on largestHost.
			largestHost.mapVM(vhost)
			return True


	def getLargestUnmappedVirtualHost(self, vhosts) :
		size = 0
		largestHost = None
		for hname in vhosts.iterkeys(): 
			vhost = vhosts[hname]
			if vhost.capacity() > size and not vhost.isMapped():
				size = vhost.capacityLeft()
				largestHost = vhost

		return largestHost

	def commitMapping(self, hosts) :
		""" Commit the pending mappings on each of the hosts. """

		unusedHosts = []
		for host in hosts :
			host.commitMappedVM()

			# Commit Mappings on the physical topology.
			vms = host.getMappedVMs()

			phyhost = self.physicalTopology.getHost(host.getName())
			vmCount = 0
			for vm in vms:
				if vm.getTenantID() == self.virtualTopology.getTenantID() :
					phyhost.mapVM(vm)
					vmCount += 1


			if vmCount == 0:
				# Host does not have any vms committed of this virtual topo. Remove from hosts.
				unusedHosts.append(host)
				
			else :
				phyhost.commitMappedVM()  # Changed the physical topology mapping.

		for h in unusedHosts :
			hosts.remove(h)


	def resetMapping(self, hosts) :
		""" Reset the pending mappings on each of the hosts. """
		for host in hosts :
			host.resetMappedVM()

	def mapHosts(self, vhosts, hosts) :
		""" Function maps vhosts(dict) on  hosts(list) in a greedy fashion """

		countMappedHosts = 0

		while not countMappedHosts == len(vhosts):
			vhost = self.getLargestUnmappedVirtualHost(vhosts)
			if vhost == None :
				break
			ret = self.mapLargestPhysicalHost(hosts, vhost)
			if ret == False :
				self.resetMapping(hosts)
				return False
			else :
				countMappedHosts += 1

		self.commitMapping(hosts)
		return True

	def displayMapping(self, hosts) :
		for host in hosts :
			host.displayMapping() 

	def writeMappingToFile(self, hosts, vhosts) :
		# Host Map

		f1 = open("./pox/virtnetsim/" + self.virtualTopology.getName() + "-map/host-maps", 'w')
		for host in hosts :
			vms = host.getMappedVMs()
			sw = host.getSwitch()
			
			for vm in vms :
				if vm.getTenantID() == self.virtualTopology.getTenantID() : 
					vm.getSwitch().setMapped()
					f1.write(vm.getIP() + " " + self.netDatabase.getSwitchKey(vm.getSwitch().getName()).split("-")[1] + " " + self.netDatabase.getSwitchKey(sw.getName()).split("-")[1] +"\n")


		# switch Map. Distribute switches randomly across the hosts.
		f2 = open("./pox/virtnetsim/" + self.virtualTopology.getName() + "-map/switch-maps", 'w')
		switches = self.virtualTopology.getSwitches() 
		
		for sw in switches.itervalues() :
			if not sw.isMapped() :
				n = random.randint(0, len(hosts) - 1)
				hostsw = hosts[n].getSwitch()
				f2.write(self.netDatabase.getSwitchKey(sw.getName()).split("-")[1] + " " + self.netDatabase.getSwitchKey(hostsw.getName()).split("-")[1] + "\n")




	def findHostMapping(self) :
		" Map virtual hosts to physical hosts "

		vhosts = self.virtualTopology.getHosts()
		phosts = self.mappingTopology.getHosts()

		vhostsCapacity = self.findTotalCapacity(vhosts)

		if vhostsCapacity > self.findTotalCapacity(phosts) :
			# Not enough capacity.
			print "Insufficient capacity"
		
		else :
			# Sufficient Capacity. Find a mapping.
			swlist1 = []
			swlist2 = []
			#Percolate host capacity to its switches. 
			for hname in phosts.iterkeys() :
				host = phosts[hname]
				sw = host.getSwitch()
				
				if sw.getName() in self.switchMap :
					self.switchMap[sw.getName()].append(host)
				else :	
					self.switchMap[sw.getName()] =  [host]
				if host.capacityLeft() > vhostsCapacity :
					for vhost in vhosts.itervalues() :
						host.mapVM(vhost)
					host.commitMappedVM()
					self.writeMappingToFile([host], vhosts)
					return True
				
				swlist1.append(sw.getName())

			# Start the percolation rounds.
			round = 0
			isMappedFlag = False

			for round in range(2):
				while not len(swlist1) == 0:
					sw = self.mappingTopology.getSwitch(swlist1.pop())

					# Check Capacity.
					totalcap = 0

					hosts = self.switchMap[sw.getName()]
					for h in hosts :
						totalcap += h.capacityLeft()

					if totalcap >= vhostsCapacity :
						ret = self.mapHosts(vhosts, hosts)
						if ret == True:
							self.writeMappingToFile(hosts, vhosts)
							return

					# Update neighbours and put neighbours in list
					neighbours = sw.getNeighbours()
					for n in neighbours :
						if n.getName() in self.switchMap :
							# Update host info.
							for h in hosts :
								nhosts = self.switchMap[n.getName()]
								if not h in nhosts :
									nhosts.append(h)
									swlist2.append(n.getName())
									
						else :
							self.switchMap[n.getName()] = self.switchMap[sw.getName()]
							swlist2.append(n.getName())

				swlist1 = swlist2
				swlist2 = []
				

