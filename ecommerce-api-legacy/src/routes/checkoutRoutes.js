const express = require('express');

function createCheckoutRoutes(checkoutController) {
  const router = express.Router();
  router.post('/checkout', (req, res, next) => checkoutController.checkout(req, res, next));
  return router;
}

module.exports = createCheckoutRoutes;
