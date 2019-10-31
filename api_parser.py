from bs4 import BeautifulSoup
from multiprocessing import Pool
import requests, csv, re, logging, time

BASE_URL = 'https://docs.oracle.com/en/java/javase/11/docs/api/'
MODULES_FILE_LIST_NAME = 'java11_modules.csv'
MODULE_FILE_NAME_PREFIX = 'module_'
PACKAGE_FILE_NAME_PREFIX = 'package_'
ALLOWED_MODULE = 'java'
MODULES_TABLE_NAME = 'overviewSummary'
IGNORED_TABLES = ['Indirect Exports']
TYPES = ['Package', 'Class', 'Exception', 'Interface', 'Enum', 'Error', 'Annotation Type']

logging.basicConfig(filename='parsing.log', 
                    filemode='w', 
                    level=logging.DEBUG, 
                    format='%(levelname)s - %(message)s')

# probably violates YAGNI for now but whatever
class DefaultNamed:
    def __init__(self, name):
        self.name = name

class Module(DefaultNamed):
    def __init__(self, name):
        DefaultNamed.__init__(self, name)
        
class Package(DefaultNamed):
    def __init__(self, name):
        DefaultNamed.__init__(self, name)
        
class Class(DefaultNamed):
    def __init__(self, name):
        DefaultNamed.__init__(self, name) 
        
class Interface(DefaultNamed):
    def __init__(self, name):
        DefaultNamed.__init__(self, name)
        
class Exception(DefaultNamed):
    def __init__(self, name):
        DefaultNamed.__init__(self, name)
        
class Enum(DefaultNamed):
    def __init__(self, name):
        DefaultNamed.__init__(self, name)
    
def normalize_text(text):
    return re.sub(r'\n+', '', text)
    
def create_direct_link(relative_link):
    return BASE_URL + relative_link
    
def create_direct_package_link(relative_link, module_name):
    return BASE_URL + module_name + '/' + relative_link
 
# parses single entry in module table
def parse_jdk_module_entry(entry):
    header = entry.find('th')
    content = entry.find('td')
            
    entry_name = header.text
    entry_relative_link = header.find('a').get('href')
    entry_link = create_direct_link(entry_relative_link)
    entry_description = normalize_text(content.text)

    return [entry_name, entry_link, entry_description]

def parse_jdk_module_overview_table(summary_table):
    overview_table = summary_table.find('tbody')
    list_result = []
    for entry in overview_table.find_all('tr'):
        list_result.append(parse_jdk_module_entry(entry))
    return list_result

# 1. parse JDK module list
def parse_jdk_modules_page():
    url = BASE_URL + 'index.html'
    html = requests.get(url).text
    soup = BeautifulSoup(html, features='html.parser')
    jdk_modules_dict = {}
    with open(MODULES_FILE_LIST_NAME, mode='w') as jdk_modules_file:
        jdk_modules_writer = csv.writer(jdk_modules_file, 
                                        delimiter=',', 
                                        quotechar='"', 
                                        quoting=csv.QUOTE_MINIMAL)
        summary_table = soup.body.find('table', 
                                       attrs={'class':MODULES_TABLE_NAME})
                                       
        def process_result_funct(list_result_entry):
            if list_result_entry[0].startswith(ALLOWED_MODULE):
                jdk_modules_writer.writerow(list_result_entry)
                jdk_modules_dict[list_result_entry[0]] = list_result_entry[1]
                
        list_result = parse_jdk_module_overview_table(summary_table)
        for module_info in list_result:
            process_result_funct(module_info)
        
    return jdk_modules_dict

# 2. parse JDK module
def parse_jdk_module_page(module_name, module_page_link):
    html = requests.get(module_page_link).text
    soup = BeautifulSoup(html, features='html.parser')
    filename = MODULE_FILE_NAME_PREFIX + module_name + '.csv'
    jdk_module_packages_dict = {}
    with open(filename, mode='w') as module_content:
        module_content_writer = csv.writer(module_content, 
                                           delimiter=',', 
                                           quotechar='"', 
                                           quoting=csv.QUOTE_MINIMAL)
        # check if has <a id='packages.summary'>
        # can be multiple - difference in caption
        packages = soup.body.find_all('table', 
                                       attrs={'class':'packagesSummary'})
        
        def process_result_funct(list_result_entry):
            module_content_writer.writerow(list_result_entry)
            jdk_module_packages_dict[list_result_entry[0]] = list_result_entry[1]
                
        list_result = parse_jdk_module_packages(packages, module_name)
        for list_result_entry in list_result:
            process_result_funct(list_result_entry)
            
        # TODO: parse module dependencies if needed
    return jdk_module_packages_dict
                
