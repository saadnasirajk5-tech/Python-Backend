const express = require('express');
const router = express.Router();
const { getAllUsers, createUser } = require('../controllers/userController');

router.get('/', (req, res) => {
    const users = getAllUsers();
    res.json(users);
});

router.post('/', (req, res) => {
    const { name, email } = req.body;
    if (!name || !email) return res.status(400).json({ error: 'Name and Email required' });

    const newUser = createUser(name, email);
    res.status(201).json(newUser);
});

module.exports = router; 








