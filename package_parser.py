from bs4 import BeautifulSoup

from support_utils import normalize_description

import requests

TYPES = ['Package', 'Class', 'Exception', 'Interface', 'Enum', 'Error', 'Annotation Type']

# TODO: move to separate module
def __validate_link(func):
    def validate_link(table_row, package_link):
        table_row = func(table_row, package_link) # reassign as we don't need inputs
        link_to_check = table_row[1]
        print('checking link...', link_to_check)
        valid_link = False
        with requests.get(link_to_check, stream=True) as response:
            try:
                response.raise_for_status()
            except (Exception, error) as e:
                print('Invalid link: ', link_to_check)
            finally:
                return table_row
    return validate_link

def parse_jdk_package(module):
    # [module] is a list that looks like this 
    # [java.base, link, description, java.io, link, description ]
    package_page_link = module[4]
    html = requests.get(package_page_link).text
    soup = BeautifulSoup(html, features='html.parser')
    type_list_joined = []
    for type in soup.body.find_all('table', attrs={'class':'typeSummary'}):
        type_list_joined += [(module + type_list_entry) for type_list_entry in __process_summary_table(type, package_page_link)]
    return type_list_joined
    
def __process_summary_table(type_list_table, package_page_link):
    table_name = type_list_table.select('caption span')[0].text
    if table_name.startswith('Class'):
        type_list = __process_type_table('class', type_list_table, package_page_link)
    elif table_name.startswith('Enum'):
        type_list = __process_type_table('enum', type_list_table, package_page_link)
    elif table_name.startswith('Interface'):
        type_list = __process_type_table('interface', type_list_table, package_page_link)
    elif table_name.startswith('Exception'):
        type_list = __process_type_table('exception', type_list_table, package_page_link)
    elif table_name.startswith('Annotation Type'):
        type_list = __process_type_table('annotation', type_list_table, package_page_link)
    else:
       type_list = __process_type_table('error', type_list_table, package_page_link)
    return type_list
    
def __process_type_table(type, type_list_table, package_link):
    table_body = type_list_table.find('tbody')
    return [([type] + __process_summary_table_row(table_row, package_link)) for table_row in table_body.find_all('tr')]
    
# this decorator affects performance, probably better to do that in a separate process 
# @__validate_link
def __process_summary_table_row(table_row, package_link):
    header, content = table_row.find('th'), table_row.find('td')
                    
    type_name = header.text
    
    last_slash = package_link.rindex('/')
    package_link_length = len(package_link)
    to_slice = package_link_length - last_slash - 1
    package_link_slice = package_link[:-to_slice]
    if not package_link_slice.endswith('/'):
        package_link_slice += '/'
    
    type_relative_link = header.find('a').get('href')
    type_link = package_link_slice + type_relative_link
    type_description = normalize_description(content.text)
    
    return [type_name, type_link, type_description]
 