# CC421 PC1

## RDF

RDF es un "Framework" para la descripción de recursos de la Web Semántica, presenta múltiples formatos, nosotros vamos a emplear el formato N3 para la descripción de triples.

## Objetivo

El objetivo de este trabajo es manipular una estructura RDF/N3 de usuarios y películas a partir de principalmente IMDb y FOAF para describir los recursos en un dominio determinado.

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

## Equipo
1. Jesús Andrés Torrejón León
2. Jordi Joel Bardales Rojas
3. Walter Jesús Felipe Tolentino
4. Julio César Yaranga Santé
