from bs4 import BeautifulSoup
import requests, csv, re

base_url = 'https://docs.oracle.com/en/java/javase/11/docs/api/'
# loading page
url = base_url + 'index.html'
html = requests.get(url).text
soup = BeautifulSoup(html, features='html.parser')

# parsing process started
# 1. get the overview table
overviewtable = soup.body.find('table', attrs={'class':'overviewSummary'})
# 2. get table tbody - for odd reason it gets only the last one tbody
# and the table has two bodies, but the first one is not important
modules = overviewtable.find('tbody')
# 3. each row looks like this
# <th class="colFirst" scope="row">
#   <a href="jdk.xml.dom/module-summary.html">jdk.xml.dom</a>
# </th>
# <td class="colLast">
#   <div class="block">Defines the subset of the W3C Document Object Model (DOM) API that is not part of the Java SE API.</div>
# </td>
with open('java11_modules.csv', mode='w') as modules_export:
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
