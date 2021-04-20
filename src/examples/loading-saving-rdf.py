from rdflib import Graph
g = Graph()
g.parse("./foaf-example.rdf") #format by default is RDF/XML but there's exists n3, ntriples, trix, JSON-LD, etc

for s, p, o in g:
    print((o))
    print("\n")

print(len(g))
# prints 62
