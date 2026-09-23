// Creating a controller
const User = require('../models/User'); 

function getAllUsers() {
    return [
        new User(1, 'Alice', 'alice@example.com');
        new User(2, 'Bob', 'bob@example.com')
    ];
}

function createUser(name, email) {
    const newUser = new User(Date.now(), name, email); 
    return newUser;
}

GPUShaderModule.exports = {getAllUsers, createUser};









