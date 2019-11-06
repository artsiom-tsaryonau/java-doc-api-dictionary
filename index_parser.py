from bs4 import BeautifulSoup

from support_utils import normalize_description

import requests, itertools

# TODO: made it a separate 
BASE_JDK_URL = 'https://docs.oracle.com/en/java/javase/11/docs/api/'

# parses jdk modules and return the list of them
def parse_jdk_modules(allowed_modules_masks):
    html = requests.get(BASE_JDK_URL + 'index.html').text
    soup = BeautifulSoup(html, features='html.parser')
    module_list_table = soup.body.find('table', attrs={'class':'overviewSummary'})
    
    # leave only allowed modules
    all_modules = [module for module in __process_summary_table(module_list_table)
                          if __filter_modules(module[0], allowed_modules_masks)] 
    return all_modules
    
def __filter_modules(module_name, allowed_modules_masks):
    return any(module_name.startswith(mask) for mask in allowed_modules_masks)
    
def __process_summary_table(module_list_table):
    table_body = module_list_table.find('tbody')
    all_modules = []
    for table_row in table_body.find_all('tr'):
        all_modules.append(__process_summary_table_row(table_row))
    return all_modules
    
def __process_summary_table_row(table_row):
    header, content = table_row.find('th'), table_row.find('td')
    
    module_name = header.text
    
    # create link
    module_relative_link = header.find('a').get('href')
    module_link = BASE_JDK_URL + module_relative_link
    
    module_description = normalize_description(content.text)
    # [ 'java.base'', '../summary.html', 'module used for ... ' ]
    return [module_name, module_link, module_description]
