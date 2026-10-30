const { AppError } = require('../utils/errors');
const logger = require('../utils/logger');

function errorHandler(err, req, res, _next) {
  if (err instanceof AppError) {
    return res.status(err.status).json({ erro: err.message });
  }

  logger.error('Erro interno inesperado', { message: err.message });
  return res.status(500).json({ erro: 'Erro interno do servidor' });
}

module.exports = errorHandler;

