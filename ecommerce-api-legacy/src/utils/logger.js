function formatMessage(level, message, meta) {
  const timestamp = new Date().toISOString();
  const suffix = meta ? ` ${JSON.stringify(meta)}` : '';
  return `[${timestamp}] [${level}] ${message}${suffix}`;
}

const logger = {
  info(message, meta) {
    console.info(formatMessage('INFO', message, meta));
  },
  warn(message, meta) {
    console.warn(formatMessage('WARN', message, meta));
  },
  error(message, meta) {
    console.error(formatMessage('ERROR', message, meta));
  },
};

module.exports = logger;
