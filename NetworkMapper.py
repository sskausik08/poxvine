'''
Coursera:
- Software Defined Networking (SDN) course
-- Network Virtualization

Professor: Nick Feamster
Teaching Assistant: Arpit Gupta
'''

from pox.core import core
from collections import defaultdict

import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
import pox.openflow.discovery
import pox.openflow.spanning_tree
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.vlan import vlan
from pox.lib.packet.ipv4 import ipv4 
from pox.lib.revent import *
from pox.lib.util import dpid_to_str
from pox.lib.util import dpidToStr

from pox.lib.addresses import IPAddr, EthAddr
from collections import namedtuple
import os 

log = core.getLogger()


class NetworkMapper (EventMixin):

	def __init__(self):
		self.listenTo(core.openflow)
		core.openflow_discovery.addListeners(self)
		log.debug("Enabling NetworkMapper Module")

		# Adjacency map.  [sw1][sw2] -> port from sw1 to sw2
		self.adjacency = defaultdict(lambda:defaultdict(lambda:None))
		
		self.switchMap = dict()
		self.switchConnections = dict()

		
	"""This event will be raised each time a switch will connect to the controller"""
	def _handle_ConnectionUp(self, event):
		
		# Use dpid to differentiate between switches (datapath-id)
		# Each switch has its own flow table. As we'll see in this 
		# example we need to write different rules in different tables.
		dpid = dpidToStr(event.dpid)
		log.debug("Switch %s has come up.", dpid)
		
		switchName = ""
		for m in event.connection.features.ports:
			name = m.name.split("-")
			if switchName == "" :
				switchName = name[0]
			if not switchName == name[0] :
				log.debug("Some Error in mapping name from the OpenFlow Switch Up Message.")

		self.switchMap[switchName] = dpid
		self.switchConnections[switchName] = event.connection


	def findSwitchName(self, dpid) :
		for name in self.switchMap.iterkeys() :
			if self.switchMap[name] == dpid :
				return name

	def findOutputPort(self, swName, srcip="0.0.0.0", dstip="0.0.0.0", tenantID = 0, routeTag = 0) :
		neighbour = ""
		if swName == "s1" and srcip == "10.0.0.5" and dstip == "10.1.0.5":
			neighbour = "s2"
		if swName == "s2" and srcip == "10.0.0.5" and dstip == "10.1.0.5":
			neighbour = "s3"
		if swName == "s3" and srcip == "10.0.0.5" and dstip == "10.1.0.5":
			neighbour = "s4"
		if swName == "s4" and srcip == "10.0.0.5" and dstip == "10.1.0.5":
			return of.OFPP_FLOOD
		if swName == "s4" and srcip == "10.1.0.5" and dstip == "10.0.0.5":
			neighbour = "s3"
		if swName == "s3" and srcip == "10.1.0.5" and dstip == "10.0.0.5":
			neighbour = "s2"
		if swName == "s2" and srcip == "10.1.0.5" and dstip == "10.0.0.5":
			neighbour = "s1"
		if swName == "s1" and srcip == "10.1.0.5" and dstip == "10.0.0.5":
			return of.OFPP_FLOOD

		return int(self.adjacency[self.switchMap[swName]][self.switchMap[neighbour]])

	def getSubnet(self, ip, subnetMask) :
		if ip == "10.0.0.5" :
			return "10.0.0.0"
		if ip == "10.1.0.5" :
			return "10.1.0.5"

	def _handle_LinkEvent (self, event):
		l = event.link
		sw1 = dpid_to_str(l.dpid1)
		sw2 = dpid_to_str(l.dpid2)

		log.debug ("link %s[%d] <-> %s[%d]",
				   sw1, l.port1,
				   sw2, l.port2)

		self.adjacency[sw1][sw2] = l.port1
		self.adjacency[sw2][sw1] = l.port2

	def _handle_PacketIn (self, event):
		"""
		Handle packet in messages from the switch.
		"""
		packet = event.parsed

		def install_fwdrule(event,srcip,dstip,outport,vlan=0):
			msg = of.ofp_flow_mod()
			
			#Match 
			msg.match = of.ofp_match()
			msg.match.dl_type = ethernet.IP_TYPE
			msg.match.set_nw_src(IPAddr(self.getSubnet(srcip, 24)), 24)
			msg.match.set_nw_dst(IPAddr(self.getSubnet(dstip, 24)), 24)

			"""
			if not vlan == 0 : 
				# Need to set VLAN Tag for isolation of tenant traffic.
				msg.actions.append(of.ofp_action_vlan_vid(vlan_vid = vlan)) """

			msg.actions.append(of.ofp_action_output(port = outport))

			msg.data = event.ofp
			msg.in_port = event.port
			event.connection.send(msg)

		def installFloodRule(event,packet,outport,vlan=0):
			msg = of.ofp_flow_mod()
			
			#Match 
			msg.match = of.ofp_match.from_packet(packet, event.port)		
			msg.actions.append(of.ofp_action_output(port = outport))
			
			if not vlan == 0 : 
				# Need to set VLAN Tag for isolation of tenant traffic.
				msg.actions.append(of.ofp_action_vlan_vid(vlan_vid = vlan))


			msg.data = event.ofp
			msg.in_port = event.port
			event.connection.send(msg)
		
		def handle_IP_packet (packet):
			ip = packet.find('ipv4')
			if ip is None:
				# This packet isn't IP!
				print "packet type has no transport ports, flooding"
				installFloodRule(event,packet,of.OFPP_FLOOD)
				return

			else :
  				print "Source IP:", ip.srcip

  				vlanPacket = packet.find('ethernet')
  				routeTag = 0
  				if vlanPacket.type == ethernet.VLAN_TYPE :
  					print "Vlan header is there."
  					print packet.__str__()

  				#switch is event.dpid
				sw = dpidToStr(event.dpid)
				swName = self.findSwitchName(sw)
				outport = self.findOutputPort(swName, ip.srcip, ip.dstip, 0, routeTag)
				install_fwdrule(event, ip.srcip, ip.dstip, outport, 1)


		handle_IP_packet(packet)

		# flood and install the flow table entry for the flood
		
		

def launch():
	# Run spanning tree so that we can deal with topologies with loops
	pox.openflow.discovery.launch()
	pox.openflow.spanning_tree.launch()

	'''
	Starting the Topology Slicing module
	'''
	core.registerNew(NetworkMapper)
