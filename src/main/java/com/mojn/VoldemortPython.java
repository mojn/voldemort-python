package com.mojn;

import py4j.GatewayServer;
import voldemort.VoldemortException;
import voldemort.client.ClientConfig;
import voldemort.client.CachingStoreClientFactory;
import voldemort.client.SocketStoreClientFactory;
import voldemort.client.StoreClientFactory;
import voldemort.versioning.VectorClock;
import voldemort.versioning.Versioned;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.Arrays;

public class VoldemortPython {

	StoreClientFactory factory;
	
	public VoldemortPython(String... bootstrapUrls) {
		ClientConfig cc = new ClientConfig();
		cc.setBootstrapUrls(bootstrapUrls);
        factory = new CachingStoreClientFactory(new SocketStoreClientFactory(cc));
	}
	
	public boolean isAlive() {
		return true;
	}

	private Object[] tryGet(String storeName, String key) {
    	Versioned<Object> resultObject = factory.getStoreClient(storeName).get(key);
    	if (resultObject != null) {
    		Object value = resultObject.getValue();
    		VectorClock clock = (VectorClock)resultObject.getVersion();
    		String version = Arrays.toString(clock.toBytes());
	    	return new Object[]{ value, version };
    	} else {
    		return null;
    	}
	}
	
    public Object[] get(String storeName, String key) {
    	try {
    		return tryGet(storeName, key);
    	} catch (VoldemortException ex) {
    		String message = ex.getMessage();
    		if (message == null) {
    			message = ex.toString();
    		}
    		System.out.println("Retrying after voldemort error: " + message);
    	}
    	try {
    		return tryGet(storeName, key);
    	} catch (VoldemortException ex) {
    		String message = ex.getMessage();
    		if (message == null) {
    			message = ex.toString();
    		}
    		System.out.println("Persistent voldemort error: " + message);
    		return null;
    	}
    }
    
    public static void main(String[] args) {
        try {
	        GatewayServer gatewayServer = new GatewayServer(new VoldemortPython(Arrays.copyOfRange(args, 1, args.length)), 0);
	        System.out.println("Gateway starting");
	        gatewayServer.start();
	        int listening_port = gatewayServer.getListeningPort();
	        System.out.println("GatewayPort-" + listening_port);
	        /* Exit on EOF or broken pipe. This ensures that the server dies if its parent program dies. */
	        BufferedReader stdin = new BufferedReader(new InputStreamReader(System.in));
        	stdin.readLine();
            System.out.println("Stdin closed - exiting");
        	System.exit(0);
        } catch (Exception ex) {
    		String message = ex.getMessage();
    		if (message == null) {
    			message = ex.toString();
    		}
            System.out.println("IOException - exiting: " + message);
        	System.exit(1);
        }
    }

}
