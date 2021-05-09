# importamos lo necesario para el formato de la entrada
import datetime
import os
import sys
import re
import time
import numpy as np

try:
    import imdb
except ImportError:
    imdb = None

from tabulate import tabulate
from pprintpp import pprint
# blank node
# a ConjunctiveGraph is an aggregation of all the named graphs in a store.
from rdflib import BNode, ConjunctiveGraph, URIRef, Literal, Namespace, RDF
# importamos FOAF: viene del acronimo Friend Of Friend, el cual es utilizado para describir relacion entre personas tales como en una red social.
from rdflib.namespace import FOAF, DC


storefn = os.path.expanduser("~/movies.n3")
userfn = os.path.expanduser("~/users.n3")

storeuri = "file://" + storefn
useruri = "file://" + userfn

title_store = "Movie Theater"
title_user = "Fábrica de usuarios"

r_cinema = re.compile(
    r"^(.*?) <(((https|http)?):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+-=\\\.&]*)>$"
)

r_newuser = re.compile(
    r"^(.*?) <([a-z0-9_-]+(\.[a-z0-9_-]+)*@[a-z0-9_-]+(\.[a-z0-9_-]+)+)>$"
)

IMDB = Namespace("http://www.csd.abdn.ac.uk/~ggrimnes/dev/imdb/IMDB#")
# predicate: vocabulary for expressing reviews and ratings using the RDF
REV = Namespace("http://purl.org/stuff/rev#")
# predicate: friendship relationship
REL = Namespace("https://www.perceive.net/schemas/20031015/relationship/")


class DoConjunctiveGraph:

    def __init__(self, pathfn, uri, title):
        self.title = title
        self.pathfn = pathfn
        self.uri = uri
        self.graph = ConjunctiveGraph()  # instancia del grafo

        if os.path.exists(self.pathfn):
            self.graph.load(self.uri, format="n3")

        # enlaza los prefijos para el namespace
        self.graph.bind("dc", DC)  # Para enlazar los prefijos
        self.graph.bind("imdb", IMDB)
        self.graph.bind("rev", REV)

    def save(self):
        self.graph.serialize(self.uri, format="n3")

    def len(self):  # Contar el numero de triples
        return self.graph.__len__()

    def help():
        print("Revisar : https://www.w3.org/TR/turtle/#BNode")


