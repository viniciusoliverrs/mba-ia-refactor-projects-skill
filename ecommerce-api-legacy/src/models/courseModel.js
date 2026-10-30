class CourseModel {
  constructor(db) {
    this.db = db;
  }

  async findActiveById(courseId) {
    return this.db.get('SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1', [courseId]);
  }

  async getFinancialReportRows() {
    const sql = `
      SELECT
        c.id AS course_id,
        c.title AS course_title,
        e.id AS enrollment_id,
        u.name AS student_name,
        p.amount AS payment_amount,
        p.status AS payment_status
      FROM courses c
      LEFT JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN users u ON u.id = e.user_id
      LEFT JOIN payments p ON p.enrollment_id = e.id
      ORDER BY c.id, e.id
    `;
    return this.db.all(sql);
  }
}

module.exports = CourseModel;

