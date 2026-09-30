from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "admin123")

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    print("Connected successfully")
    summary = driver.execute_query("""
        CREATE (a:Person {name: $name})
        CREATE (b:Person {name: $friend_name})
        CREATE (a)-[:KNOWS]->(b)
        """,
        name="Alice", friend_name="David",
        database="neo4j"
    ).summary
    print("Created {nodes_created} nodes in {time} ms.".format(
        nodes_created=summary.counters.nodes_created,
        time=summary.result_available_after
    ))

    records, summary, keys = driver.execute_query("""
        MATCH (p:Person)-[:KNOWS]->(:Person)
        RETURN p.name AS name
        """,
        database="neo4j",
    )

    for record in records:
        print(record.data())

    print("The query `{query}` returned {records_count} records in {time} ms.".format(
        query=summary.query, records_count=len(records),
        time=summary.result_available_after
    ))

