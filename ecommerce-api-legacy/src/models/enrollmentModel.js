class EnrollmentModel {
  constructor(db) {
    this.db = db;
  }

  async create(userId, courseId) {
    const result = await this.db.run(
      'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
      [userId, courseId]
    );
    return result.lastID;
  }
}

module.exports = EnrollmentModel;

