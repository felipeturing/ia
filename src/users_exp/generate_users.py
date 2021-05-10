# importing the module
import random

users = []
with open('users.csv') as f:
    line = f.readline()
    while line:
        line = f.readline()
        users.append(line[:-1])

for user in users:
    friends = random.sample(users,random.randint(4 , 10))
    if user in friends:
        friends.remove(user)
        print ("Eliminada repeticion")
        
    print (user , ":" ,end='' )
    for friend in friends:
        print (friend , ";" ,end='')
    print ("\b\b" )

    

