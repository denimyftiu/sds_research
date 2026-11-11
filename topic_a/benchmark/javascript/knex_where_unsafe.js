function endpoint(knex, value) {
  return knex("users").whereRaw(`name = '${value}'`);
}
