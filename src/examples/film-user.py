import datetime, os, sys, re, time, rdfextras

try:
    import imdb
except ImportError:
    imdb = None

from rdflib import BNode, ConjunctiveGraph, URIRef, Literal, Namespace, RDF
from rdflib.namespace import FOAF, DC

storefn = os.path.expanduser("~/movies.n3")
userfn = os.path.expanduser("~/users.n3")

storeuri = "file://" + storefn
useruri = "file://" + userfn

title_store = "Movie Theater"
title_user  = "Fábrica de usuarios"

r_cinema = re.compile(
    r"^(.*?) <(((https|http)?):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+-=\\\.&]*)>$"
)

r_newuser = re.compile(
    r"^(.*?) <([a-z0-9_-]+(\.[a-z0-9_-]+)*@[a-z0-9_-]+(\.[a-z0-9_-]+)+)>$"
)

IMDB = Namespace("http://www.csd.abdn.ac.uk/~ggrimnes/dev/imdb/IMDB#")
REV = Namespace("http://purl.org/stuff/rev#")
REL = Namespace("https://www.perceive.net/schemas/20031015/relationship/")

class DoConjunctiveGraph:

    def __init__(self, pathfn, uri, title):
        self.title = title
        self.pathfn = pathfn
        self.uri = uri
        self.graph = ConjunctiveGraph() # instancia del grafo
        if os.path.exists(self.pathfn):
            self.graph.load(self.uri, format="n3")
        self.graph.bind("dc", DC) # Para enlazar los prefijos
        self.graph.bind("imdb", IMDB)
        self.graph.bind("rev", REV)

    def save(self):
        self.graph.serialize(self.uri, format="n3")

    def len(self): # Contar el numero de triples
        return self.graph.__len__()

    def help():
        print("Revisar : https://www.w3.org/TR/turtle/#BNode")


class UserFactory(DoConjunctiveGraph):

    def __init__(self, pathfn, uri, title):
        #self.title = "Fabrica de Usuarios"
        DoConjunctiveGraph.__init__(self, pathfn, uri, title)
        self.graph.bind("foaf", FOAF)
        self.graph.bind("rel", REL)
        self.graph.add((URIRef(self.uri), DC["title"], Literal(self.title)))
        self.save()

    def new_user(self, user_data=None):
        user_nick, user_email = (r_newuser.match(user_data).group(1), r_newuser.match(user_data).group(2))
        self.graph.add((URIRef(self.uri + "#%s"%user_nick), RDF.type, FOAF["Person"]))
        self.graph.add((URIRef(self.uri + "#%s"%user_nick), FOAF["nick"], Literal(user_nick)))
        self.graph.add((URIRef(self.uri + "#%s"%user_nick), FOAF["mbox"], Literal(user_email)))
        self.save()
        return user_nick # para poder trabajar con nick ya serializado en el archivo n3

    def set_user_name(self, user_nick, user_name):
        if not self.user_is_in(user_nick):
            raise Exception ("El nick %s no está registrado"%user_nick)
        self.graph.add((URIRef(self.uri + "#%s"%user_nick), FOAF["name"], Literal(user_name)))
        self.save()

    def set_friends(self, user_nick_me, user_nick_you):
        if not (self.user_is_in(user_nick_me) and self.user_is_in(user_nick_you)):
            raise Exception ("Algún amigo no está registrado")
        self.graph.add((URIRef(self.uri + "#%s"%user_nick_you), REL["friendOf"], URIRef(self.uri + "#%s"%user_nick_me)))
        self.graph.add((URIRef(self.uri + "#%s"%user_nick_me), REL["friendOf"], URIRef(self.uri + "#%s"%user_nick_you)))
        self.save()

    def list_friends(self):
        return self.graph.query(
            """ SELECT ?aname ?bname
                WHERE {
                    ?a rel:friendOf ?b .
                    ?a foaf:name ?aname .
                    ?b foaf:name ?bname .
                }""")

    def list_users(self):
        return self.graph.query(
            """ SELECT DISTINCT ?nick
                WHERE {
                    ?p foaf:nick ?nick .
                }""")

    def list_friends_of_nick(self, nick_user):
        return self.graph.query(
            """ SELECT DISTINCT ?nick
                WHERE {
                    ?p foaf:nick "%s" .
                    ?p rel:friendOf ?q .
                    ?q foaf:nick ?nick .
                }"""%nick_user)

    def get_user_uri(self, user_nick):
        return URIRef(self.uri + "#%s"%user_nick)
