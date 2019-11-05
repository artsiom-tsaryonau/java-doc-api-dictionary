import csv

from multiprocessing import Pool
from itertools import chain

from index_parser import parse_jdk_modules
from module_parser import parse_jdk_module
from package_parser import parse_jdk_package

# TODO: move to utils
def __write_to_csv_file(filename, module_package_list):
    with open(filename, mode='w') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for module_package_type_list in module_package_list:
            for module_package_type in module_package_type_list:
                writer.writerow(module_package_type)

# parse index page
modules = parse_jdk_modules(['java']) # result is [ java.base, link, description ]

# parse each module page
modules_parameters = [(module, []) for module in modules]
with Pool(4) as p:
    # result is [ [java.base, link, description, java.io, link, description] ]
    module_packages_list = list(p.starmap(parse_jdk_module, modules_parameters))

with Pool(4) as p:
    #  TODO: rework the way it returns lists
    #  [
    #    [ [ java.base ... java.lang .... Closeable ] [ java.base ... java.lang ... Closeable ] ],
    #    [ [ java.base ... java.lang.annotation ... Closeable ] [ java.base ... java.lang.annotation ... Closeable ] ]
    #  ]
    final_list = p.map(parse_jdk_package, chain.from_iterable(module_packages_list))
    
__write_to_csv_file('api_parsed.csv', final_list)