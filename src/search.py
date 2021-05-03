# importing the module

import imdb

ia = imdb.IMDb()

def imdb_code (movie_name):
    search = ia.search_movie(movie_name)
    if(len(search) >=  1) : 
        id = search[0].movieID      
        print(search[0]['title'] + " : " + id )



with open('list.txt') as f:
    line = f.readline()
    while line:
        line = f.readline()
        #print(line)
        imdb_code(line)
        

