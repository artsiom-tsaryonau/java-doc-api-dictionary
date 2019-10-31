from bs4 import BeautifulSoup
from multiprocessing import Pool
import requests, csv, re
import logging

BASE_URL = 'https://docs.oracle.com/en/java/javase/11/docs/api/'
MODULES_FILE_LIST_NAME = 'java11_modules.csv'
MODULE_FILE_NAME_POSTFIX = '_module.csv'
ALLOWED_MODULE = 'java'
MODULES_TABLE_NAME = 'overviewSummary'
IGNORED_TABLES = ['Indirect Exports']

logging.basicConfig(filename='parsing.log', 
                    filemode='w', 
                    level=logging.DEBUG, 
                    format='%(levelname)s - %(message)s')

def normalize_text(text):
    return re.sub(r'\n+', '', text)
    
def create_direct_link(relative_link):
    return BASE_URL + relative_link
 
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
    filename = module_name + MODULE_FILE_NAME_POSTFIX
    with open(filename, mode='w') as module_content:
        module_content_writer = csv.writer(module_content, 
                                           delimiter=',', 
                                           quotechar='"', 
                                           quoting=csv.QUOTE_MINIMAL)
        # check if has <a id='packages.summary'>
        # can be multiple - difference in caption
        packages = soup.body.find_all('table', 
                                       attrs={'class':'packagesSummary'})
        process_packages(packages, module_content_writer)
# !!!! IGNORE module dependencies for now
        # check if has <a id='services.summary'>
        #provides = soup.body.find('table',
        #                           attrs={'class':'providesSummary'})
        #uses = soup.body.find('table',
        #                       attrs={'class':'usesSummary'})
        # check if has <a id='modules.summary'>
        # can be multiple - difference in caption
        # requires = soup.body.find_all('table',
        #                              attrs={'class':'requiresSummary'})
    
def process_packages(packages, csv_writer):
    package_lists = parkse_jdk_module_packages(packages)
    for package_list in package_lists:
        for package_entry in package_list:
            csv_writer.writerow(package_entry)
                
def parkse_jdk_module_packages(packages):
    package_lists = []
    for package_table in packages:
        list_result = parse_jdk_module_package(package_table)
        package_lists.append(list_result)
    return package_lists
    
def parse_jdk_module_package(package):
    list_result = []
    
    # check for table type
# !!!! IGNORE [Indirect Exports] for now
    table_name = package.select('caption span')[0].text
    if (table_name not in IGNORED_TABLES):
        for row in package.find_all('tr'):
            if row.find('th').text != 'Package':
                list_result.append(parse_jdk_module_package_entry(row))
    return list_result
        
def parse_jdk_module_package_entry(entry):
    header = entry.find('th')
    content = entry.find('td')
        
    entry_name = header.text
        
    entry_relative_link = header.find('a').get('href')
    # some URI start with ../ for some reason
    if entry_relative_link.startswith("../"):
        entry_relative_link = entry_relative_link[3:]
    entry_link = create_direct_link(entry_relative_link)
    entry_description = normalize_text(content.text)
    logging.debug(entry_name + ' : ' + entry_description)
    return [entry_name, entry_link, entry_description]

# exec
modules_dict = parse_jdk_modules_page()
for key, value in modules_dict.items():
    logging.debug('module: ' + key + ' |')
    parse_jdk_module_page(key, value)
    logging.debug('====')
