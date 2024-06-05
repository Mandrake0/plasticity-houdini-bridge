# Plasticity Houdini Bridge

This is currently proof of Concept for a Plasticity Houdini Bridge.
It shouldn't be used in Production at any Time! 

The Code is not cleaned up and has internal Test's

**Works with Houdini 19.5.XXX**


## Note

There is a Bug with H20 in the python threading, that's the main reason why it doesn't work in H20.   


## Installation

1. Download Current Repository
2. Extract to preferd Directory
3. Move plasticity.json to the Houdini User Package Folder
4. Edit plasticity.json and set the Path
5. Start Houdini and check use the Node in a Geo Node

## Connect to Plasticity

### Plasticity

Enable the Plasticity Server in the Preferences and Restart.

![Plasticity](/help/images/plasticity_preferences_server.png)


### Houdini

Create Geometry SOP dive in and add Plasticity Node

![Houdini](/help/images/houdini_plasticity_parameters.png)

PRESS
* Connect
* Subscripte ALL
* List all
* Reload Mesh (When you update the Mesh just press this Button) 

