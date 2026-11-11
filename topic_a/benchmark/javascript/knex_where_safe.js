function endpoint(knex, value) {
  return knex("users").where("name", value);
}