#        return self.graph.objects(URIRef(self.uri+"#felipeturing"), FOAF["name"])
    def user_by_nick(self, nick_user):
        return self.graph.query(
            """ SELECT ?nick ?name ?mbox
                WHERE {
                    ?p foaf:nick "%s" .
                    ?p foaf:nick ?nick .
                    ?p foaf:name ?name .
                    ?p foaf:mbox ?mbox .
                }"""%nick_user)

    def user_is_in(self, user_nick):
        return (URIRef(self.uri + "#%s"%user_nick), RDF.type, FOAF["Person"]) in self.graph


class Store(DoConjunctiveGraph):

    def __init__(self, pathfn, uri, title ):
        DoConjunctiveGraph.__init__(self, pathfn, uri, title)
        self.graph.add((URIRef(self.uri), DC["title"], Literal(self.title)))
        #self.save()

    def cinema(self, data=None):
        if data is not None:
            name_cinema, web_cinema = (r_cinema.match(data).group(1), r_cinema.match(data).group(2))
            self.graph.add((URIRef(self.uri + "#cinema"), RDF.type, FOAF["Organization"]))
            self.graph.add((URIRef(self.uri + "#cinema"), FOAF["name"], Literal(name_cinema)))
            self.graph.add((URIRef(self.uri + "#cinema"), FOAF["weblog"], Literal(web_cinema)))
            self.save()
        else:
            return self.graph.objects(URIRef(self.uri + "#cinema"), FOAF["name"])

    def listmovies(self):
        return self.graph.query(
            """ SELECT DISTINCT ?p ?title
                WHERE {
                    ?p a imdb:Movie .
                    ?p dc:title ?title .
                }""")


    def new_movie(self, movie):
        movieuri = URIRef("https://www.imdb.com/title/tt%s/" % movie.movieID)
        self.graph.add((movieuri, RDF.type, IMDB["Movie"]))
        self.graph.add((movieuri, DC["title"], Literal(movie["title"])))
        self.graph.add((movieuri, IMDB["year"], Literal(int(movie["year"]))))
        for director in movie["director"]:
            self.graph.add((movieuri, IMDB["director"], Literal(director)))
        for actor in (movie["cast"][0], movie["cast"][1]):
            self.graph.add((movieuri, IMDB["cast"], Literal(actor)))
        self.save()

    def movie_is_in(self, uri):
        return (URIRef(uri), RDF.type, IMDB["Movie"]) in self.graph

    def new_review(self, user_uri, movie_id, date, rating, comment=None):
        review = BNode()  # @@ humanize the identifier (something like #rev-$date)
        movieuri = URIRef("https://www.imdb.com/title/tt%s/" % movie_id)
        self.graph.add((movieuri, REV["hasReview"], URIRef("%s#%s" % (self.uri, review))))
        #self.graph.add((review, RDF.type, REV["Review"]))
        #self.graph.add((review, DC["date"], Literal(date)))
        #self.graph.add((review, REV["maxRating"], Literal(5)))
        #self.graph.add((review, REV["minRating"], Literal(0)))
        #self.graph.add((review, REV["reviewer"], user_uri))
        #self.graph.add((review, REV["rating"], Literal(rating)))
        self.graph.add((URIRef("%s#%s" % (self.uri, review)), RDF.type, REV["Review"]))
        self.graph.add((URIRef("%s#%s" % (self.uri, review)), DC["date"], Literal(date)))
        self.graph.add((URIRef("%s#%s" % (self.uri, review)), REV["maxRating"], Literal(5)))
        self.graph.add((URIRef("%s#%s" % (self.uri, review)), REV["minRating"], Literal(0)))
        self.graph.add((URIRef("%s#%s" % (self.uri, review)), REV["reviewer"], user_uri))
        self.graph.add((URIRef("%s#%s" % (self.uri, review)), REV["rating"], Literal(rating)))
        if comment is not None:
            self.graph.add((URIRef("%s#%s" % (self.uri, review)), REV["text"], Literal(comment)))
        self.save()

    def list_movies_user(self, user_uri):
        return self.graph.query(
            """ SELECT DISTINCT ?title
                WHERE {
                    ?p rev:reviewer %s%s%s .
                    ?movie rev:hasReview ?p .
                    ?movie dc:title ?title .
                }"""%("<",user_uri,">"))


