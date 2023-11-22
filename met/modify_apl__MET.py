from modelconfigIMC import ModelConfig
mc = ModelConfig()


#define a function that creates a lsit with desired intervals , same as the ones used with the met file 
min_value = 0
max_value = 10 
interval =  2


data = list(range(min_value, max_value +1, interval))

for x  in data : 
   mc['ADMS_PARAMETERS_MET']['MetDataFileWellFormedPath'] = '"C:directoryofmetfile/variable{}.MET"'.format(x)
   mc.write('directory'+'CXX_variable_' + str(x) +'.apl')

