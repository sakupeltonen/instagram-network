import networkx as nx
import numpy as np
from sklearn.cluster import KMeans

from database import UserDatabase

db = UserDatabase("instagram2.db")

account_data = db.simple_query("SELECT username, followers_updated_date, bio FROM accounts")
account_dict = {x[0]: x[1:] for x in account_data}
follower_data = db.simple_query("SELECT * FROM followers")

# create graph of all followers
# used to get degree
g_unfiltered = nx.Graph()
g_unfiltered.add_edges_from(follower_data)


# filter by scraped
# filtered_accounts = [username for username in g_unfiltered.nodes if account_dict[username][0]]

# filter by amount of connections
min_deg = 10
filtered_accounts = [username for username in g_unfiltered.nodes
                     if g_unfiltered.degree[username] > min_deg]


# temp solution to avoid non-modifiability of views
_g = g_unfiltered.subgraph(filtered_accounts)
g = nx.Graph(_g)

# relabels nodes with indices from sorted(g.nodes)
g_relabeled = nx.convert_node_labels_to_integers(g, ordering='sorted')
# make relabeling explicit for bringing back the results
label_dict = {i: username for i, username in enumerate(sorted(g.nodes))}


def get_adjlist(filename):
    with open(filename, 'w') as f:
        for line in nx.generate_adjlist(g_relabeled):
            f.write(line + '\n')


def load_embeddings(filename):
    with open(filename, 'r') as f:
        _ = f.readline()  # first line contains headers
        for line in f:
            # omit newline character
            items = line[:-1].split(' ')

            # get username based on label
            node_label = int(items[0])
            username = label_dict[node_label]

            # extract embedding
            embedding = list(map(lambda x: float(x), items[1:]))

            # save embedding to g
            g.nodes[username]['embedding'] = embedding


def cluster_analysis(n_clusters):
    X = np.array([g.nodes[username]['embedding']
                  for username in sorted(g.nodes)])

    kmeans = KMeans(n_clusters=n_clusters).fit(X)

    cluster_label_by_username = {label_dict[i]: cluster_label
                                 for i, cluster_label in enumerate(kmeans.labels_.tolist())}

    usernames_by_cluster = {}
    for cluster_label in range(n_clusters):
        usernames_by_cluster[cluster_label] = []

        for username in filtered_accounts:
            if cluster_label_by_username[username] == cluster_label:
                usernames_by_cluster[cluster_label].append(username)

    return usernames_by_cluster

# get_adjlist('/Users/saku/Documents/CS/deepwalk/edges2.txt')
load_embeddings('testi2.txt')
clusters = cluster_analysis(40)

# i = 1
# for username in clusters[0]:
#     bio = account_dict[username][1]
#     if bio:
#
#         print('{}: {}'.format(username, repr(bio.decode('utf-8'))))
#     else:
#         print(username)
