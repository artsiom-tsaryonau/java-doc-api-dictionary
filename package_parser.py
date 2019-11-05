from bs4 import BeautifulSoup
import requests, re

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

# TODO: move to separate method
def __normalize_description(text):
    return re.sub(r'\n+', '', text)

def parse_jdk_package(module):
    # [module] is a list that looks like this 
    # [java.base, link, description, java.io, link, description ]
    package_page_link = module[4]
    html = requests.get(package_page_link).text
    soup = BeautifulSoup(html, features='html.parser')
    # there are multiple types of object in the package
    types = soup.body.find_all('table', attrs={'class':'typeSummary'})
    module_package_type_list = []
    for type in types: # process each table type
        # [[exception, Exception, link, description]]
        type_list = __process_summary_table(type, package_page_link)
        # [[java.base, link, description, java.io, link, description, exception, Exception, link, description]]
        type_list = [module + type_list_entry for type_list_entry in type_list]
        module_package_type_list += type_list # join the type list to other type lists
    return module_package_type_list
    
def __process_summary_table(type_list_table, package_page_link):
    type_list = []
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
    types_list = []
    for table_row in table_body.find_all('tr'):
        types_list.append([type] + __process_summary_table_row(table_row, package_link))
    return types_list
    
# this decorator affects performance, probably better to do that in a separate process 
# @__validate_link
def __process_summary_table_row(table_row, package_link):
    header = table_row.find('th')
    content = table_row.find('td')
                    
    type_name = header.text
    
    last_slash = package_link.rindex('/')
    package_link_length = len(package_link)
    to_slice = package_link_length - last_slash - 1
    package_link_slice = package_link[:-to_slice]
    if not package_link_slice.endswith('/'):
        package_link_slice += '/'
    
    type_relative_link = header.find('a').get('href')
    type_link = package_link_slice + type_relative_link
    type_description = __normalize_description(content.text)
    
    return [type_name, type_link, type_description]
 