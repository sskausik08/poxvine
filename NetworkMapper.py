'''
Virtual Network Simulator POX Application.
Author : Kausik Subramanian
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
from NetworkMapping import Route 
from VNSTopology import Topology

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

		# Initialize Physical Topology.
		self.phyTopo = Topology("phy")

		#Temp
		self.routeAdded = False

		
	"""This event will be raised each time a switch will connect to the controller"""
	def _handle_ConnectionUp(self, event):
		
		# Use dpid to differentiate between switches (datapath-id)
		# Each switch has its own flow table. As we'll see in this 
		# example we need to write different rules in different tables.
		dpid = dpidToStr(event.dpid)
		
		switchName = ""
		for m in event.connection.features.ports:
			name = m.name.split("-")
			if switchName == "" :
				switchName = name[0]
				print switchName
			if not switchName == name[0] :
				log.debug("Some Error in mapping name from the OpenFlow Switch Up Message.")

		self.switchMap[switchName] = dpid
		self.switchConnections[switchName] = event.connection



	def findSwitchName(self, dpid) :
		for name in self.switchMap.iterkeys() :
			if self.switchMap[name] == dpid :
				return name

	def getSwitchMacAddr(self, sw) :
		if sw == None : 
			return None
		else : 
			dpid = self.switchMap[sw]
			mac = dpid.replace("-", ":")
			return mac

	def findOutputPort(self, curr, next, prev = None) :
		#curr and next are not adjacent. Find the next switch.
		sw = self.findNeighbour(src = curr, dst = next)
		if sw == prev :
			return of.OFPP_IN_PORT # send back on the input port.

		elif not self.adjacency[self.switchMap[curr]][self.switchMap[sw]] == None :
			return self.adjacency[self.switchMap[curr]][self.switchMap[sw]]
		
		else :	
			print "[ERROR] No edge present."
			return None


	def getSubnet(self, ip, subnetMask) :
		if ip == "10.0.0.5" or ip == "10.0.0.0":
			return "10.0.0.0"
		if ip == "10.1.0.5" or ip == "10.1.0.0":
			return "10.1.0.0"
		if ip == "10.2.0.5" or ip == "10.2.0.0":
			return "10.2.0.0"


	def findNeighbour(self, src, dst) :
		return self.phyTopo.getNeighbour(src, dst)


	def addForwardingRules(self, srcSubnet, dstSubnet, route) :
		"This function proactively adds the forwarding rules from srcSubnet to dstSubnet."

		currRouteTag = 2 # Start with 1. 

		# First switch
		sw = route.getFirstSwitch()
		sw_next = route.getNextRouteTagSwitch()

		print "Adding VLAN Tag rule for Switch " + sw
		self.installRouteTagRule(
			connection = self.switchConnections[sw], 
			srcip = srcSubnet, dstip = dstSubnet, 
			srcSw = sw, dstSw = sw_next, prevSw=None,
			vlanMatch = 0, vlanAction = 4,
			routeTagMatch = 0, routeTagAction = currRouteTag)

		
		sw = sw_next
		sw_prev = route.getPrevSwitch()

		while not route.isLastSwitch() : 
			sw_next = route.getNextRouteTagSwitch()

			print "Adding rule for Switch " + sw
			if route.getCurrentRouteTag() :
				self.installRouteTagRule(
					connection = self.switchConnections[sw], 
					srcip = srcSubnet, dstip = dstSubnet, 
					srcSw = sw, dstSw = sw_next, prevSw=sw_prev,
					vlanMatch = 4, vlanAction = 0 ,
					routeTagMatch = currRouteTag, routeTagAction = (currRouteTag + 1) ) 
				currRouteTag += 1

			sw = sw_next
			sw_prev = route.getPrevSwitch()


		# Last Switch. Strip VLAN
		print "Adding rule for Switch " +  sw

		self.installRouteTagRule(
			connection = self.switchConnections[sw], 
			srcip = srcSubnet, dstip = dstSubnet, 
			srcSw = sw, dstSw = None, prevSw = None,
			vlanMatch = 4 , vlanAction = -1,
			routeTagMatch = currRouteTag, routeTagAction = 0)
	

		# Add the required switch Tunnel rules.

		for src in self.switchMap.iterkeys():
			for dst in self.switchMap.iterkeys():
				if not src == dst :
					self.installSwitchTunnelRule(
						connection = self.switchConnections[src],
						srcSw = src, dstSw = dst)




	def getVlanId(self, tenantID, routeTag) :
		# A function of tenant ID and routeTag. 
		# 12 Bit VLAN ID: Most Significant 6 bits : tenantID, Least Significant 6 bits : routeTag
		return (tenantID * 64 + routeTag)

	def installRouteTagRule(self, connection, srcip, dstip, srcSw, dstSw, prevSw,
		vlanMatch = 0, vlanAction = 0, routeTagMatch = 0, routeTagAction = 0):
		msg = of.ofp_flow_mod()
		
		#Match 
		msg.match = of.ofp_match()
		msg.match.dl_type = ethernet.IP_TYPE
		msg.match.set_nw_src(IPAddr(self.getSubnet(srcip, 24)), 24)
		msg.match.set_nw_dst(IPAddr(self.getSubnet(dstip, 24)), 24)

		if not vlanMatch == 0 and not routeTagMatch == 0 : 
			msg.match.dl_vlan = self.getVlanId(vlanMatch, routeTagMatch)

		if vlanAction == -1 : 
			#Strip Vlan tag.
			msg.actions.append(of.ofp_action_strip_vlan())

		elif not vlanAction == 0 and not routeTagAction == 0: 
			# Need to set VLAN Tag for isolation of tenant traffic.
			msg.actions.append(of.ofp_action_vlan_vid(vlan_vid = self.getVlanId(vlanAction, routeTagAction))) 
		
		elif vlanAction == 0 and not routeTagAction == 0:
			msg.actions.append(of.ofp_action_vlan_vid(vlan_vid = self.getVlanId(vlanMatch, routeTagAction))) 
		
		if dstSw == None :
			outport = of.OFPP_FLOOD
		else :
			msg.actions.append(of.ofp_action_dl_addr.set_src(EthAddr(self.getSwitchMacAddr(dstSw))))
			outport = self.findOutputPort(curr=srcSw, next=dstSw, prev=prevSw)

		msg.actions.append(of.ofp_action_output(port = outport))
		connection.send(msg)

	def installSwitchTunnelRule(self, connection, srcSw, dstSw) :
		msg = of.ofp_flow_mod()

		#Match 
		msg.match = of.ofp_match()
		msg.match.dl_src = EthAddr(self.getSwitchMacAddr(dstSw))

		outport = self.findOutputPort(curr=srcSw, next=dstSw)
		if outport == None :
			print "NONE is here. Why?"
		msg.actions.append(of.ofp_action_output(port = outport))
		connection.send(msg)		



	def reactiveInstallRule(self, event, srcip, dstip, outport, vlan=0):
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

	def _handle_LinkEvent (self, event):
		l = event.link
		sw1 = dpid_to_str(l.dpid1)
		sw2 = dpid_to_str(l.dpid2)

		log.debug ("link %s[%d] <-> %s[%d]",
				   sw1, l.port1,
				   sw2, l.port2)

		self.adjacency[sw1][sw2] = int(l.port1)
		self.adjacency[sw2][sw1] = int(l.port2)

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

			
			if not vlan == 0 : 
				# Need to set VLAN Tag for isolation of tenant traffic.
				msg.actions.append(of.ofp_action_vlan_vid(vlan_vid = vlan)) 

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

  				route1 = Route()
  				route2 = Route()
  				route3 = Route()
  				route4 = Route()

  				if not self.routeAdded : 
	  				route1.addSrcSubnet("10.0.0.0", 24)
	  				route1.addDstSubnet("10.1.0.0", 24)
	  				route1.addNextSwitch("s10", True)
	  				route1.addNextSwitch("s1", False)
	  				route1.addNextSwitch("s2", False)
	  				route1.addNextSwitch("s3", False)
	  				route1.addNextSwitch("s4", True)
	  				route1.addNextSwitch("s3", True)
	  				route1.addNextSwitch("s4", False)
	  				route1.addNextSwitch("s20", True)
	  				"""
	  				route1.addNextSwitch("s3", False)
	  				route1.addNextSwitch("s2", False)
	  				route1.addNextSwitch("s1", True)
	  				route1.addNextSwitch("s2", False)
	  				route1.addNextSwitch("s3", False)
	  				route1.addNextSwitch("s4", False) """

					self.addForwardingRules(srcSubnet = "10.0.0.0" , dstSubnet = "10.1.0.0", 
					route = route1)


					route2.addSrcSubnet("10.1.0.0", 24)
	  				route2.addDstSubnet("10.0.0.0", 24)
	  				route2.addNextSwitch("s20", True)
	  				route2.addNextSwitch("s4", False)
	  				route2.addNextSwitch("s3", False)
	  				route2.addNextSwitch("s2", False)
	  				route2.addNextSwitch("s1", False)
	  				route2.addNextSwitch("s10", True)

	  				self.addForwardingRules(srcSubnet = "10.1.0.0" , dstSubnet = "10.0.0.0", 
					route = route2)

	  				route3.addSrcSubnet("10.0.0.0", 24)
	  				route3.addDstSubnet("10.2.0.0", 24)
	  				route3.addNextSwitch("s10", True)
	  				route3.addNextSwitch("s1", False)
	  				route3.addNextSwitch("s2", False)
	  				route3.addNextSwitch("s3", False)
	  				route3.addNextSwitch("s4", True)
	  				route3.addNextSwitch("s3", False)
	  				route3.addNextSwitch("s30", True)
	  				self.addForwardingRules(srcSubnet = "10.0.0.0" , dstSubnet = "10.2.0.0", 
					route = route3)

					route4.addSrcSubnet("10.2.0.0", 24)
	  				route4.addDstSubnet("10.0.0.0", 24)
	  				route4.addNextSwitch("s30", True)
	  				route4.addNextSwitch("s3", False)
	  				route4.addNextSwitch("s2", False)
	  				route4.addNextSwitch("s1", False)
	  				route4.addNextSwitch("s10", True)
	  				self.addForwardingRules(srcSubnet = "10.2.0.0" , dstSubnet = "10.0.0.0", 
					route = route4)

					self.routeAdded = True
	  				
  				#switch is event.dpid
  				"""
				sw = dpidToStr(event.dpid)
				swName = self.findSwitchName(sw)
				outport = self.findOutputPort(swName, ip.srcip, ip.dstip, 0, routeTag)
				install_fwdrule(event, ip.srcip, ip.dstip, outport, 5)
				"""
				


		handle_IP_packet(packet)

		# flood and install the flow table entry for the flood
		
		

def launch():
	# Run spanning tree so that we can deal with topologies with loops
	pox.openflow.discovery.launch()

	'''
	Starting the Topology Slicing module
	'''
	core.registerNew(NetworkMapper)
