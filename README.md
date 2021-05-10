# CC421 PC1

## RDF

RDF es un "Framework" para la descripción de recursos de la Web Semántica, presenta múltiples formatos, nosotros vamos a emplear el formato N3 para la descripción de triples.

## Objetivo

El objetivo de este trabajo es manipular una estructura RDF/N3 de usuarios y películas a partir de principalmente IMDb y FOAF para describir y consultar con SparQL los recursos en un dominio determinado.

## Instalación

```bash
pip install rdflib
pip install imdbpy
```

## Importaciones

```python
import datetime, os, sys, re, time
import numpy as np

try:
    import imdb
except ImportError:
    imdb = None

from tabulate import tabulate
from pprintpp import pprint
from rdflib import BNode, ConjunctiveGraph, URIRef, Literal, Namespace, RDF
from rdflib.namespace import FOAF, DC
```
## Instrucciones para la manipulación de RDF
```bash
!python3 film-user.py cinema   "Cinestar <https://www.cinestar.com.pe/>"
python3 film-user.py newmovie "https://www.imdb.com/title/tt0102926/"
python3 film-user.py newuser  "felipe31415 <felipe@uni.pe>"
python3 film-user.py newuser  "jesus15 <jesus@uni.pe>"
python3 film-user.py setfriends "jesus15" "felipe31415"
python3 film-user.py listofusers
python3 film-user.py listoffriends
python3 film-user.py userbynick "jesus15"
python3 film-user.py myfriends "felipe31415"
python3 film-user.py newmovie "https://www.imdb.com/title/tt2980516/"
python3 film-user.py listofmovies
python3 film-user.py review "jesus15" "The Theory of Everything"
python3 film-user.py moviebyurl "<https://www.imdb.com/title/tt0468569/>"
python3 film-user.py recommendtome "felipe31415"
python3 film-user.py topratedmovies  0 10
```

## Equipo
1. Jesús Andrés Torrejón León
2. Jordi Joel Bardales Rojas
3. Walter Jesús Felipe Tolentino
4. Julio César Yaranga Santé
