"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.

Running : 
sudo mn --custom PhysicalTopologyCreation.py  --topo PhyTopo --controller=remote,ip=192.168.0.103 --link=tc

Host IP : 
setIP()
"""

from mininet.topo import Topo
from mininet.link import TCLink

class PhyTopo( Topo ):
	"Create Physical Topology based on specifications."

	def __init__( self ):
		"Create physical topo."

		# Initialize topology
		Topo.__init__( self )

		# Add hosts
		leftHost = self.addHost( 'v1', ip="10.0.0.5", prefixLen=24)
		rightHost = self.addHost( 'v2', ip="10.1.0.5", prefixLen=24)
		midHost = self.addHost( 'v3', ip="10.2.0.5", prefixLen=24)

		#Add switches
		f2 = open("phy/phy-switches", 'r')
		switch_desc = f2.readlines()
		switch_hash = dict()

		for line in switch_desc:
			lineArr = line.split()        
			switch_hash[lineArr[0]] = self.addSwitch(lineArr[0])

		switch_hash['s10'] = self.addSwitch('s10')
		switch_hash['s20'] = self.addSwitch('s20')
		switch_hash['s30'] = self.addSwitch('s30')


		#Create the links between switches.
		f3 = open("phy/phy-links", 'r')
		link_desc = f3.readlines()


		#Add Links.
		for line in link_desc:
			lineArr = line.split()
			self.addLink( switch_hash[lineArr[0]],  switch_hash[lineArr[1]], bw= int(lineArr[2])) 

		self.addLink( switch_hash['s1'], switch_hash['s10'], bw=10) 
		self.addLink( switch_hash['s4'], switch_hash['s20'], bw=10)
		self.addLink( switch_hash['s3'], switch_hash['s30'], bw=10)

		self.addLink( switch_hash['s10'], leftHost, bw=10) 
		self.addLink( switch_hash['s20'], rightHost, bw=10)
		self.addLink( switch_hash['s30'], midHost, bw=10)



		
		


topos = { 'PhyTopo': ( lambda: PhyTopo() ) }
