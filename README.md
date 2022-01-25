#### Group 4: Christian Berchtold, Dominic Meier
# Final Project: Image Board Analyser
### Main project description
An image board is a dataset of user generated messages, some of which contain images.
Our project consists of a bot that automatically fetches data about threads, posts, and posters from
an image board, then offers statistics and analytics on these.
For this project we choose a 4chan since it is has the most traffic and data.
### Back End
Tasks: Data Fetching, Data Analysis, Data Storage
Desription: The backend periodically (~ every 5min) fetches the data from an image
board via json. The json file contains all threads at that time. New threads
are added to the memory, existing threads are updated with the new posts,
pruned/deleted threads (= closed and no longer present) are taken from the
memory and stored in an SQL database (or any related flavor).
During idle time it analyzes the active threads in order to provide real time
analysis, such as: replies/min, # of unique users, reply count among posters,
posts with images, threads/hour, origin of poster, etc.
### Front End
Tasks: Webservice, Visualization, API
Description: The frontend is a separate instance and offers the API to provide access to
the analysis, converting it for the user as a webservice.
### Other goals, given the time
If we find ourselves having still a bit of time, we thought of creating a Machine Learning based
analyser. We not yet set our minds on what to use, not knowing what we will encounter and if it is
feasible. One idea would be latent semantic analysis for keyword extraction. Other unsupervised
methods might be considered as well. Further, we might conduct supervised learning based on our
own dataset, such as the early detection of trending/popular threads given the data once they are
pruned.
