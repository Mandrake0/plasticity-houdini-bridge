from .client import PlasticityClient
#from .hou_handler import SceneHandler

#handler = SceneHandler()
#plasticity_client = PlasticityClient(handler)


def plasticity_client(handler):
    return PlasticityClient(handler)