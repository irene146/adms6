import os 
from modelconfig import ModelConfig
mc = ModelConfig()
mc.read('davetest.ini')

#define a function that writes values in desired intervals, creating a list at 


    
 mc['ADMS_SOURCE_DETAILS']['SrcPolEmissionRate'] = '1.7e+0'
mc.write('davetest1.apl')

