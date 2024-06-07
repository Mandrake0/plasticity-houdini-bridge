# Analyse the Threading Error with Hython
import hou


g = hou.node('/obj').createNode('geo')
p = g.createNode('Plasticity')

p.parm("Connect").pressButton()