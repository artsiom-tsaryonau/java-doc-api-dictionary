from bs4 import BeautifulSoup
import requests, re

# TODO: made it a separate 
BASE_JDK_URL = 'https://docs.oracle.com/en/java/javase/11/docs/api/'

# TODO: move to separate method
def __normalize_description__(text):
    return re.sub(r'\n+', '', text)

# parses jdk modules and return the list of them
def parse_jdk_modules(allowed_modules_masks):
    html = requests.get(BASE_JDK_URL + 'index.html').text
    soup = BeautifulSoup(html, features='html.parser')
    module_list_table = soup.body.find('table', attrs={'class':'overviewSummary'})
    
    all_modules = __process_summary_table__(module_list_table)
    # leave only allowed modules
    all_modules = [module for module in all_modules 
                          if __filter_modules__(module[0], allowed_modules_masks)] 
    return all_modules
    
def __filter_modules__(module_name, allowed_modules_masks):
    for mask in allowed_modules_masks:
        if  module_name.startswith(mask):
            return True
    return False
    
def __process_summary_table__(module_list_table):
    table_body = module_list_table.find('tbody')
    all_modules = []
    for table_row  in table_body.find_all('tr'):
        all_modules.append(__process_summary_table_row__(table_row))
    return all_modules
    
def __process_summary_table_row__(table_row):
    header = table_row.find('th')
    content = table_row.find('td')
    
    module_name = header.text
    
    # create link
    module_relative_link = header.find('a').get('href')
    module_link = BASE_JDK_URL + module_relative_link
    
    module_description = __normalize_description__(content.text)
    # [ 'java.base'', '../summary.html', 'module used for ... ' ]
    return [module_name, module_link, module_description]
