function endpoint(db, value) {
  return db.query("SELECT * FROM users WHERE name = $name", {bind: {name: value}});
}
