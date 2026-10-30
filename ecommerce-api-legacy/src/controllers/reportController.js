const { PAYMENT_STATUS } = require('../config/constants');

class ReportController {
  constructor({ courseModel }) {
    this.courseModel = courseModel;
  }

  async getFinancialReport(req, res, next) {
    try {
      const rows = await this.courseModel.getFinancialReportRows();
      const coursesMap = new Map();

      for (const row of rows) {
        if (!coursesMap.has(row.course_id)) {
          coursesMap.set(row.course_id, {
            course: row.course_title,
            revenue: 0,
            students: [],
          });
        }

        if (row.enrollment_id !== null && row.enrollment_id !== undefined) {
          const courseReport = coursesMap.get(row.course_id);
          const paidAmount = row.payment_amount ? Number(row.payment_amount) : 0;

          if (row.payment_status === PAYMENT_STATUS.PAID) {
            courseReport.revenue += paidAmount;
          }

          courseReport.students.push({
            student: row.student_name || 'Unknown',
            paid: paidAmount,
          });
        }
      }

      return res.status(200).json(Array.from(coursesMap.values()));
    } catch (err) {
      return next(err);
    }
  }
}

module.exports = ReportController;

