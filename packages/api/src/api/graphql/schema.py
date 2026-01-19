"""
Strawberry GraphQL schema definition.
"""
import strawberry
from strawberry.fastapi import GraphQLRouter

from api.graphql.resolvers import Query, Mutation


# Create the schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
)


def get_context(request):
    """Build context for GraphQL resolvers."""
    return {"request": request}


# Create the GraphQL router for FastAPI
graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphql_ide="graphiql",
)
