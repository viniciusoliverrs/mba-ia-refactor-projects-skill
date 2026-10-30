const PAYMENT_STATUS = Object.freeze({
  PAID: 'PAID',
  DENIED: 'DENIED',
});

const APPROVED_CARD_PREFIX = '4';
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CARD_DIGITS_REGEX = /^\d{13,19}$/;

module.exports = {
  PAYMENT_STATUS,
  APPROVED_CARD_PREFIX,
  EMAIL_REGEX,
  CARD_DIGITS_REGEX,
};

