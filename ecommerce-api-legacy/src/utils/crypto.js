const crypto = require('crypto');

const SALT_BYTES = 16;
const KEY_LENGTH = 32;

function hashPassword(password) {
  const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
  const derivedKey = crypto.scryptSync(String(password), salt, KEY_LENGTH).toString('hex');
  return `${salt}:${derivedKey}`;
}

function verifyPassword(password, storedHash) {
  if (!storedHash || !storedHash.includes(':')) {
    return false;
  }
  const [salt, keyHex] = storedHash.split(':');
  const derivedKey = crypto.scryptSync(String(password), salt, KEY_LENGTH);
  const keyBuffer = Buffer.from(keyHex, 'hex');
  if (derivedKey.length !== keyBuffer.length) {
    return false;
  }
  return crypto.timingSafeEqual(derivedKey, keyBuffer);
}

module.exports = {
  hashPassword,
  verifyPassword,
};

