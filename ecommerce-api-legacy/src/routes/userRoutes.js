const express = require('express');

function createUserRoutes(userController) {
  const router = express.Router();
  router.delete('/users/:id', (req, res, next) => userController.deleteUser(req, res, next));
  return router;
}

module.exports = createUserRoutes;

