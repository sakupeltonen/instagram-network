from pyx import *
from PIL import Image

import networkx as nx
import os
import random

from database import UserDatabase
from insight import get_tagged_users


"""
TEST 3.3

Layout
- calculate positions for scraped accounts only 
- fix the result, and add privates ony by one. 
    - done in small chunks for efficiency
- proper handling of the weights in the original graph

Drawing
- only include accounts with images
- don't show usernames
- scale the positions to avoid overlapping"""

db = UserDatabase("instagram2.db")

account_data = db.simple_query("SELECT username, followers_updated_date FROM accounts")
account_dict = {x[0]: x[1:] for x in account_data}
follower_data = db.simple_query("SELECT * FROM followers")

tags = get_tagged_users(db)

g_directed = nx.DiGraph()
g_directed.add_edges_from(follower_data)
g = g_directed.to_undirected()

# filter accounts having less than some amount of connections
min_deg = 20
filtered_accounts = [username for username in g.nodes if g.degree[username] > min_deg]
g = g.subgraph(filtered_accounts)

"""
Weight edges based on the degree of the edge's vertices
"""


def calculate_weight(edge):
    user1, user2 = edge

    if user2 in tags[user1] or user1 in tags[user2]:
        return 1
    else:
        # intuition is that the link tells more
        # about the user with the smaller amount of followers
        return min(0.002,
                   1 / (min(g.degree[user1], g.degree[user2])))


weights = {}
for edge in g.edges:
    weights[edge] = calculate_weight(edge)

nx.set_edge_attributes(g, weights, 'weight')


# list of usernames where followers_updated_date is set
scraped_accounts = [username for username in g.nodes if account_dict[username][0]]
scraped_subg = g.subgraph(scraped_accounts)

# calculate positions in subgraph of scraped accounts
scraped_pos = nx.spring_layout(scraped_subg, k=0.005)


# find accounts with some amount of connections, that haven't been scraped
not_scraped = list(set(filtered_accounts) - set(scraped_accounts))

final_pos = scraped_pos


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


for chunk in chunks(not_scraped, 10):
    temp_g = nx.subgraph_view(g, lambda x: x in scraped_accounts or x in chunk)
    temp_pos = nx.spring_layout(temp_g, k=0.005, iterations=20, pos=scraped_pos, fixed=scraped_accounts)
    for username in chunk:
        final_pos[username] = temp_pos[username]


def clamp(x):
    # add some randomness to avoid sharp borders
    maxx = 0.5 - random.uniform(0, 0.15)
    minx = -0.4 + random.uniform(0, 0.15)
    return max(min(maxx, x), minx)


# clamp position to avoid overly sparse graph
for username in final_pos.keys():
    pos = final_pos[username]
    final_pos[username] = (clamp(pos[0]), clamp(pos[1]))


# TODO wiggle around nodes to avoid overlapping

# scraped accounts + those with more than 10
subgraph = g.subgraph(scraped_accounts + filtered_accounts)

# size of canvas s*2
s = 100
# radius of node
img_s = 0.6

c = canvas.canvas()

for edge in list(subgraph.edges):
    (x0, y0) = final_pos[edge[0]]
    (x1, y1) = final_pos[edge[1]]


    if edge[1] in tags[edge[0]]:
        line_style = [style.linewidth(img_s / 10), color.transparency(0.95), color.rgb.blue]
    else:
        line_style = [style.linewidth(img_s / 20), color.transparency(0.99)]

    c.stroke(path.line(x0*s + img_s/2, y0*s + img_s/2,
                       x1*s + img_s/2, y1*s + img_s/2),
             line_style)

for node in list(subgraph.nodes):
    (x, y) = final_pos[node]

    path = os.getcwd() + "/img/" + node + ".png"
    if os.path.isfile(path):
        i = Image.open(path)

        c.insert(bitmap.bitmap(s * x, s * y, i, compressmode=None, width=img_s))
       # c.text(s * x + img_s / 2, s * y + img_s, node.replace('_', r'\_'), [text.halign.boxcenter])

    # else:
    #     i = Image.open("pics/placeholder.png")



c.writePDFfile("pyx_img/force_directed8")
