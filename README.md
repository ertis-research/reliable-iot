# reliable-iot

***UNDER DEVELOPMENT***

From the Edge to the Cloud: enabling reliable IoT applications


This Project focuses on the application of fault-tolerance techniques for IoT systems
on a cloud-fog architecture.

![Screenshot from 2019-05-21 16-55-39](https://user-images.githubusercontent.com/16557115/58107001-4fec6680-7be9-11e9-8641-d1d5f5df4c95.png)

Notes:
- When deploying all modules to Docker Swarm, use de following command: **docker stack deploy -c docker-compose-all.yml IOT**.

The name **IOT** it's important because the **IoT_Register** module will try to deploy dynamically a new Docker container to the network **IOT_default**.
