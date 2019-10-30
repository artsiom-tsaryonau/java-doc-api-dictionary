from bs4 import BeautifulSoup
from multiprocessing import Pool
import requests, csv, re

base_url = 'https://docs.oracle.com/en/java/javase/11/docs/api/'
modules_file = 'java11_modules.csv'

# indirect exports might be convenient if we were to build 
# true graph of modules and its packages

# hierarchy: 
# module -> 
#   package(exports, indirect exports)
#       interface, class, enum, exception
#   service(provides, uses)
#   modules(requires, indirect requires)

# parses main index.html page
def parse_main_doc():
    url = base_url + 'index.html'
    html = requests.get(url).text
    soup = BeautifulSoup(html, features='html.parser')
    modules_dict = {} # modules for further processing
    with open(modules_file, mode='w') as modules_export:
        modules_writer = csv.writer(modules_export, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        overviewtable = soup.body.find('table', attrs={'class':'overviewSummary'})
        modules = overviewtable.find('tbody')
        for row in modules.find_all('tr'):
            header = row.find('th')
            module_name = header.text
            module_link = base_url + header.find('a').get('href')
            description_raw = row.find('td').text
            description = re.sub(r'\n+', '', description_raw)
        
            if module_name.startswith('java'):
                row = [module_name, module_link, description]
                modules_writer.writerow(row)
                modules_dict[module_name] = module_link
    return modules_dict
    
def parse_module_doc(module_pair):
    print(module_pair[0] + ' -> ' + module_pair[1])
    html = requests.get(module_pair[1]).text
    soup = BeautifulSoup(html, features='html.parser')
    module_filename = module_pair[0] + '.csv'
    with open(module_filename, mode='w') as modules_content:
        modules_content_writer = csv.writer(modules_content, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # have packages
        packagestable = soup.body.find('table', attrs={'class':'packagesSummary'})
        packages = packagestable.find('tbody')
        for row in packages.find_all('tr'):
            header = row.find('th')
            package_name = header.text
            package_link = base_url + header.find('a').get('href')
            description_raw = row.find('td').text
            description = re.sub(r'\n+', '', description_raw)
            
            print (package_name + ' -> ' + package_link)
            row = [package_name, package_link, description]
            modules_content_writer.writerow(row)
            
        # have services which are classes
    print('\n')
    
# probably can be parallelized    
def parse_modules(modules_dict):
    with Pool(4) as p:
        p.map(parse_module_doc, modules_dict.items())

modules_dict = parse_main_doc()
parse_modules(modules_dict)
        