def parse_jdk_module_packages(packages, module_name):
    for package_table in packages:
        return parse_jdk_module_package(package_table, module_name)
    
def parse_jdk_module_package(package, module_name):
    list_result = []
    
    # check for table type
    # TODO: indirect exports are ignored
    table_name = package.select('caption span')[0].text
    if (table_name not in IGNORED_TABLES):
        for row in package.find_all('tr'):
            if row.find('th').text not in TYPES:
                list_result.append(parse_jdk_module_package_entry(row, module_name))
    # all packages are processed at that stage
    return list_result
        
def parse_jdk_module_package_entry(entry, module_name):
    header = entry.find('th')
    content = entry.find('td')
        
    entry_name = header.text
        
    entry_relative_link = header.find('a').get('href')
    # some URI start with ../ for some reason
    if entry_relative_link.startswith("../"):
        entry_relative_link = entry_relative_link[3:]
    entry_link = create_direct_package_link(entry_relative_link, module_name)
    entry_description = normalize_text(content.text)
    return [entry_name, entry_link, entry_description]

def parse_jdk_package_page(package_name, package_page_link):
    html = requests.get(package_page_link).text
    soup = BeautifulSoup(html, features='html.parser')
    filename = PACKAGE_FILE_NAME_PREFIX + package_name + '.csv'
    with open(filename, mode='w') as package_content:
        package_content_writer = csv.writer(package_content, 
                                             delimiter=',', 
                                             quotechar='"', 
                                             quoting=csv.QUOTE_MINIMAL)
        types = soup.body.find_all('table',
                                   attrs={'class':'typeSummary'})
                                   
        type_dict = {}
        for type in types:
            table_name = type.select('caption span')[0].text
            if table_name.startswith('Class'):
                logging.debug('\t\tClasses =>')
                type_dict['class'] = parse_type_entries(type, package_page_link)
            elif table_name.startswith('Enum'):
                logging.debug('\t\tEnums =>')
                type_dict['enum'] = parse_type_entries(type, package_page_link)
            elif table_name.startswith('Interface'):
                logging.debug('\t\tInterfaces =>')
                type_dict['interface'] = parse_type_entries(type, package_page_link)
            elif table_name.startswith('Exception'):
                logging.debug('\t\tException =>')
                type_dict['exception'] = parse_type_entries(type, package_page_link)
            elif table_name.startswith('Annotation Type'):
                logging.debug('\t\tAnnotation Type =>')
                type_dict['annotation'] = parse_type_entries(type, package_page_link)
            else:
                logging.debug('\t\tError =>')
                type_dict['error'] = parse_type_entries(type, package_page_link)
                
        print(type_dict)
              
def parse_type_entries(type, package_link):
    list_result = []
    for entry in type.find_all('tr'):
        if entry.find('th').text not in TYPES:
            list_result.append(parse_type_entry(entry, package_link))
    return list_result
        
def parse_type_entry(entry, package_link):
    header = entry.find('th')
    content = entry.find('td')
                    
    entry_name = header.text
    logging.debug('\t\t\t' + entry_name)

    last_slash = package_link.rindex('/')
    package_link_length = len(package_link)
    to_slice = package_link_length - last_slash + 1

    entry_relative_link = header.find('a').get('href')
    entry_link = package_link[:-to_slice] + entry_relative_link
    entry_description = normalize_text(content.text)
    
    return [entry_name, entry_link, entry_description]
    
# pure sequential execution
start_seq_time = time.time()
# exec
modules_dict = parse_jdk_modules_page() # { module: http_link }
for key, value in modules_dict.items():
    logging.debug('Module: ' + key)
    packages_dict = parse_jdk_module_page(key, value) # { package: http_link }
    for package, link in packages_dict.items():
        logging.debug('\tPackage: ' + package)
        parse_jdk_package_page(package, link)
    break
elapsed_seq_time = time.time() - start_seq_time
print(elapsed_seq_time)
