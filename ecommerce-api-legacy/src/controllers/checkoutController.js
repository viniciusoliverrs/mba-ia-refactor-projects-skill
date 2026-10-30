const { APPROVED_CARD_PREFIX, EMAIL_REGEX, PAYMENT_STATUS } = require('../config/constants');
const { hashPassword } = require('../utils/crypto');
const { NotFoundError, ValidationError } = require('../utils/errors');
const logger = require('../utils/logger');

class CheckoutController {
  constructor({ db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel }) {
    this.db = db;
    this.userModel = userModel;
    this.courseModel = courseModel;
    this.enrollmentModel = enrollmentModel;
    this.paymentModel = paymentModel;
    this.auditLogModel = auditLogModel;
  }

  validateInput(body = {}) {
    const {
      usr: userName,
      eml: email,
      pwd: password,
      c_id: rawCourseId,
      card: cardNumber,
    } = body;

    if (!userName || !email || !rawCourseId || !cardNumber) {
      throw new ValidationError('Bad Request');
    }

    if (typeof email !== 'string' || !EMAIL_REGEX.test(email)) {
      throw new ValidationError('Email inválido');
    }

    const courseId = Number(rawCourseId);
    if (!Number.isInteger(courseId) || courseId <= 0) {
      throw new ValidationError('Curso inválido');
    }

    return {
      userName: String(userName).trim(),
      email: email.trim(),
      password: password ? String(password) : null,
      courseId,
      cardNumber: String(cardNumber).trim(),
    };
  }

  async checkout(req, res, next) {
    try {
      const { userName, email, password, courseId, cardNumber } = this.validateInput(req.body);

      const course = await this.courseModel.findActiveById(courseId);
      if (!course) {
        throw new NotFoundError('Curso não encontrado');
      }

      const last4 = cardNumber.slice(-4);
      logger.info('Processando transação de checkout', { courseId, cardLast4: last4 });

      const paymentStatus = cardNumber.startsWith(APPROVED_CARD_PREFIX)
        ? PAYMENT_STATUS.PAID
        : PAYMENT_STATUS.DENIED;

      if (paymentStatus === PAYMENT_STATUS.DENIED) {
        throw new ValidationError('Pagamento recusado');
      }

      const enrollmentId = await this.db.withTransaction(async () => {
        let user = await this.userModel.findByEmail(email);
        let userId = user ? user.id : null;

        if (!userId) {
          if (!password) {
            throw new ValidationError('Senha é obrigatória para novos usuários');
          }
          const passwordHash = hashPassword(password);
          userId = await this.userModel.create(userName, email, passwordHash);
        }

        const createdEnrollmentId = await this.enrollmentModel.create(userId, courseId);
        await this.paymentModel.create(createdEnrollmentId, course.price, paymentStatus);
        await this.auditLogModel.logAction(`Checkout curso ${courseId} por ${userId}`);
        return createdEnrollmentId;
      });

      return res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    } catch (err) {
      return next(err);
    }
  }
}

module.exports = CheckoutController;
