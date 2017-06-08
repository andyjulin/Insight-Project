import sys
from datetime import datetime

import psycopg2
import googlemaps
from bs4 import BeautifulSoup
from website import app
from flask import render_template, request

gmaps = googlemaps.Client(key='AIzaSyAm2m8M3Lfsqn_f_QwK_7cybr8ErEhzz-Y')

def parse_instruction(instruction):
    words = instruction.split()
    
    exit = ''
    road = ''
    
    for w in range(len(words)):
        if w < len(words) - 1:
            if words[w] == 'exit':
                exit = words[w + 1]
            
            # Check for current road
            elif words[w] in ['on', 'onto']:
                for o in range(w + 1, len(words)):
                    # Road name in middle of text
                    if not words[o][0].isupper() \
                    and not words[o][0].isdigit():
                        road = ' '.join(words[w + 1:o])
                        break        
                    # Road name at end of text
                    elif o == len(words) - 1:
                        road = ' '.join(words[w + 1:])
                        break
                        
    road = road.strip(',').split('/')[0]                    
            
    return exit, road


def get_direction_list(start_loc, end_loc, departure = None):
    if not departure:
        departure = datetime.now()

    directions_result = gmaps.directions(start_loc, end_loc, \
            mode="driving", departure_time=departure)

    data = directions_result[0]['legs'][0]['steps']

    dirs = [(data[d]['html_instructions'], data[d]['duration']['value']) \
            for d in range(len(data))]

    dir_list = []

    for d in dirs:
        t = BeautifulSoup(d[0])
        
        text = t.find('p').get_text() + ' '
        text = text.replace('St ', 'Street ')
        text = text.replace('Rd ', 'Road ')
        
        exit, road = parse_instruction(text)

        dir_list.append([exit, road])

    return dir_list


def get_last_exit(highway, county, postmile):
    data = highways[test_highway]    
    
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


@app.route('/')
@app.route('/index')
def index():
   return render_template("index.html", )

@app.route('/output')
def show():
    start_loc = request.args.get('start_loc')
    end_loc = request.args.get('end_loc')

    direction_list = get_direction_list(start_loc, end_loc)

#    print direction_list

    return render_template(
            "output.html", 
            start_loc = start_loc,
            end_loc = end_loc,
            direction_list = direction_list
    )

