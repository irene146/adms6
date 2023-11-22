from modelconfig import ModelConfig
mc = ModelConfig()
mc.read('davetest.ini')

# define a function that creates a lsit with desired intervals 
min_value = 0
max_value = 10 
interval =  2

data = list(range(min_value, max_value +1, interval))


for x  in data : 
    mc['ADMS_SOURCE_DETAILS']['SrcPolEmissionRate'] = str(x)+'e+0'
    mc.write('CXX_variable_' + str(x) +'.apl')

