from bs4 import BeautifulSoup

from support_utils import normalize_description

import requests

# TODO: made it a separate 
BASE_JDK_URL = 'https://docs.oracle.com/en/java/javase/11/docs/api/'

def parse_jdk_module(module, allowed_packages_masks):
    # [module] is a list that looks like this [java.base, link, description]
    html = requests.get(module[1]).text
    soup = BeautifulSoup(html, features='html.parser')
    package_list_table = [package_list_table for package_list_table in soup.body.find_all('table', attrs={'class':'packagesSummary'})
                                             if __is_supported_table(package_list_table)]
    if not package_list_table:
        return []
    return [(module + package) for package in __process_summary_table(package_list_table, module[0])
                               if __filter_packages(package[0], allowed_packages_masks)]    

def __is_supported_table(package_table):
    package_table_name = package_table.select('caption span')[0].text
    return package_table_name not in ['Indirect Exports']
    
def __filter_packages(package_name, allowed_packages_masks):
    return not allowed_packages_masks or any(package_name.startswith(mask) for mask in allowed_packages_masks)
    
def __process_summary_table(package_list_table, module_name):
    table_body = package_list_table[0].find('tbody')
    return [__process_summary_table_row(table_row, module_name) for table_row in table_body.find_all('tr')]
    
def __process_summary_table_row(table_row, module_name):
    header, content = table_row.find('th'), table_row.find('td')
    
    package_name = header.text
    
    # create link
    package_relative_link = header.find('a').get('href')
    # some URI starts with ../
    if package_relative_link.startswith('../'):
        package_relative_link = package_relative_link[3:]
    package_link = BASE_JDK_URL  + module_name + '/' + package_relative_link
    
    package_description = normalize_description(content.text)
    return [package_name, package_link, package_description]
