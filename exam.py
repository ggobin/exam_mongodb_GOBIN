from pymongo import MongoClient
from pprint import pprint

outputfile = "res.txt"

def write_init_message(message):
    with open(outputfile, "w", encoding="utf-8") as file:
        file.write(message + "\n\n")
        
def write_message(message):
    with open(outputfile, "a", encoding="utf-8") as file:
        file.write(message + "\n\n")
    
def write_response_list(cursor, question):
    with open(outputfile, "a", encoding="utf-8") as file:
        file.write(str(question)  + "\n")
        for c in cursor:
            file.write(str(c)  + "\n")
        file.write("\n")
        
def write_response_int(valeur, question):
    with open(outputfile, "a", encoding="utf-8") as file:
        file.write(str(question)  + "\n")
        file.write(str(valeur)  + "\n")
        file.write("\n")

write_init_message("Exam_Mongodb_GOBIN :")
    
# (a) Pour se connecter à MongoDB via pymongo, ajoutez l'authentification aux lignes de codes suivantes puis lancez-les
client = MongoClient(
    host="127.0.0.1",
    port = 27017,
    username = "datascientest",
    password = "dst123"
)

# (b)Afficher la liste des bases de données disponibles.
write_response_list(client.list_database_names(),"# (b) Afficher la liste des bases de données disponibles")

# (c) Afficher la liste des collections disponibles dans cette base de données.
sample = client["sample"]
write_response_list(sample.list_collection_names(),"# (c) Afficher la liste des collections disponibles dans cette base de données.")

# (d) Afficher un des documents de cette collection.
write_response_list(sample["books"].find_one(),"# (d) Afficher un des documents de cette collection.")

# (e) Afficher le nombre de documents dans cette collection
write_response_int(sample["books"].count_documents({}),"# (e) Afficher le nombre de documents dans cette collection")

write_message("##### Exploration de la base ######")

# (a1) Afficher le nombre de livres avec plus de 400 pages, 
nb_doc = sample["books"].count_documents(
        {"pageCount": {"$gte": 400}},
    )
write_response_int(nb_doc,"# (a1) Afficher le nombre de livres avec plus de 400 pages")

# (a2) affichez ensuite le nombre de livres ayant plus de 400 pages ET qui sont publiés.
nb_doc = sample["books"].count_documents(
        {
            "$and": [
                {"pageCount": {"$gte": 400}},
                {"status": "PUBLISH"},
            ]
        }
    )
write_response_int(nb_doc,"# (a2) affichez ensuite le nombre de livres ayant plus de 400 pages ET qui sont publiés.")

# (b) Afficher le nombre de livres ayant le mot-clé Android dans leur description (brève ou longue).
nb_doc = sample["books"].count_documents(
        {
            "$or": [
                {"shortDescription":{"$regex": "Android"}},
                {"longDescription":{"$regex": "Android"}}
            ]
        }
    )
write_response_int(nb_doc,"# (b) Afficher le nombre de livres ayant le mot-clé Android dans leur description (brève ou longue).")

# (c) Chaque document possède un attribut categories qui est une liste. 
# Vous devez grouper tous les documents en un à l'aide de l'opérateur $group. 
# Puis, à l'aide de l'opérateur $addToSet, créez 2 set à partir des catégories contenus dans la liste categories selon leur index 0 ou 1. 
# Pour cibler, les catégories utilisez l'opérateur $arrayElemAt.

cursor = sample["books"].aggregate(
            [
                {"$group": {"_id":None, 
                        "categorie_0": {
                            "$addToSet": {
                                "$arrayElemAt":["$categories",0]
                            }
                        },
                        "categorie_1":{
                            "$addToSet": {
                                "$arrayElemAt":["$categories",1]
                            }
                        }}
                
                },
                {"$project" :{ "_id":0, "categorie_0":1, "categorie_1":1}}
                # Affiche uniquement 20 lignes de chaque catégorie afin de vérifier que l'agrégat retourne bien les deux catégories.
                #{"$project" :{ "_id":0, "categorie_0":{"$slice":["$categorie_0",20]}, "categorie_1":{"$slice":["$categorie_1",20]}}},
            ]
        )

write_response_list(cursor,"# (c) afficher la liste des deux categories selon leur index 0 ou 1.")

# (d) Afficher le nombre de livres qui contiennent des noms de langages suivant dans leur description longue : 
# Python, Java, C++, Scala. 
# On pourra s'appuyer sur des expressions régulières et une condition or.
nb_livres = sample["books"].count_documents(
        {"longDescription":{"$regex": "Python|Java|C++|Scala"}}
)

write_response_int(nb_livres,"# (d) Afficher le nombre de livres qui contiennent des noms de langages suivant dans leur description longue.")

# (e) Afficher diverses informations statistiques sur notre bases de données : 
# nombre maximal, minimal, et moyen de pages par catégorie. 
# On utilisera une pipeline d'aggregation, le mot clef $group, ainsi que les accumulateurs appropriés. 
# N'oubliez pas d'aller voir "$unwind" pour ce problème.
cursor = sample["books"].aggregate(
            [
                {"$unwind": "$categories"},
                {"$group": {"_id":"$categories",
                           "nb_max":{"$max" :"$pageCount"}, 
                           "nm_min":{"$min":"$pageCount"},
                           "avg":{"$avg":"$pageCount"}
                           }
                },
            ]
        )

