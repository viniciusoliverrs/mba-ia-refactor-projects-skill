const { NotFoundError, ValidationError } = require('../utils/errors');
const logger = require('../utils/logger');

class UserController {
  constructor({ userModel }) {
    this.userModel = userModel;
  }

  async deleteUser(req, res, next) {
    try {
      const userId = Number(req.params.id);
      if (!Number.isInteger(userId) || userId <= 0) {
        throw new ValidationError('ID de usuário inválido');
      }

      const existing = await this.userModel.findById(userId);
      if (!existing) {
        throw new NotFoundError('Usuário não encontrado');
      }

      await this.userModel.deleteWithCascade(userId);
      logger.info('Usuário e vínculos removidos com integridade', { userId });

      return res.status(200).json({
        msg: 'Usuário e registros associados (matrículas e pagamentos) removidos com sucesso.',
      });
    } catch (err) {
      return next(err);
    }
  }
}

module.exports = UserController;
