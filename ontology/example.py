"""
This file shows how to load/interact with the COVID-19 ontology
"""
import rdflib
import owlrl


class COVID19Graph:
    def __init__(self):
        self.g = rdflib.Graph()
        self.g.parse('ontology.ttl', format='ttl')

    def _to_rdflib_ident(self, s):
        try:
            if s.startswith("http"):
                return rdflib.URIRef(s)
            else:
                return rdflib.BNode(s)
        except Exception:
            return rdflib.Literal(s)

    def add_file(self, filename):
        """
        Load contents of file into graph
        """
        self.g.parse(filename, format='ttl')
        owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(self.g)

    def query(self, query):
        return list(self.g.query(query))

    def dump_query(self, query):
        """
        Pretty-prints query results
        """
        for r in self.query(query):
            print(r)


if __name__ == '__main__':
    g = COVID19Graph()
    g.add_file('example.ttl')

    # get all entities
    print("All entities:")
    g.dump_query("""SELECT ?ent WHERE {
        ?ent a covid:Entity
    }""")

    # get all entities with tests
    print()
    print("All entities w/ positive tests:")
    g.dump_query("""SELECT ?ent ?test ?time WHERE {
        ?ent a covid:Entity .
        ?test a covid:Test .
        ?ent covid:hasTest ?test .
        ?test covid:testedPositive true .
        ?test covid:hasTime ?time
    }""")

    # get all interactions w/ at least 1 positive-testing entity
    print()
    print("All interactions w/ positive entities")
    g.dump_query("""SELECT ?int ?posent ?ent WHERE {
        ?int a covid:Interaction .
        ?int covid:involved ?posent .
        ?int covid:involved ?ent .
        ?ent a covid:Entity .
        ?posent a covid:Entity .
        ?posent covid:hasTest/covid:testedPositive true
    }""")
