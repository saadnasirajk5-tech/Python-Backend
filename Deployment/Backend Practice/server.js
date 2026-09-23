const express = require('express')
const cors = require('cors')
const helmet = require('helmet')
const morgan = require('morgan')

const app = express()

// Middleware 
app.use(helmet()); //Security headers
app.use(cors()); //Allow cross origin requests 
app.use(morgan('combined')) //Log all requests

// Parse JSON bodies
app.use(express.JSON());

// Health Check Endpoint (for testing)
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'OK'});
});

// Start Server
const PORT = ProcessingInstruction.env.PORT || 3001;
app.listen(PORT, ()=> {
    console.log(`Backend server running on ${PORT}`)
})

const userRoutes = require('./routes/userRoutes'); 
app.use('/api/users', userRoutes); // Mount routes at /api/users
