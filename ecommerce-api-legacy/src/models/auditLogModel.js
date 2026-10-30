class AuditLogModel {
  constructor(db) {
    this.db = db;
  }

  async logAction(action) {
    await this.db.run(
      "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
      [action]
    );
  }
}

module.exports = AuditLogModel;