write_response_list(cursor,"# (e) Afficher diverses informations statistiques sur notre bases de données.")

# (f) Via une pipeline d'aggrégation, Créer de nouvelles variables en extrayant info 
# depuis l'attribut dates : année, mois, jour. On rajoutera une condition pour filtrer seulement les livres publiés après 2009. 
# N'affichez que les 20 premiers.

pipeline = [
            {"$project": {
                  "year": {"$year": "$publishedDate"},
                  "month": {"$month": "$publishedDate"},
                  "day": {"$dayOfMonth": "$publishedDate"}
                  }
            },
            {"$match": {
                  "year": {"$gte": 2009}
                  }},
            {"$limit": 20}
]

cursor = sample["books"].aggregate(pipeline)
write_response_list(cursor,"# (f) Via une pipeline d'aggrégation, Créer de nouvelles variables en extrayant info ")

# (g) À partir de la liste des auteurs, créez de nouveaux attributs (author_1, author_2 ... author_n). 
# Observez le comportement de "$arrayElemAt". N'affichez que les 20 premiers dans l'ordre chronologique.

# Récupération du nombre maximum d'auteurs dans tous les documents
nb_auteurs = list(sample["books"].aggregate(
        [
            {"$project": {
                "nb_auteur" : {"$size":"$authors"}
                }
            },
            {
            "$group": {"_id":0,"nb_autheur":{"$max":"$nb_auteur"}}
            },
        ]
    )
)
#print("Nombre maximum d'auteurs par document :", nb_auteurs)

# Création d'un pipeline pour créer les nouvelles colonnes
# Question : Comment rendre la création des attributs dynamiques ?
pipeline = [
    {"$set": {
        "author_1": {"$arrayElemAt":["$authors",0]},
        "author_2": {"$arrayElemAt":["$authors",1]},
        "author_3": {"$arrayElemAt":["$authors",2]},
        "author_4": {"$arrayElemAt":["$authors",3]},
        "author_5": {"$arrayElemAt":["$authors",4]},
        "author_6": {"$arrayElemAt":["$authors",5]},
        "author_7": {"$arrayElemAt":["$authors",6]},
        "author_8": {"$arrayElemAt":["$authors",7]}
    }},
    {"$limit": 20},
    {"$sort":{"publishedDate":1}},
    {"$merge":"books"} # applique la création sur la collection
]
sample["books"].aggregate(pipeline)
cursor = sample["books"].find({}).limit(20)
write_response_list(cursor,"# (g) À partir de la liste des auteurs, créez de nouveaux attributs (author_1, author_2 ... author_n).")

#(h) En s'inspirant de la requête précédente, créer une colonne contenant le nom du premier auteur, 
# puis agréger selon cette colonne pour obtenir le nombre d'articles pour chaque premier auteur. 
# Afficher le nombre de publications pour les 10 premiers auteurs les plus prolifiques. 
# On pourra utiliser un pipeline d'agrégation avec les mots-clefs $group, $sort, $limit.

#Creation d'un pipeline d'agrégation
pipeline = [
    {"$set": {
        "author_1": {"$arrayElemAt":["$authors",0]},
    }},
    {"$group": {
        "_id":"$author_1", "nb_artcile":{"$sum":1}
    }},
    {"$sort":{"nb_artcile":-1}},
    {"$limit":10}
]

cursor = sample["books"].aggregate(pipeline)
write_response_list(cursor,"# (h) Afficher le nombre de publications pour les 10 premiers auteurs les plus prolifiques. ")

#(i) [OPTIONNEL] Afficher la distribution du nombre d'auteurs : 
# Commencer par créer une nouvelle colonne avec le nombre d'auteurs (taille de la liste de l'attribut authors ), 
# puis agrégez sur cette colonne avec l'accumulateur $count ou $sum.

#Creation d'un pipeline d'agrégation
pipeline = [
    {"$set": {
        "nb_author": {"$size":"$authors"},
    }},
    {"$group": {
        "_id":"$nb_author", "dist":{"$sum":1}
    }},
    # Question : Comment définir l'ordre d'affichage ? Dans ce cas, la distribution s'affiche avant le nb auteur.
    {"$project": {"_id":0, "nb_author":"$_id","dist":1}}, 
    {"$sort":{"dist":-1}}
]

cursor = sample["books"].aggregate(pipeline)
write_response_list(cursor,"#(i) [OPTIONNEL] Afficher la distribution du nombre d'auteurs")

#(j) [OPTIONNEL] Afficher l'occurence de chaque auteur selon son index dans l'attribut "authors".
# Un même auteur peut avoir plusieurs index. 
# N'affichez pas les auteurs vides, sortez par ordre d'occurence décroissant avec une limite de 20. 
# Utilisez "$unwind" pour séparer les auteurs et "$project" pour supprimer les auteurs absents.

cursor = sample["books"].aggregate(
            [
                {"$unwind": "$authors"},
                {"$group": {"_id":"$authors","nb_occurence":{"$sum":1}}},
                {"$project": {"_id":0, "author":"$_id", "nb_occurence":1}},
                {"$match":{"author": {"$ne":""}}},
                {"$sort":{"nb_occurence":-1}},
                {"$limit":10}
            ]
        )

write_response_list(cursor,"#(j) [OPTIONNEL] Afficher l'occurence de chaque auteur selon son index dans l'attribut 'authors'.")