# -*- coding: utf-8 -*-
"""
proladder crawler
"""
##TODO: add writer/loader
from bs4 import BeautifulSoup
import urllib
from collections import defaultdict
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

import numpy as np
import matplotlib.pyplot as plt

#############
##player class
############# 
def str2int(s):
    return int(s.replace(",","").split(' ')[0].split('/')[0])

class pro_player(object):
    classes = ["nilfgaard", "scoiatael", "northernkingdom", "skellige", "monster"]
    class_colors = [(0.1, 0.1, 0.1, 1), (0.1, 0.8, 0.1, 1), (0.1, 0.3, 0.9, 1), (0.3, 0.3, 0.7, 1), (0.9, 0, 0, 1)]
    def __init__(self, html_element):
        divs = html_element.find_all("div")
        self.rank = int(divs[0].text)
        self.country = divs[1].i['class'][1].split('-')[-1]
        self.id = divs[2].text
        self.score, self.matches = self._get_score_matches(divs[3].findChildren())
        self.matches = int(divs[3].span.text.split(' ')[0])
        self.low = 0
        for c in self.classes:
            block = html_element.find("div", class_ = c)
            if block == None:
                self.low+=1
#                print("{}: {} = {}".format(self.rank, self.low, c))
                block = html_element.find("div", class_ = "lowest")
                
            best = str2int(block.get_text(" ").split(" ")[0])
            score, matches = self._get_score_matches(block.div.div.findChild().find_next_siblings())
            setattr(self, c, {"best": best, "current": score, "matches":matches})
    
    def _get_score_matches(self, block):
        score = str2int(block[0].text)
        matches = str2int(block[1].text)
        return score, matches
            
    def valid(self):
        matches = []
        scores = []
        for c in self.classes:
            matches += [self[c]['matches']]
            scores += [self[c]['best']]
        best_scores =  sum(sorted(scores)[1:])
        total_matches = sum(matches)
        if self.matches != total_matches:
            print("#{} {}: matches {} != total matches {}".format(self.rank, self.id, self.matches, total_matches))
        if self.score != best_scores:
            print("#{} {}: score {} != best scores {}".format(self.rank, self.id, self.score, best_scores))
        return (self.matches == total_matches) and (self.score <= best_scores)
    
    def __getitem__(self, key):
        return getattr(self, key, None)
    
    def to_list(self):
        headers = ["rank", "country", "id", "score", "matches"]
        values = [str(self[header]) for header in headers]
        for c in self.classes:
            for item in self[c].items():
                headers.append("{}_{}".format(c, item[0]))
                values.append(item[1])
        return values, headers
    

#############
##player database
############# 
class player_db(object):
    def __init__(self):
        self.ids = []
        self.count = 0
        self.player_list =[]
    
    def append(self, player):
        if isinstance(player, pro_player) and player.valid():
            if player.id in self.ids:
                print("{} already existed".format(player.id))
            else:
                self.ids.append(player.id)
                self.player_list.append(player)
                self.count += 1
        else:
            print("{} is not a valid pro player".format(player.rank))
            
    def __iadd__(self, player):
        self.append(player)
        return self
    
    def _class_stats(self, class_):
        '''
        all mean_score_x is normalized to 100 games
        mean_score_c: mean class score of players completed 100 games
        mean_score_a: mean class score of players played 
        mean_score_t: mean class score per game
        '''
        if class_ not in pro_player.classes:
            raise NameError("{} is not a valid class".format(class_))
        stats = defaultdict(lambda: 0)
        for player in self.player_list:
            class_dict = player[class_]
            stats['total_matches'] +=  class_dict['matches']
            if class_dict['matches'] >= 100:
                stats['complete'] += 1
                stats['mean_score_c'] += class_dict['best']
                stats['mean_score_a'] += class_dict['best']
                stats['mean_score_t'] += class_dict['current'] * class_dict['matches']
            else:
                if class_dict['matches'] > 0:  
                    stats['incomplete'] += 1
                    stats['mean_score_a'] += class_dict['best'] * 100 / class_dict['matches']
                    stats['mean_score_t'] += class_dict['current'] * 100
        if stats['complete'] > 0:
            stats['mean_score_c'] /= stats['complete']
        else:
            stats['mean_score_c'] = 0
        if (stats['complete'] + stats['incomplete']) > 0:
            stats['mean_score_a'] /= (stats['complete'] + stats['incomplete'])
        else:
            stats['mean_score_a'] = 0
        if stats['total_matches'] > 0:
            stats['mean_score_t'] /= stats['total_matches']
        else:
            stats['mean_score_t'] = 0
        return stats
    
    def stats(self, plot = False):
        all_stats = dict()
        for c in pro_player.classes:
            all_stats[c] = self._class_stats(c)
        if plot:
          pass
            
        return all_stats

def plot(stats, radii = 'mean_score_c',  width = 'total_matches', order = None, offset = 1150):
    radius_list = np.array([stats[c][radii] for c in pro_player.classes])
    width_list = np.array([stats[c][width] for c in pro_player.classes])
    if order == 'radii':
        order = np.argsort(radius_list)
    elif order == 'width':
        order = np.argsort(width_list)
    else: 
        if isinstance(order, (list, np.ndarray, set)) and \
            set(order) == set(np.arange(len(pro_player.classes))):
                order = np.array(order)
        else:
            order = np.arange(len(pro_player.classes))
    radius_list = radius_list[order]
    width_list = width_list[order]
    print(order)
    width_list = width_list/np.sum(width_list) * 2 * np.pi
    theta = np.cumsum(width_list)
    theta -= width_list/2
    ax = plt.subplot(111, projection='polar')
    bars = ax.bar(theta, radius_list, width = width_list, 
                  bottom=-offset, edgecolor = (1, 0.9, 0.1, 1), 
                  color = np.array(pro_player.class_colors)[order],
                  tick_label = np.array(pro_player.classes)[order])
    
    plt.show()
    
def test(a):
    if isinstance(a, list) and len(a) == 1:
        print(1)
    else:
        print(2)
############
##html
############
def get_page(index = 1):
    base_site = "https://masters.playgwent.com/en/rankings/pro-ladder"
    if index < 1:
        index = 1
    return "%s/%d" % (base_site, index)
        

def parse_page(index = 1):
    site = get_page(index)
    print("parsing: {}".format(site))
    req = urllib.request.Request(site, headers=hdr)
    page = urllib.request.urlopen(req).read()
    soup = BeautifulSoup(page)
#    page_string = soup.prettify()
    players = soup.find_all("div", class_="c-ranking-mobile-table__body")
    first_player = players[1].findChild() #using the second block which contains more info
    other_players = first_player.find_next_siblings()
    return [first_player] + other_players

def crawl(start_page = 1, crawl_pages = 50):
    player_list = player_db()
    
    for index in range(start_page, start_page + crawl_pages):
        players = parse_page(index)
        for player in players:
            player_list.append(pro_player(player))
    return player_list

def main():
    db0 = crawl(1, 25) #first 25 pages, have completed ~2 classes
    stats0 = db0.stats()
    plot(stats0, order = 'radii')
    db1 = crawl(25, 100) #first 25 pages, have completed ~2 classes
    stats1 = db1.stats()
    plot(stats1, order = 'radii')

if __name__ == "__main__":
    main()
#    pass