def main(argv=None):

    if not argv:
        argv = sys.argv

    s = Store(storefn, storeuri, title_store)
    u = UserFactory(userfn, useruri, title_user)

    if argv[1] in ("help", "--help", "h", "-h"):
        help()
    elif argv[1] == "newuser":
        nick_user = r_newuser.match(argv[2]).group(1)
        if u.user_is_in(nick_user):
           raise Exception("El nick %s ya se encuentra registrado"%nick_user)
        else:
            nick_registered = u.new_user(argv[2])
            try:
                user_name = eval(input("Nombre: "))
                u.set_user_name(nick_registered, user_name)
            except:
                raise Exception ("Error al registrar el nombre de %s"%nick_registered)
    elif argv[1] == "setfriends" :
        u.set_friends(argv[2], argv[3])
    elif argv[1] == "triples":
        print(u.len())
    elif argv[1] == "listofusers":
        for user_name in u.list_users():
            print("%s"%user_name)
    elif argv[1] == "userbynick":
        for data_user in u.user_by_nick(argv[2]):
            print(" Nick : %s\n Nombre : %s\n Email : %s"%data_user)
    elif argv[1] == "listoffriends":
        for data_friend in u.list_friends():
            print("%s es amig@ de %s"%data_friend)
    elif argv[1] == "myfriends":
        for nick_friend in u.list_friends_of_nick(argv[2]):
            print("%s"%nick_friend)
    elif argv[1] == "cinema":
        if os.path.exists(storefn):
            print("Ya existe un cine registrado")
        else:
            s.cinema(argv[2])
    elif argv[1] == "newmovie":
        if argv[2].startswith("https://www.imdb.com/title/tt"):
            if s.movie_is_in(argv[2]):
                raise Exception ("La película ya se encuentra registrada")
            else:
                i = imdb.IMDb()
                movie = i.get_movie(argv[2][len("https://www.imdb.com/title/tt") : -1])
                print("%s (%s)" % (movie["title"].encode("utf-8"), movie["year"]))
                for director in movie["director"]:
                    print("Dirigida por: %s" % director["name"].encode("utf-8"))
                print("Actores principales:")
                for actor in (movie["cast"][0], movie["cast"][1]):
                    print("%s como %s" % (actor["name"].encode("utf-8"),actor.currentRole))
                s.new_movie(movie) #Registrar la cabecera de la pelicula (nombre, fecha de revision, tipo de objeto)
        else: raise Exception("El formato de la película debe ser https://www.imdb.com/title/tt[id]/")

    elif argv[1] == "usermovie":
        if u.user_is_in(argv[2]) and s.movie_is_in(argv[3]):
            user_uri = u.get_user_uri(argv[2])
            movie_id = argv[3][len("https://www.imdb.com/title/tt") : -1]
            rating = None
            while not rating or (rating > 5 or rating <= 0):
                try:
                    rating = int(eval(input("Valoración (max 5): ")))
                except ValueError:
                    rating = None
            date = None
            while not date:
                try:
                    i = eval(input("Fecha de visualización (YYYY-MM-DD): "))
                    date = datetime.datetime(*time.strptime(i, "%Y-%m-%d")[:6])
                except:
                    date = None
            comment = eval(input("Comentario: "))
            s.new_review(user_uri, movie_id, date, rating, comment) # Se regitra el detalle de la revision de la pelicula

    elif argv[1] == "listofmovies":
        for movie in s.listmovies():
            print("%s - %s"%movie)

    elif argv[1] == "recommendtome":
        """ Peliculas clasificadas por amigos """
        """for nick_friend in u.list_friends_of_nick(argv[2]):
            print("Amig@ : %s"%nick_friend)
            friend_uri = u.get_user_uri(nick_friend)
            for movie_user in s.list_movies_user(friend_uri):
                print("  %s"%movie_user)"""
        for nick_friend in u.list_friends_of_nick(argv[2]):
            for movie_user in s.list_movies_user(u.get_user_uri(nick_friend)):
                print("  %s"%movie_user)


    else: print("Sin acciones")

if __name__ == "__main__":
    if not imdb:
        raise Exception(
            'This example requires the IMDB library! Install with "pip install imdbpy"'
        )
    main()


"""
from rdflib import Graph
g = Graph()
g.parse('dicom.owl')
q =
[poner 3 comillas] SELECT ?c WHERE { ?c rdf:type owl:Class .
       FILTER (!isBlank(?c)) } [poner 3 comillas]

qres = g.query(q)

"""

"""
References :
    RDF 1.1 Turtle : https://www.w3.org/TR/turtle/
    FOAF specification : http://xmlns.com/foaf/spec/
    rdflib.graph.Graph : https://rdflib.readthedocs.io/en/stable/apidocs/rdflib.html#rdflib.graph.Graph
    IMDB roles : https://imdbpy.readthedocs.io/en/latest/usage/role.html
    Querying with SPARQL : https://rdflib.readthedocs.io/en/stable/intro_to_sparql.html
    Working with SPARQL : https://rdfextras.readthedocs.io/en/latest/working_with.html
"""
