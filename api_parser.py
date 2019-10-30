from bs4 import BeautifulSoup
import requests, csv, re

base_url = 'https://docs.oracle.com/en/java/javase/11/docs/api/'
modules_file = 'java11_modules.csv'

# parses main index.html page
def parse_main_doc(modules):
    modules_dict = {}
    with open(modules_file, mode='w') as modules_export:
        modules_writer = csv.writer(modules_export, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in modules.find_all('tr'):
            header = row.find('th')
            module_name = header.text
            module_link = base_url + header.find('a').get('href')
            description_raw = row.find('td').text
            description = re.sub(r'\n+', '', description_raw)
        
            if module_name.startswith('java'):
                row = [module_name, module_link, description]
                modules_writer.writerow(row)
            
            modules[module_name] = module_link
    return modules

# 1. parse root modules
url = base_url + 'index.html'
html = requests.get(url).text
soup = BeautifulSoup(html, features='html.parser')
overviewtable = soup.body.find('table', attrs={'class':'overviewSummary'})
modules = overviewtable.find('tbody')
module_dict = parse_main_doc(modules)