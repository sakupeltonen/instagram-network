# instagram-network

![graph](/graphs/example.png)
Network of Instagram users. [Zoomable PDF](https://github.com/Kuivausrumpusoolo/instagram-network/blob/master/graphs/force_directed10.pdf)

## Data Collection
The data was gathered using Selenium WebDriver. The crawler has gathered over 300 000 connections, which corresponds to about a thousand users.

Collected attributes include:<ul>
<li>username</li>
<li>name</li>
<li>profile picture</li>
<li>bio</li>
<li>list of followers and following</li>
<li>image descriptions and tagged users</li>
</ul>

All of the data is publicly available through the users' profiles (although Instagram will try to slow you down). That is, there is no data from people who have set their account to private. Connections to private accounts will however be visible in the follower/following lists of public accounts, which may make some private accounts visible as well. 

The database is not included. 

## Graph Visualization
Each user is a vertex, and connections between users are edges. For now, the graph is handled as an undirected graph. The layout is calculated with using a [force-directed algorithm](https://networkx.org/documentation/stable/reference/generated/networkx.drawing.layout.spring_layout.html#networkx.drawing.layout.spring_layout) from networkx. The layout should be such that accounts that have many common connections are positioned next to each other. Of course, doing this in only two dimensions is extremely limiting. 

Another challenge comes from private accounts, that cause the data to be incomplete. Since the layout algorithm has no knowledge of possible links between two private accounts, it tries to separate them, even though they had exactly the same known connections to (public) accounts. One option is to add *ghost edges* to counteract the repulsive force between such vertices. This approach is not scalable because the amount of ghost edges required is proportional to |V|^2. 

My solution consists of splitting the layout calculation in to two parts: <ol>
  <li>Only consider the subgraph induced by the public accounts. Calculate force-directed layout for the subgraph</li>
  <li>One by one, add private accounts to the layout. Fix the positions of the other accounts. This way, the positions of the private accounts do not affect each other. </li>
</ol>
In practice, the private accounts are added in small chunks instead of one by one.

## Vertex Embedding & Bio Analysis
I'm using [DeepWalk](https://arxiv.org/pdf/1403.6652.pdf), which is a vertex embedding technique similar to [word2vec](https://www.tensorflow.org/tutorials/text/word2vec). In graphs, *sentences* can be obtained with random walks. The embedding space is a continuous n-dimensional vector space. This representation is efficient and flexible. It also doesn't suffer from some of the problems caused by private accounts in the layout task. 

So far the random walks are taken with all edges having equal weight (probability). There are many ways to make the embedding more accurate:<ul>
  <li>Increase the weight of edges to smaller accounts. Connections to small accounts are likely more personal.</li>
  <li>Weight connections to accounts who engage with the user, eg. comment, like or tag on posts.</li>
</ul>

I'm looking to connecting information from the bios of the accounts to the embedding of the node. There are many common abbrevations and symbols such as 'CHEM' or §. These could be correlated with some dimensions in the embedding space. 
The bio of an account is visible regardless of its private status, so this could even be a way to have a high accuracy classification for private accounts as well.
