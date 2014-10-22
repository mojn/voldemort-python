package com.mojn;

import py4j.GatewayServer;
import voldemort.client.ClientConfig;
import voldemort.client.CachingStoreClientFactory;
import voldemort.client.SocketStoreClientFactory;
import voldemort.client.StoreClientFactory;
import voldemort.versioning.VectorClock;
import voldemort.versioning.Versioned;

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
	
    public Object[] get(String storeName, String key) {
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
    
    public static void main(String[] args) {
        GatewayServer gatewayServer = new GatewayServer(new VoldemortPython(Arrays.copyOfRange(args, 1, args.length)), Integer.parseInt(args[0]));
        System.out.println("Gateway starting");
        gatewayServer.start();
    }

}
