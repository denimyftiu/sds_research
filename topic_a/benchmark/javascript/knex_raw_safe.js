function endpoint(knex, value) {
  return knex.raw("SELECT * FROM users WHERE name = ?", [value]);
}
