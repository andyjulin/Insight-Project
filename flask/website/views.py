import sys
from datetime import datetime

import numpy as np
import pandas as pd
import psycopg2
import googlemaps
from bs4 import BeautifulSoup
from website import app
from flask import render_template, request

sys.path.append("../modules")
from highways import get_roads, get_road_codes, get_highways, get_last_exit
from features import get_features

api_key = 'AIzaSyAm2m8M3Lfsqn_f_QwK_7cybr8ErEhzz-Y'

gmaps = googlemaps.Client(key=api_key)

highways = get_highways()

df_features = get_features()

def parse_instruction(instruction):
    words = instruction.split()
    
    exit = ''
    road = ''
    
    for w in range(len(words)):
        if w < len(words) - 1:
            if words[w] == 'exit':
                if not words[w + 1][0].isalpha():
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

#    print 'Initial Road:', road
                        
    road = [filter_road(r) for r in road.strip(',').split('/')]#[0]                    

#    print 'Adjusted Road:', road

    return exit, road


def filter_road(text):
    text = text + ' '
    text = text.replace('St ', 'Street ')
    text = text.replace('Rd ', 'Road ')
    text = text.replace('Expy ', 'Expressway ')
    text = text.replace('Ave ', 'Avenue ')
    text = text.strip()

    return text


def get_direction_list(start_loc, end_loc, departure = None):
    if not departure:
        departure = datetime.now()

    directions_result = gmaps.directions(start_loc, end_loc, \
            mode="driving", departure_time=departure)

    data = directions_result[0]['legs'][0]['steps']

    dirs = [(data[d]['html_instructions'], data[d]['duration']['value']) \
            for d in range(len(data))]

    road_list = []
    dir_list = []

    last_road = ''
    for d in dirs:
        t = BeautifulSoup(d[0])
        
        text = filter_road(t.find('p').get_text())# + ' '.strip()

        
        exit, road = parse_instruction(text)
        code = road[0].split(' ')[0]
        road = [r.replace("-", " ") for r in road]

#        dir_list.append([exit, road])
        if len(road) > 0:
            if len(dir_list) > 0:

#                print road, last_road

#                if road.find(dir_list[-1][0]) != -1 or dir_list[-1].find(road) != -1:
                if road[0] is last_road[0] or road[0].find(last_road[0]) != -1 or last_road[0].find(road[0]) != -1:
                    continue


#            print "Road: '%s', Last Road: '%s'" % (road, last_road)

            if code in highways:
                if exit != '':
                    road_list[-1][2] = exit

                road_list.append([road[0], get_exit(code, last_road), ''])#, text])


            dir_list.append(text)
            last_road = road

    return road_list, dir_list


def get_exit(highway, road):
    if highway not in highways or not highways[highway]:
        return None 


#    print "Checking '%s' for '%s'" % (highway, road)
    d = highways[highway].exits
    for e in sorted(d):
        d_name = d[e][2].replace('SR', 'CA')
        d_name = d_name.replace("-", " ")
        d_name = d_name.replace(' east', ' E').replace(' west', ' W').replace(' north', ' N').replace(' south', ' S')

        d_name = ' '.join(d_name.split())

        i = -1
        for r in road:
            road_words = r.split()
            for w in road_words:
                if w in ['N', 'S', 'E', 'W']:
                    road_words.remove(w)
            r = ' '.join(road_words)

            i = d_name.find(r)

            if i != -1:
                break

        if i != -1:
            return '%4s - %3s - %6s' % (e, d[e][0], d[e][1])
    
    return ''


def get_last_exit(highway, county, postmile):
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


@app.route('/')
@app.route('/index')
@app.route('/map')
def show_map():
    start_loc = request.args.get('start_loc')
    end_loc = request.args.get('end_loc')

    if start_loc is None or end_loc is None:
        start_loc = "Insight Data Science"
        end_loc = "San Francisco"

    # run direction_list through exit bounding function
    # use exit bounds to obtain exit intervals for each road
    # plot points colorized by risk

    road_list, dir_list = get_direction_list(start_loc, end_loc)


    df_predict = pd.DataFrame.from_csv('../data/df_predict_v0.0.csv')

    points = []
    for r in road_list:
        road_name = '-'.join(r[0].split()[:2])
        highway = int(r[0].split()[1])
        df_t = df_predict[df_predict.Highway == highway]

        i = 0
        for v in df_t.values:
            label = 'segment_%d' % i
            color = 'green' if v[7] < 1.1 else 'yellow' if v[7] < 1.25 else 'red'

            points.append([label, v[3], v[4], color])
            i += 1


#    points = [
#        ['testcity1', 34.052, -118.243],
#        ['testcity2', 37.47, -119.25]
#    ]


    return render_template(
            "map.html", 
            api_key = api_key,
            start_loc = start_loc,
            end_loc = end_loc,
            road_list = road_list,
            dir_list = dir_list,
            points = points,
    )
