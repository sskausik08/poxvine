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
		for host in hosts :
			host.commitMappedVM()

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

	def findHostMapping(self) :
		" Map virtual hosts to physical hosts "

		vhosts = self.virtualTopology.getHosts()
		phosts = self.mappingTopology.getHosts()

		vhostsCapacity = self.findTotalCapacity(vhosts)

		if vhostsCapacity > self.findTotalCapacity(phosts) :
			print str(vhostsCapacity) + " " + str(self.findTotalCapacity(phosts))
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
					print "mapping possible on this host itself."
					for vhost in vhosts.itervalues() :
						host.mapVM(vhost)
					host.commitMappedVM()
					host.displayMapping()
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
						print "Mapping possible on " + sw.getName() + ":"
						for h in hosts :
							print h.getName(),

						ret = self.mapHosts(vhosts, hosts)
						if ret == True:
							print "mapping done"
							self.displayMapping(hosts)
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


			for swname in self.switchMap.iterkeys() :
				hosts = self.switchMap[swname]
				print "\n" + swname + ":"
				for h in hosts :
					print h.getName(),
				






				
















		



