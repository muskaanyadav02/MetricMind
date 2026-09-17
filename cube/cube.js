module.exports = {
  schemaPath: "model",

  driverFactory: ({ dataSource } = {}) => {
    return {
      type: "snowflake",
      account: process.env.CUBEJS_DB_ACCOUNT,
      username: process.env.CUBEJS_DB_USER,
      password: process.env.CUBEJS_DB_PASS,
      database: process.env.CUBEJS_DB_NAME,
      schema: process.env.CUBEJS_DB_SCHEMA,
      warehouse: process.env.CUBEJS_DB_WAREHOUSE,
      role: process.env.CUBEJS_DB_ROLE,
    };
  },
};