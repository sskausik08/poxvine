POXVine

Kausik Subramanian, IIT Bombay
Bachelor Thesis Project

Guide : Purushottam Kulkarni and Umesh Bellur


System Setup : 
The POXVine system consists of two components, the POX controller and the mininet infrastructure. The POX controller can be local or remote to the mininet infrastructure. 

You can get the mininet VM here : http://mininet.org/vm-setup-notes/


Instructions to run :

POX controller : 
1. Download the POX code repository from https://github.com/noxrepo/pox
2. Download the POXVine repository.
3. Copy the POXVine folder in the 'pox' directory in the POX code repository [Inside the 'pox' directory are the different pox modules like forwarding, topology etc. We use POXVine as a library]
4. From the source of POX code repository, run 
	$ ./pox.py $$.NetworkMapper
	where $$ = name of POXVine code folder which you copied in the 'pox' directory.

This will start the POX controller. 


Mininet Infrastructure : 
1. Running the POX Controller will create the required mininet files in the directory 
'virtnetsim-mininet-files' in the POXVine source folder. This folder will contain a PhysicalTopologyCreation.py and various configuration files of the form 'phy-*' 
2. If the POX controller is running local to the mininet VM, cd into the folder and run
	$ sudo mn --custom PhysicalTopologyCreation.py  --topo PhyTopo --controller=remote,ip=127.0.0.1 --link=tc

3. If the POX controller is remote, then copy this folder to the mininet VM. 
   In the VM, cd to the folder and run 
   	$ sudo mn --custom PhysicalTopologyCreation.py  --topo PhyTopo --controller=remote,ip=<IP of remote controller> --link=tc

4. This will open a mininet console which you can use to perform operations on the mininet switches and hosts. 

