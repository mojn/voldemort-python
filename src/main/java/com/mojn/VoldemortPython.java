package com.mojn;

import py4j.GatewayServer;

import voldemort.client.ClientConfig;
import voldemort.client.CachingStoreClientFactory;
import voldemort.client.SocketStoreClientFactory;
import voldemort.client.StoreClient;
import voldemort.client.StoreClientFactory;

import java.util.Arrays;

public class VoldemortPython {

	StoreClientFactory factory;
	
	public VoldemortPython(String... bootstrapUrls) {
		ClientConfig cc = new ClientConfig();
		cc.setBootstrapUrls(bootstrapUrls);
        factory = new CachingStoreClientFactory(new SocketStoreClientFactory(cc));
	}
	
    public StoreClient<String, Object> getClient(String storeName) {
        return factory.getStoreClient(storeName);
    }

    public void close() {
    	factory.close();
    }
    
    public static void main(String[] args) {
        GatewayServer gatewayServer = new GatewayServer(new VoldemortPython(Arrays.copyOfRange(args, 1, args.length)), Integer.parseInt(args[0]));
        gatewayServer.start();
    }

}
