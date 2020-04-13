import src/cli
from src/rdf_extracts import getTypes

# cli.run()

types = getTypes()
for result in types["results"]["bindings"]:
    print(result["label"]["value"])
