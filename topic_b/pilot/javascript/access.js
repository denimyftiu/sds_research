// Synthetic workflow fixture; never a real-project observation.
function find(db, knex, User, value) {
  db.query(`SELECT * FROM users WHERE name = '${value}'`);
  knex("users").where("name", value);
  return User.findAll({where: {name: value}});
}
