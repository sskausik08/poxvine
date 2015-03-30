import java.io.*;
import java.net.*;
import java.util.*;


public class NetFeat {
	private enum NetFeatMode {
    	Client, Server
	}	

	// Constants : 
	int NetFeatServerPort = 4567;
	int NetFeatClientPort = 4576;
	int DatagramSize = 256;
	int MaxBufferTime = 5;

	String address;
	
	NetFeatMode mode;
	protected DatagramSocket socket = null;
	

	// Print Variable.
	boolean printVariable = false;

	public NetFeat() {
	}

	public static void main(String[] args) throws IOException {	
		new NetFeat().run(args);
	}

	public void run(String[] args) throws IOException {
		parseArguments(args);
		print();
		if(mode == NetFeatMode.Client) {
			runClient();
		}
		else {
			runServer();
		}
	}	

	public void parseArguments(String[] args) {
		try {
			for(int i = 0; i < args.length; ++i) {
				if(args[i].equals("-c")) {
					mode = NetFeatMode.Client;
					address = args[i+1];
				}
				else if(args[i].equals("-s")) {
					mode = NetFeatMode.Server;
				}
			}
		}
		catch(Exception e) {
			System.out.println("Error in parsing arguments.");
		}
	}

	public void print() {
	}

	public void runClient() throws SocketException, UnknownHostException, IOException {
		socket = new DatagramSocket(NetFeatClientPort);
		sendPackets();
	}

	public void sendPackets() throws UnknownHostException {
		int packetNum = 0;
		String randomStr = "";
		Random r = new Random();

		for(int i = 0; i < DatagramSize; ++i) {
			randomStr += (char) (r.nextInt(26) + 'a');
		}

		byte[] buf = new byte[DatagramSize];
        buf = randomStr.getBytes();
        InetAddress server = InetAddress.getByName(address);
   	    DatagramPacket packet = new DatagramPacket(buf, buf.length, server, NetFeatServerPort);
        for (int i = 0; i < 10; ++i) { 
	        try {
	        	socket.send(packet);
	        } catch (IOException e) {}
	    }
	}

	public void runServer() throws IOException, SocketException {
		socket = new DatagramSocket(NetFeatServerPort);
		byte[] buf = new byte[DatagramSize];
        DatagramPacket packet = new DatagramPacket(buf, buf.length);
       	while(true) {
        	socket.receive(packet);
        	InetAddress addr = packet.getAddress();
        	if (!printVariable) {
        		System.out.println("Source IP Address is " + addr.getHostAddress()); 
        		printVariable = true;
        	}
        }
	}
}

	