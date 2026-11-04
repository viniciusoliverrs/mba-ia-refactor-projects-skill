const express = require('express');
const settings = require('./config/settings');
const { DatabaseConnection } = require('./database/connection');
const { initDatabase } = require('./database/schema');
const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditLogModel = require('./models/auditLogModel');
const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');
const createApiRouter = require('./routes');
const errorHandler = require('./middlewares/errorHandler');

const { notFoundHandler } = errorHandler;
const logger = require('./utils/logger');

// Factory pura: recebe a conexão já pronta; não abre banco, não cria schema e não faz listen.
function createApp(db) {
  const userModel = new UserModel(db);
  const courseModel = new CourseModel(db);
  const enrollmentModel = new EnrollmentModel(db);
  const paymentModel = new PaymentModel(db);
  const auditLogModel = new AuditLogModel(db);

  const checkoutController = new CheckoutController({
    db,
    userModel,
    courseModel,
    enrollmentModel,
    paymentModel,
    auditLogModel,
  });
  const reportController = new ReportController({ courseModel });
  const userController = new UserController({ userModel });

  const app = express();
  app.use(express.json());

  app.get('/health', (_req, res) => {
    res.status(200).json({ status: 'ok' });
  });

  app.use('/api', createApiRouter({ checkoutController, reportController, userController }));
  app.use(notFoundHandler);
  app.use(errorHandler);

  return app;
}

if (require.main === module) {
  const db = new DatabaseConnection();
  initDatabase(db)
    .then(() => {
      const app = createApp(db);
      app.listen(settings.port, () => {
        logger.info(`LMS API rodando na porta ${settings.port}`);
      });
    })
    .catch((err) => {
      logger.error('Falha ao iniciar servidor', { message: err.message });
      process.exit(1);
    });
}

module.exports = { createApp };
