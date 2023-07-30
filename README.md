# RestApiDEE

## Table of Contents
1. [Introduction](#introduction)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Set Up](#set-up)
5. [Usage](#usage)


## Introduction
The RestApi is a ground module that is charged with the comunication between the frontend aplications (Dashboard, FlutterFrontEnd) and the database (mongoDB).
This module contains 2 parts the API and the database (located in dump/DEE).

## Requirements
Before starting with the installation, make sure you have the following software installed on your system:

- Python 3.7
- MongoDB Community Edition
- MongoDB Database Tools
- MongoDB Compass (optional, but recommended for easier database management)
- PyCharm (or any preferred IDE)

The following modules are required for full functionality:

- Dashboard/FlutterFrontEnd [![DroneEngineeringEcosystem Badge](https://img.shields.io/badge/DEE-Dashboard-brightgreen.svg)](https://github.com/dronsEETAC/DashboardDEE)
- AutopilotService [![DroneEngineeringEcosystem Badge](https://img.shields.io/badge/DEE-AutopilotService-brightgreen.svg)](https://github.com/dronsEETAC/DroneAutopilotDEE)


## Installation
To run and contribute, clone this repository to your local machine and install the requirements. You can install MongoDB and MongoDB Database Tools from the following links:

- [Install MongoDB](https://www.mongodb.com/docs/manual/administration/install-community/)
- [Install MongoDB Database Tools](https://www.mongodb.com/docs/database-tools/)

To make it easier to work with the database, it is also recommended to install [MongoDB Compass](https://www.mongodb.com/products/compass).

## Set Up
The RestApi service can be run in simulation mode. 
To run the service you must edit the run/debug configuration in PyCharm, as shown in the image, in order to pass the required arguments to the script. 
You will need to change from Script path to Module name and input _uvicorn_, as well as adding the following parameters: _main:app --reload_.
![image](https://github.com/Frixon21/RestApiDEE/assets/72676967/e34bd344-ee58-4d86-b2ba-dc65c5d5c117)
![image](https://github.com/Frixon21/RestApiDEE/assets/72676967/d8c9e3e4-b2a8-4df5-be1f-376d070fe58d)


To restore the database you will have to run the following command from the mian RestApi dirrectory. Keep in mind that if you did not add the mongoDB Tools to your path you will have to copy them into your folder. 
```
mongorestore dump/
```

## Usage 
Once the service has started, navigate to http://127.0.0.1:8000 to see and try all the different API endpoints.
![image](https://github.com/Frixon21/RestApiDEE/assets/72676967/a9c89fcc-6552-4918-9f06-bdd76c7cfa29)

For the endpoints __/connect__, __/disconnect__, and __/connection_status__, you will need to have the Autopilot service running along with the MQTT brokers, and Mission Planner.
If you need more information about that, it can all be found in the main repo of the Drone Engineering Ecosystem.
[![DroneEngineeringEcosystem Badge](https://img.shields.io/badge/DEE-MainRepo-brightgreen.svg)](https://github.com/dronsEETAC/DroneEngineeringEcosystemDEE)



