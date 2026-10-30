const express = require('express');

function createReportRoutes(reportController) {
  const router = express.Router();
  router.get('/admin/financial-report', (req, res, next) =>
    reportController.getFinancialReport(req, res, next)
  );
  return router;
}

module.exports = createReportRoutes;
