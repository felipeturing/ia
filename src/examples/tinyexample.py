import rdflib

g = rdflib.Graph()

result = g.parse("http://www.w3.org/People/Berners-Lee/card");

for subject, predicate, obj in g:
#    print("subject : " + subject + " predicate : " + predicate + "object" + obj)
    if(subject, predicate, obj) not in g:
        raise Exception("Could be better")

print("graph has {} statements.".format(len(g)))
print(g.serialize(format="turtle").decode("utf-8"))
