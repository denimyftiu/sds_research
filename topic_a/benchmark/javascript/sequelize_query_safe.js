function endpoint(db, value) {
  return db.query("SELECT * FROM users WHERE name = :name", {replacements: {name: value}});
}
