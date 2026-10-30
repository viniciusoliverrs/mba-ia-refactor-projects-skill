class UserModel {
  constructor(db) {
    this.db = db;
  }

  async findByEmail(email) {
    return this.db.get('SELECT id, name, email FROM users WHERE email = ?', [email]);
  }

  async findById(userId) {
    return this.db.get('SELECT id, name, email FROM users WHERE id = ?', [userId]);
  }

  async create(name, email, passwordHash) {
    const result = await this.db.run(
      'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
      [name, email, passwordHash]
    );
    return result.lastID;
  }

  async deleteWithCascade(userId) {
    return this.db.withTransaction(async () => {
      await this.db.run(
        'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
        [userId]
      );
      await this.db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
      const result = await this.db.run('DELETE FROM users WHERE id = ?', [userId]);
      return result.changes;
    });
  }
}

module.exports = UserModel;
