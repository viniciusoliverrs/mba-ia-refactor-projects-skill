const { AppError } = require('../utils/errors');
const logger = require('../utils/logger');

function notFoundHandler(_req, res) {
  return res.status(404).json({ erro: 'Rota não encontrada' });
}

function errorHandler(err, req, res, _next) {
  if (err instanceof AppError) {
    return res.status(err.status).json({ erro: err.message });
  }

  // Erros do body-parser (JSON malformado, payload grande demais) são erros do cliente, não 500.
  if (err.type === 'entity.parse.failed' || err.type === 'entity.too.large') {
    return res.status(err.status || 400).json({ erro: 'Payload inválido' });
  }

  logger.error('Erro interno inesperado', { message: err.message });
  return res.status(500).json({ erro: 'Erro interno do servidor' });
}

module.exports = errorHandler;
module.exports.notFoundHandler = notFoundHandler;

