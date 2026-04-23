const { gql } = require("graphql-tag");

const typeDefs = gql`
  type Job {
    id: ID!
    status: String!
    progress: Int!
    outputUrl: String
  }

  type Query {
    jobStatus(id: ID!): Job
  }
`;

module.exports = typeDefs;
