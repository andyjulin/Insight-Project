from bs4 import BeautifulSoup
import urllib2
import pandas as pd
import numpy as np


# County codes not listed on Wikipedia pages
counties = {
'Nevada County, California': u'NEV',
'Los Angeles County, California': u'LA',
'Contra Costa County, California': u'CC',
'Alameda County, California': u'ALA',
'Riverside County, California': u'RIV',
'Orange County, California': u'ORA',
'Solano County, California': u'SOL',
'San Diego County, California': u'SD',
'San Bernardino County, California': u'SBD',
'Napa County, California': u'NAP',
'Yolo County, California': u'YOL',
'Sierra County, California': u'SIE',
'Sacramento County, California': u'SAC',
'Placer County, California': u'PLA',
}

# County codes with no 'County' column on their Wikipedia pages
single_county_roads = {
    'CA-85': u'SCL',
    'I-40': u'SBD',
    'CA-55': u'ORA',
    'I-105': u'LA',
    'I-110': u'LA',
    'CA-110': u'LA',    
    'CA-170': u'LA',  
}

# Roads which have an extra column in the Wikipedia table
km_highways = [
    'I-10',  'I-15',  'I-40',  'I-80', 'I-210',
    'I-605', 'CA-15', 'CA-24', 'CA-55'
]

# Designate roads to be used in analysis
i_roads = [
    'I-5',   'I-10',  'I-15',  'I-40',  'I-80', 
    'I-105', 'I-110', 'I-205', 'I-210', 'I-280',
    'I-605', 'I-680',
]

us_roads = [
    'US-50', 'US-101',
]

ca_roads = [
    'CA-1',   'CA-4',   'CA-14',  'CA-22',  'CA-24',  
    'CA-41',  'CA-55',  'CA-57',  'CA-58',  'CA-60',
    'CA-85',  'CA-91',  'CA-92',  'CA-99',  'CA-110',
    'CA-118', 'CA-120', 'CA-126', 'CA-134', 'CA-170', 
    'CA-198', 'CA-215'  
]

bad_roads = [   
    'I-8',  'I-580', 
]

roads = i_roads + us_roads + ca_roads# + bad_roads

road_codes = {}
for r in roads:
    c = r.split('-')
    road_codes[int(c[1])] = r

highways = {}


def get_roads():
    return roads


def get_road_codes():
    return road_codes


class Highway:   
    def __init__(self, code, verbose = False):        
        self.exits = {}
        self.code = code
        self.verbose = verbose
        
        self.get_html()
        
        if self.verbose:
            d = self.exits.itervalues().next()
            
            print '  %6s: %4s - %7s - %s' % (self.code, d[0], d[1], d[2])
    

    def get_html(self):
        s = self.code.split('-')

        if s[0] == 'CA':
            part = 'California_State_Route_%s' % s[1]
        elif s[0] == 'I':
            part = 'Interstate_%s_(California)' % s[1]
        elif s[0] == 'US':
            part = 'U.S._Route_%s_in_California' % s[1]

        url = 'https://en.wikipedia.org/wiki/' + part

        try:
            if self.verbose:
                print 'Checking ', url

            f = urllib2.urlopen(url)
            el_html = f.read()
            f.close()

            html = BeautifulSoup(el_html, 'html')
            
            self.get_exits(html)

        except ValueError:
            print '\tUnable to find:', self.code
        
    def get_exits(self, html):
        exit_list = html.find('span', id='Exit_list')
        
        if exit_list is None:
            exit_list = html.find('span', id='Major_intersections')            
        
        el_table = exit_list.find_next('table')

        el_rows = el_table.find_all('tr')

        # Certain roads only pass through one county, so it's easy!
        single_county_road = self.code in single_county_roads
        if single_county_road:
            county = single_county_roads[self.code] 
        else:
            county = ''
        
        for tr in enumerate(el_rows[1:]):
            # Other roads pass through multiple counties
            if not single_county_road:
                for td in tr[1].find_all('td'):                    
                    # Some have the county codes listed within the table...
                    c = td.find('small')
                    if c:
                        county = c.get_text().split()[0]
                        
                    # ...others must be input manually
                    c = td.find('a')
                    if c \
                    and c.has_attr('title') \
                    and 'County, California' in c['title']:
                        if c['title'] in counties:
                            county = counties[c['title']]

            
            # Find columns for exits / Postmile codes
            for th in tr[1].find_all('th'):
                td_exit = th.find_next_sibling('td')
                
                # Check for an additional column when both mi / km listed
                if self.code in km_highways:
                    td_exit = td_exit.find_next_sibling('td')   

                # Check for blank cells for longer exits
                if td_exit:
                    td_location = td_exit.find_next_sibling('td')
                    exit = td_exit.get_text()
                else:
                    td_location = None
                    exit = ''

                if td_location:
                    location = td_location.get_text().strip()
                else:
                    location = ''
                
                postmile = th.get_text()

                # Just take beginning of Postmile code stretch
                if '.' in postmile:
                    postmile = postmile[:postmile.index('.') + 3]

                # Just take beginning of Exit name listing
                if len(postmile) < 2 or len(exit.split()) > 1:
                    break
                
                # Only care about initial exits
                if exit != '':
                    if len(exit) == 1 \
                    or len(exit) == 2 and exit[1].isalpha():
                        exit = '0' + exit
                        
                    self.exits[exit] = [county, postmile, location]


def load_highways():
    if highways == {}:
        for r in roads:
            highways[r] = Highway(r)


def get_exit(highway, road):
    load_highways()

    d = highways[highway].exits
    for e in sorted(d):
        if road in d[e][2]:
            return '%4s - %3s - %6s' % (e, d[e][0], d[e][1])
    
    return 0


def get_last_exit(d):
    load_highways()

    if int(d[0]) not in road_codes:
        return 0
    
    highway = road_codes[int(d[0])]
    county = d[1]
    postmile = d[2]

    data = highways[highway]    
    
    c = postmile[0] if postmile[0].isalpha() else ' '    
    f = float(postmile[1:]) if c != ' ' else float(postmile)
    
    exit = 0
    
    e_last = 0
    c_last = ''
    
    for e in sorted(data.exits):
        t_county = data.exits[e][0]
        t_postmile = data.exits[e][1]
        
        if county != t_county:
            continue
        
        c1 = t_postmile[0] if t_postmile[0].isalpha() else ' '        
        f1 = float(t_postmile[1:]) if c1 != ' ' else float(t_postmile)
                        
        if (c1 == c):
            if f1 > f and exit == 0:
                exit = e_last
                
        else:
            c_last = c1
            
        e_last = e
            
#         print '%4s - %3s - %6s - %s' % (e, data.exits[e][0], data.exits[e][1], data.exits[e][2])
        
    return exit 

