class TopologyCreator(object):
	" Creates custom Topology Configuration Files "

	def __init__(self, type, k, tenantName, hostCapacity=10):
		self.name = tenantName
		self.hostCapacity = hostCapacity
		if type == "ring" :
			# Make a ring topology of k switches. 
			self.ring(k)
		elif type == "tree" :
			# Make a tree topology of depth k.
			self.tree(k)

	def ring(self, size) :
		# Make a ring topology of k switches. 

		f1 = open("./pox/virtnetsim/" + self.name + "/" + self.name + "-switches", 'w')

		for i in range(size) :
			f1.write("s" + str(i) + " " + str(1024) + "\n")

		f2 = open("./pox/virtnetsim/" + self.name +  "/" + self.name + "-links", 'w')

		for i in range(size) :
			f2.write("s" + str(i) + " s" + str((i + 1) % size) + " " + str(10) + "\n")

		
		f3 = open("./pox/virtnetsim/" + self.name +  "/" + self.name +  "-hosts", 'w')

		for i in range(size) :
			f3.write("h" + str(i) + " vsub" + str(i) + " " + str(self.hostCapacity) + " 10.0." + str(i) + ".5 s" + str(i) + "\n")


	def tree(self, depth) :
		# Make a ring topology of k switches. 

		f1 = open("./pox/virtnetsim/" + self.name + "/" + self.name + "-switches", 'w')

		for i in range(pow(2, depth) - 1):
			f1.write("s" + str(i) + " " + str(1024) + "\n")


		f2 = open("./pox/virtnetsim/" + self.name +  "/" + self.name + "-links", 'w')
		for i in range(pow(2, depth - 1) - 1) :
			f2.write("s" + str(i) + " s" + str(2 * i + 1) + " " + str(10) + "\n")
			f2.write("s" + str(i) + " s" + str(2 * i + 2) + " " + str(10) + "\n")

		
		f3 = open("./pox/virtnetsim/" + self.name +  "/" + self.name +  "-hosts", 'w')

		for i in range(pow(2, depth - 1) - 1, pow(2, depth) - 1):
			f3.write("h" + str(i) + " vsub" + str(i) + " " + str(self.hostCapacity) + " 10.0." + str(i) + ".5 s" + str(i) + "\n")


ring = TopologyCreator("tree", 4, "tenant3", 20)

		