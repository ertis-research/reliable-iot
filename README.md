# From the Edge to the Cloud: Enabling Reliable IoT Applications

This project focuses on the application of fault-tolerance techniques for IoT devices in mission-critical applications
on a cloud-fog-edge architecture.

This project is described in this [paper](https://ieeexplore.ieee.org/abstract/document/8972812). If you find this repository useful for your research, please consider citing:
```
@inproceedings{martin2019,
  author={Mart{\'\i}n, Cristian and Garrido, Daniel and D{\'\i}az, Manuel and Rubio, Bartolom{\'e}},
  booktitle={2019 7th International Conference on Future Internet of Things and Cloud (FiCloud), August 26-28, Istanbul, Turkey},
  title={From the Edge to the Cloud: Enabling Reliable IoT Applications},
  year={2019},
  pages={17-22},
  keywords={Internet of Things, Fault Tolerance, Container Virtualisation, Edge, Fog, Apache Kafka},  
  doi={10.1109/FiCloud.2019.00011}
}
```


![Screenshot from 2019-05-21 16-55-39](https://user-images.githubusercontent.com/16557115/58107001-4fec6680-7be9-11e9-8641-d1d5f5df4c95.png)

This project requires a Docker Swarm cluster to deploy the system. Plese visit the [official page](https://docs.docker.com/engine/swarm/ )  for more information. 

## Deploy the system 

### On a Raspberry Pi Cluster
```
docker stack deploy -c docker-raspberry.yml reliableiot
```

### On AMD64
```
docker stack deploy -c docker-amd64.yml reliableiot
```

Once deployed, you will have access to the Reliable Web UI at http://localhost:8002/

## Build and deploy the system on a Linux Cluster 

Before deploying all modules on Docker Swarm, the following Docker images must be built: *iotdatabase, iotregister, iotweb, iotshadowapplications, leshanondockers, leshanmonitor, iotrecovery.* The other images: *mongo, zookeeper, kafka*, are directly pulled from Docker hub.

Building commands:
  - ```docker build --tag=iotdatabase .```
  - ```docker build --tag=iotregister .```
  - ```docker build --tag=iotweb .```
  - ```docker build --tag=iotshadowapp .```
  - ```docker build --tag=leshanondockers .```
  - ```docker build --tag=leshanmonitor .```
  - ```docker build --tag=iotrecovery .```

Then, deploy the cluster:
```
docker stack deploy -c docker-compose-all.yml reliableiot
```

## Docker Hub dependencies for Linux:
  - [Mongo](https://hub.docker.com/_/mongo) 
  - [Apache Zookeeper](https://hub.docker.com/_/zookeeper)  
  - [Apache Kafka](https://hub.docker.com/r/wurstmeister/kafka)
  
## Docker Hub dependencies for Raspberry:
  - [Mongo](https://hub.docker.com/r/webhippie/mongodb/) 
  - [Apache Zookeeper](https://hub.docker.com/_/zookeeper)  
  - [Apache Kafka](https://hub.docker.com/r/ertis/kafka) 

## Supported OSs:
- ARMv7 -- Raspberry Pi
- AMD64 --Linux

