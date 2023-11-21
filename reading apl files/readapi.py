import os 
from modelconfig import ModelConfig
mc = ModelConfig()
mc.read('davetest.ini')
mc['ADMS_SOURCE_DETAILS']['SrcPolEmissionRate'] = '1.7e+0'
mc.write('davetest3.apl')

