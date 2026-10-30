const express = require('express');
const createCheckoutRoutes = require('./checkoutRoutes');
const createReportRoutes = require('./reportRoutes');
const createUserRoutes = require('./userRoutes');

function createApiRouter({ checkoutController, reportController, userController }) {
  const apiRouter = express.Router();

  apiRouter.use(createCheckoutRoutes(checkoutController));
  apiRouter.use(createReportRoutes(reportController));
  apiRouter.use(createUserRoutes(userController));

  return apiRouter;
}

module.exports = createApiRouter;
