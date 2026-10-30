class PaymentModel {
  constructor(db) {
    this.db = db;
  }

  async create(enrollmentId, amount, status) {
    const result = await this.db.run(
      'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
      [enrollmentId, amount, status]
    );
    return result.lastID;
  }
}

module.exports = PaymentModel;
