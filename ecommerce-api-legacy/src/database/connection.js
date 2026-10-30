const sqlite3 = require('sqlite3');
const settings = require('../config/settings');

class DatabaseConnection {
  constructor(dbPath = settings.dbPath) {
    this.db = new sqlite3.Database(dbPath);
  }

  run(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.run(sql, params, function onRun(err) {
        if (err) {
          return reject(err);
        }
        return resolve({ lastID: this.lastID, changes: this.changes });
      });
    });
  }

  get(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.get(sql, params, (err, row) => {
        if (err) {
          return reject(err);
        }
        return resolve(row || null);
      });
    });
  }

  all(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.all(sql, params, (err, rows) => {
        if (err) {
          return reject(err);
        }
        return resolve(rows || []);
      });
    });
  }

  async withTransaction(work) {
    await this.run('BEGIN TRANSACTION');
    try {
      const result = await work();
      await this.run('COMMIT');
      return result;
    } catch (err) {
      await this.run('ROLLBACK');
      throw err;
    }
  }
}

const dbConnection = new DatabaseConnection();

module.exports = {
  DatabaseConnection,
  dbConnection,
};
