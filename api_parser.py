import time, csv

from multiprocessing import Pool

from index_parser import parse_jdk_modules
from module_parser import parse_jdk_module
from package_parser import parse_jdk_package

# TODO: move to utils
def _write_to_csv_file(filename, data_list):
    with open(filename, mode='w') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for line in data_list:
            writer.writerow(line)

# parse index page
start_time = time.time()
modules = parse_jdk_modules(['java']) # result is [ java.base, link, description ]

# parse each module page
modules_parameters = [(module, []) for module in modules]
with Pool(4) as p:
    # result is [ [java.base, link, description, java.io, link, description] ]
    module_packages_list = list(p.starmap(parse_jdk_module, modules_parameters))

# TODO: paralellize
# parse each package page
final_list = []
for module_packages in module_packages_list:
    # list [ java.base, link, descr, java.io, link, descr ]
    for module_package in module_packages:
        print(module_package[0], '->', module_package[3])
        # list [ java.base, link, descr, java.io, link, descr, type, Serializable, link descr ]
        module_package_type = parse_jdk_package(module_package)
        final_list += module_package_type
    
elapsed_time = time.time() - start_time
print(elapsed_time)

print('Saving to file...') 
_write_to_csv_file('api_parsed.csv', final_list)
print('Done')