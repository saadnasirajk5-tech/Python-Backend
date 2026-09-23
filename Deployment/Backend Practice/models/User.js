class User{
    constructor(id, name, email) {
        this.id = id; 
        this.email = email; 
        this.name = name; 
        this.createdAt = new Date();
    }
}

module.exports = User;