class UserFactory(DoConjunctiveGraph):

    def __init__(self, pathfn, uri, title):
        #self.title = "Fabrica de Usuarios"
        DoConjunctiveGraph.__init__(self, pathfn, uri, title)
        # enlazamos las relaciones
        self.graph.bind("foaf", FOAF)
        self.graph.bind("rel", REL)
        # agregamos el triple del titulo cuando se inicializa
        self.graph.add((URIRef(self.uri), DC["title"], Literal(self.title)))
        # self.save()

    def new_user(self, user_data=None):
        # al agregar un usuario verificamos que sea de acuerdo a la expresion regular
        user_nick, user_email = (r_newuser.match(user_data).group(
            1), r_newuser.match(user_data).group(2))
        # agregamos el triple que corresponde con el usuario su nick y su correo al sujeto se le concatena su nickname para darle una identidad
        self.graph.add((URIRef(self.uri + "#%s" %
                       user_nick), RDF.type, FOAF["Person"]))
        self.graph.add((URIRef(self.uri + "#%s" % user_nick),
                       FOAF["nick"], Literal(user_nick)))
        self.graph.add((URIRef(self.uri + "#%s" % user_nick),
                       FOAF["mbox"], Literal(user_email)))

        # este metodo llama al serialize el cual lo guarda en este directorio
        self.save()
        return user_nick  # para poder trabajar con nick ya serializado en el archivo n3

    def set_user_name(self, user_nick, user_name):
        if not self.user_is_in(user_nick):
            raise Exception("El nick %s no está registrado" % user_nick)
        # agregamos el triple de tipo FOAF que agrega el username
        self.graph.add((URIRef(self.uri + "#%s" % user_nick),
                       FOAF["name"], Literal(user_name)))
        self.save()

    def set_friends(self, user_nick_me, user_nick_you):
        if not (self.user_is_in(user_nick_me) and self.user_is_in(user_nick_you)):
            raise Exception("Algún amigo no está registrado")
        # agregamos dos triples que indican la amistad entre las personas, las cuales estaran asociadas a los sujetos
        self.graph.add((URIRef(self.uri + "#%s" % user_nick_you),
                       REL["friendOf"], URIRef(self.uri + "#%s" % user_nick_me)))
        self.graph.add((URIRef(self.uri + "#%s" % user_nick_me),
                       REL["friendOf"], URIRef(self.uri + "#%s" % user_nick_you)))
        self.save()

    def list_friends(self):
        # rdflib permite hacer sparql
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
                }""" % nick_user)

    def get_user_uri(self, user_nick):
        return URIRef(self.uri + "#%s" % user_nick)
#        return self.graph.objects(URIRef(self.uri+"#felipeturing"), FOAF["name"])

    def user_by_nick(self, nick_user):
        return self.graph.query(
            """ SELECT ?nick ?name ?mbox
                WHERE {
                    ?p foaf:nick "%s" .
                    ?p foaf:nick ?nick .
                    ?p foaf:name ?name .
                    ?p foaf:mbox ?mbox .
                }""" % nick_user)

    def user_is_in(self, user_nick):
        # verifica si el triple de tipo persona con nick_name esta en el grafo
        return (URIRef(self.uri + "#%s" % user_nick), RDF.type, FOAF["Person"]) in self.graph

    def show_user_digraph(self, flag):
        return flag


class Store(DoConjunctiveGraph):

    def __init__(self, pathfn, uri, title):
        DoConjunctiveGraph.__init__(self, pathfn, uri, title)
        # cuando inicializamos agrega el triple con predicado Titulo
        self.graph.add((URIRef(self.uri), DC["title"], Literal(self.title)))
        # self.save()

    def cinema(self, data=None):
        if data is not None:
            # extraemos información de la entrada gracias a la expresion regular
            name_cinema, web_cinema = (r_cinema.match(
                data).group(1), r_cinema.match(data).group(2))
            self.graph.add((URIRef(self.uri + "#cinema"),
                           RDF.type, FOAF["Organization"]))
            self.graph.add((URIRef(self.uri + "#cinema"),
                           FOAF["name"], Literal(name_cinema)))
            self.graph.add((URIRef(self.uri + "#cinema"),
                           FOAF["weblog"], Literal(web_cinema)))
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

    def data_movie_by_uri(self, movie_uri):
        return self.graph.query(
            """ SELECT ?title ?year
                WHERE {
                    %s%s%s dc:title ?title .
                    %s%s%s imdb:year ?year .
                }""" % ("<", movie_uri, ">", "<", movie_uri, ">"))

    def movie_uri_by_title(self, movie_title):
        return self.graph.query(
            """ SELECT DISTINCT ?p
                WHERE {
                    ?p dc:title "%s" .
                }""" % movie_title)

    def top_rated_movies(self, offset, limit, m):
        C = self.graph.query(
            """ SELECT (AVG(?rating) as ?R)
                WHERE {
                    ?url rev:hasReview ?review .
                    ?review a rev:Review .
                    ?review rev:rating ?rating .
                }""")
        C = float("%s" % list(C)[0])
# weighted rating (WR) = (v ÷ (v+m)) × R + (m ÷ (v+m)) × C
        return self.graph.query(
            """ SELECT (?title AS ?pelicula)
                       (COUNT(?review) AS ?v)
                       (AVG(?rating) AS ?R)
                       (
                            (
                             (COUNT(?review)/(COUNT(?review)+%d))*AVG(?rating) +
                             (%d            /(COUNT(?review)+%d))*%.4f
                            )
                            AS ?IMDbRating
                        )

                WHERE {
                    ?url rev:hasReview ?review .
                    ?url dc:title ?title .
                    ?review a rev:Review .
                    ?review rev:rating ?rating .
                }
                GROUP BY ?title
                ORDER BY DESC(?IMDbRating)
                LIMIT %s
                OFFSET %s""" % (m, m, m, C, limit, offset))

    def new_movie(self, movie):
        movieuri = URIRef("https://www.imdb.com/title/tt%s/" % movie.movieID)
        self.graph.add((movieuri, RDF.type, IMDB["Movie"]))
        self.graph.add((movieuri, DC["title"], Literal(movie["title"])))
        self.graph.add((movieuri, IMDB["year"], Literal(int(movie["year"]))))
        for genres in movie["genres"]:
            self.graph.add((movieuri, IMDB["genres"], Literal(genres)))
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
        self.graph.add(
            (movieuri, REV["hasReview"], URIRef("%s#%s" % (self.uri, review))))
        #self.graph.add((review, RDF.type, REV["Review"]))
        #self.graph.add((review, DC["date"], Literal(date)))
        #self.graph.add((review, REV["maxRating"], Literal(5)))
        #self.graph.add((review, REV["minRating"], Literal(0)))
        #self.graph.add((review, REV["reviewer"], user_uri))
        #self.graph.add((review, REV["rating"], Literal(rating)))
        self.graph.add(
            (URIRef("%s#%s" % (self.uri, review)), RDF.type, REV["Review"]))
        self.graph.add((URIRef("%s#%s" % (self.uri, review)),
                       DC["date"], Literal(date)))
        self.graph.add((URIRef("%s#%s" % (self.uri, review)),
                       REV["maxRating"], Literal(5)))
        self.graph.add((URIRef("%s#%s" % (self.uri, review)),
                       REV["minRating"], Literal(0)))
        self.graph.add((URIRef("%s#%s" % (self.uri, review)),
                       REV["reviewer"], user_uri))
        self.graph.add((URIRef("%s#%s" % (self.uri, review)),
                       REV["rating"], Literal(rating)))
        if comment is not None:
            self.graph.add((URIRef("%s#%s" % (self.uri, review)),
                           REV["text"], Literal(comment)))
        self.save()

    def list_movies_user(self, user_uri):
        return self.graph.query(
            """ SELECT DISTINCT ?title
                WHERE {
                    ?p rev:reviewer %s%s%s .
                    ?movie rev:hasReview ?p .
                    ?movie dc:title ?title .
                }""" % ("<", user_uri, ">"))


def main(argv=None):

    if not argv:
        argv = sys.argv

    s = Store(storefn, storeuri, title_store)
    u = UserFactory(userfn, useruri, title_user)

    if len(argv) > 1:
        if argv[1] in ("help", "--help", "h", "-h"):
            help()
        elif argv[1] == "newuser":
            nick_user = r_newuser.match(argv[2]).group(1)
            if u.user_is_in(nick_user):
                raise Exception(
                    "El nick %s ya se encuentra registrado" % nick_user)
            else:
                nick_registered = u.new_user(argv[2])
                try:
                    user_name = eval(input("Nombre: "))
                    u.set_user_name(nick_registered, user_name)
                except:
                    raise Exception(
                        "Error al registrar el nombre de %s" % nick_registered)
        elif argv[1] == "setfriends":
            u.set_friends(argv[2], argv[3])
        elif argv[1] == "triplesusersn3":
            print(u.len())
        elif argv[1] == "triplesmoviesn3":
            print(s.len())
        elif argv[1] == "listofusers":
            for user_name in u.list_users():
                print("%s" % str(user_name))
        elif argv[1] == "userbynick":
            for data_user in u.user_by_nick(argv[2]):
                print(" Nick : %s\n Nombre : %s\n Email : %s" % data_user)
        elif argv[1] == "listoffriends":
            for data_friend in u.list_friends():
                print("%s es amig@ de %s" % data_friend)
        elif argv[1] == "myfriends":
            for nick_friend in u.list_friends_of_nick(argv[2]):
                print("%s" % nick_friend)
        elif argv[1] == "cinema":
            if os.path.exists(storefn):
                print("Ya existe un cine registrado")
            else:
                s.cinema(argv[2])
        elif argv[1] == "newmovie":
            if argv[2].startswith("https://www.imdb.com/title/tt"):
                if s.movie_is_in(argv[2]):
                    print("La película ya se encuentra registrada")
                else:
                    i = imdb.IMDb()
                    movie = i.get_movie(
                        argv[2][len("https://www.imdb.com/title/tt"): -1])
                    print("Película : %s" % movie["title"].encode("utf-8"))
                    print("Año : %s" % movie["year"])
                    print("Género : ", end=" ")
                    for genre in movie["genres"]:
                        print("%s" % genre, end=" ")
                    print("")
                    for director in movie["director"]:
                        print("Dirigida por: %s" %
                              director["name"].encode("utf-8"))
                    print("Actores principales:")
                    for actor in (movie["cast"][0], movie["cast"][1]):
                        print("%s como %s" %
                              (actor["name"].encode("utf-8"), actor.currentRole))
                    # Registrar la cabecera de la pelicula (nombre, fecha de revision, tipo de objeto, director, genero y actores principales)
                    s.new_movie(movie)           
            else:
                raise Exception(
                    "El formato de la película debe ser https://www.imdb.com/title/tt[id]/")

        elif argv[1] == "review":
            if not len(list(s.movie_uri_by_title(argv[3]))) == 0:
                movie_uri = "%s" % list(s.movie_uri_by_title(argv[3]))[0]
                if u.user_is_in(argv[2]) and s.movie_is_in(movie_uri):
                    user_uri = u.get_user_uri(argv[2])
                    movie_id = movie_uri[len(
                        "https://www.imdb.com/title/tt"): -1]
                    rating = None
                    print("Película : %s \t Año: %s" %
                          list(s.data_movie_by_uri(movie_uri))[0])
                    while not rating or (rating > 5 or rating <= 0):
                        try:
                            rating = int(eval(input("Valoración (max 5): ")))
                        except ValueError:
                            rating = None
                    date = None
                    while not date:
                        try:
                            i = eval(
                                input("Fecha de visualización (YYYY-MM-DD): "))
                            date = datetime.datetime(
                                *time.strptime(i, "%Y-%m-%d")[:6])
                        except:
                            date = None
                    comment = eval(input("Comentario: "))
                    s.new_review(user_uri, movie_id, date, rating, comment)
            else:
                print("Película no encontrada")

        elif argv[1] == "listofmovies":
            for movie in s.listmovies():
                print("%s - %s" % movie)

        elif argv[1] == "recommendtome":
            """ Peliculas clasificadas por amigos """
            """for nick_friend in u.list_friends_of_nick(argv[2]):
                print("Amig@ : %s"%nick_friend)
                friend_uri = u.get_user_uri(nick_friend)
                for movie_user in s.list_movies_user(friend_uri):
                    print("  %s"%movie_user)"""
            for nick_friend in u.list_friends_of_nick(argv[2]):
                for movie_user in s.list_movies_user(u.get_user_uri(nick_friend)):
                    print("  %s" % movie_user)
        elif argv[1] == "topratedmovies":
            table = np.array(
                [["Película", "Número de reviews", "Valoración promedio(0-5)", "IMDb Rating"]])
            m = 2  # minimo de reviews requeridas para ingresar en la lista top de recomendados
            for movie in s.top_rated_movies(argv[2], argv[3], m):
                if(int(movie[1]) >= m):
                    table = np.append(table, [movie], axis=0)
            print(tabulate(np.delete(table, 0, axis=0),
                  table[0], tablefmt="fancy_grid", numalign="right", floatfmt=".1f"))
        
        elif argv[1] == "user_digraph":
            print(u.show_user_digraph(argv[2]))
        
        else:
            print("Bandera no reconocida")
    else:
        print("Sin acciones")


if __name__ == "__main__":
    if not imdb:
        raise Exception(
            'This example requires the IMDB library! Install with "pip install imdbpy"'
        )
    main()


"""
REMARK 1 :
    from rdflib import Graph
    g = Graph()
    g.parse('dicom.owl')
    q =
    [poner 3 comillas] SELECT ?c WHERE { ?c rdf:type owl:Class .
           FILTER (!isBlank(?c)) } [poner 3 comillas]

    qres = g.query(q)

"""
"""
REMARK 2 :
    weighted rating (WR) = (v ÷ (v+m)) × R + (m ÷ (v+m)) × C

    Where:

    R = average for the movie (mean) = (Rating)
    v = number of votes for the movie = (votes)
    m = minimum votes required to be listed in the Top 250 (currently 25,000)
    C = the mean vote across the whole report
"""

"""
REMARK 3 :
    References :
        RDF 1.1 Turtle : https://www.w3.org/TR/turtle/
        FOAF specification : http://xmlns.com/foaf/spec/
        rdflib.graph.Graph : https://rdflib.readthedocs.io/en/stable/apidocs/rdflib.html#rdflib.graph.Graph
        IMDB roles : https://imdbpy.readthedocs.io/en/latest/usage/role.html
        SPARQL Query Language for RDF : https://www.w3.org/TR/rdf-sparql-query/#modDistinct
        Querying with SPARQL : https://rdflib.readthedocs.io/en/stable/intro_to_sparql.html
        Working with SPARQL : https://rdfextras.readthedocs.io/en/latest/working_with.html
"""
