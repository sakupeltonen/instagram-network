# instagram-network

![graph](pics/force-directed8.pdf)

## Data Collection
The data was gathered using Selenium WebDriver. The crawler has gathered over 300 000 connections, which corresponds to about a thousand users.

Collected attributes include:
<ul>
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
Each user is a vertex, and connections between users are edges. For now, the graph is handled as an undirected graph. The layout is calculated with using a [force-directed algorithm](https://networkx.org/documentation/stable/reference/generated/networkx.drawing.layout.spring_layout.html#networkx.drawing.layout.spring_layout) from networkx. 
