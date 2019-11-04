from bs4 import BeautifulSoup
import requests, re

# TODO: made it a separate 
BASE_JDK_URL = 'https://docs.oracle.com/en/java/javase/11/docs/api/'

# TODO: move to separate method
def __normalize_description__(text):
    return re.sub(r'\n+', '', text)

def parse_jdk_module(module, allowed_packages_masks):
    # [module] is a list that looks like this [java.base, link, description]
    html = requests.get(module[1]).text
    soup = BeautifulSoup(html, features='html.parser')
    package_list_tables = soup.body.find_all('table', attrs={'class':'packagesSummary'})
    package_list_table = [package_list_table for package_list_table in package_list_tables
                                             if _is_supported_table(package_list_table)]
    if not package_list_table:
        return []

    all_packages = [package for package in _process_summary_table(package_list_table, module[0])
                            if _filter_packages(package[0], allowed_packages_masks)]    
    # TODO: turn into list comprehension
    module_packages_list = []
    for package in all_packages:
        module_packages_list.append(module + package)
    return module_packages_list

def _is_supported_table(package_table):
    package_table_name = package_table.select('caption span')[0].text
    if (package_table_name not in ['Indirect Exports']):
        return True
    return False
    
def _filter_packages(package_name, allowed_packages_masks):
    if not allowed_packages_masks: # all allowed
        return True
        
    for mask in allowed_packages_masks:
        if package_name.startswith(mask):
            return True
    return False
    
def _process_summary_table(package_list_table, module_name):
    table_body = package_list_table[0].find('tbody')
    all_packages = []
    for table_row in table_body.find_all('tr'):
        all_packages.append(_process_summary_table_row(table_row, module_name))
    return all_packages
    
def _process_summary_table_row(table_row, module_name):
    header = table_row.find('th')
    content = table_row.find('td')
    
    package_name = header.text
    
    # create link
    package_relative_link = header.find('a').get('href')
    # some URI starts with ../
    if package_relative_link.startswith('../'):
        package_relative_link = package_relative_link[3:]
    package_link = BASE_JDK_URL  + module_name + '/' + package_relative_link
    
    package_description = __normalize_description__(content.text)
    return [package_name, package_link, package_description]
