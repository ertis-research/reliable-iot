# reliable-iot

## ***UNDER DEVELOPMENT***

From the Edge to the Cloud: enabling reliable IoT applications


This Project focuses on the application of fault-tolerance techniques for IoT systems
on a cloud-fog architecture.

![Screenshot from 2019-05-21 16-55-39](https://user-images.githubusercontent.com/16557115/58107001-4fec6680-7be9-11e9-8641-d1d5f5df4c95.png)

Notes:
- When deploying all modules to Docker Swarm, use de following command: 
```
docker stack deploy -c docker-compose-all.yml reliableiot
```

Before deploying all modules on Swarm, the following Docker images must be built: *iotdatabase, iotregister, iotweb, iotshadowapplications, leshanondockers, leshanmonitor, iotrecovery.* The other images: *mongo, zookeeper, kafka*, are directly pulled from Docker hub.

Building commands:
  - ```docker build --tag=iotdatabase .```
  - ```docker build --tag=iotregister .```
  - ```docker build --tag=iotweb .```
  - ```docker build --tag=iotshadowapp .```
  - ```docker build --tag=leshanondockers .```
  - ```docker build --tag=leshanmonitor .```
  - ```docker build --tag=iotrecovery .```

(Mind the final dot in the building commands!)


Docker hub downloaded images:
  - https://hub.docker.com/_/mongo
  - https://hub.docker.com/_/zookeeper
  - https://hub.docker.com/r/wurstmeister/kafka



The docker compose file is the following:
>It may change.


```
version: '3.2'

services:
  mongo_db: 
    image: mongo        
    ports:
      - "27018:27017"
#----------------------------------------
  mongoapi:
    image: iotdatabase:latest
    deploy:
        replicas: 3
        restart_policy:
            condition: on-failure
    ports:
      - "8000:80"
#----------------------------------------
  iotregister:
    image: iotregister:latest
    build: .
    deploy:
      replicas: 3
    ports:
      - "8001:80"
    volumes: 
      - type: bind
        source: /var/run/docker.sock
        target: /var/run/docker.sock
        
#----------------------------------------
  iotweb:
    image: iotweb:latest
    deploy:
      replicas: 3
      restart_policy:
          condition: on-failure
    ports:
      - "8002:80"

#----------------------------------------
  iotshadowapplications:
    image: iotshadowapp:latest
    deploy:
      replicas: 3
      restart_policy:
          condition: on-failure
    ports:
      - "8003:80"

#---------------------------------------
  iotrecovery:
    image: iotrecovery:latest
    deploy:
      replicas: 3
      restart_policy:
          condition: on-failure
    ports:
      - "8004:80"


#--------------------LESHAN-SERVER-CLIENT------------------
  leshan:
    image: leshanondockers:latest
    deploy:
      replicas: 1
      restart_policy:
          condition: on-failure
    ports:
      - target: 8080
        published: 8080
        protocol: tcp

      - target: 5683
        published: 5683
        protocol: udp
#--------------KAFKA-ZOOKEEPER-----------
  zookeeper1:
    image: zookeeper:latest
    restart: always
    ports:
      - 2181:2181
    environment:
      ZOO_MY_ID: 1
      ZOO_SERVERS: server.1=0.0.0.0:2888:3888;2181 server.2=zookeeper2:2888:3888;2181

  zookeeper2:
    image: zookeeper:latest
    restart: always
    ports:
      - 2182:2181
    environment:
      ZOO_MY_ID: 2
      ZOO_SERVERS: server.1=zookeeper1:2888:3888;2181 server.2=0.0.0.0:2888:3888;2181

   
  kafka1:
    image: wurstmeister/kafka:2.12-2.2.1
    ports:
      - target: 9094
        published: 9094
        protocol: tcp
        mode: host
    environment:
      HOSTNAME_COMMAND: "hostname"
      KAFKA_ZOOKEEPER_CONNECT: zookeeper1:2181, zookeeper2:2181
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: INSIDE:PLAINTEXT,OUTSIDE:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: INSIDE://:9092,OUTSIDE://localhost:9094
      KAFKA_LISTENERS: INSIDE://:9092,OUTSIDE://:9094
      KAFKA_INTER_BROKER_LISTENER_NAME: INSIDE
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECTION_TIMEOUT_MS: 36000
      KAFKA_LOG_RETENTION_BYTES: -1
      KAFKA_LOG_RETENTION_DAYS: 2
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  kafka2:
    image: wurstmeister/kafka:2.12-2.2.1
    ports:
      - target: 9095
        published: 9095
        protocol: tcp
        mode: host
    environment:
      HOSTNAME_COMMAND: "hostname"
      KAFKA_ZOOKEEPER_CONNECT: zookeeper1:2181, zookeeper2:2181
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: INSIDE:PLAINTEXT,OUTSIDE:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: INSIDE://:9092,OUTSIDE://localhost:9095
      KAFKA_LISTENERS: INSIDE://:9092,OUTSIDE://:9095
      KAFKA_INTER_BROKER_LISTENER_NAME: INSIDE
      KAFKA_BROKER_ID: 2
      KAFKA_ZOOKEEPER_CONNECTION_TIMEOUT_MS: 36000
      KAFKA_LOG_RETENTION_BYTES: -1
      KAFKA_LOG_RETENTION_DAYS: 2
      KAFKA_CREATE_TOPICS: "FailureTopic:2:2"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```
