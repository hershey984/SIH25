const express = require('express');
const multer = require('multer');
const chatController = require('../controllers/chatController');

const router = express.Router();

// Configure multer for file uploads
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB limit
  },
  fileFilter: (req, file, cb) => {
    // Allow images and documents
    const allowedMimes = [
      'image/jpeg', 'image/png', 'image/gif', 'image/webp',
      'application/pdf', 'text/plain', 'application/json'
    ];
    
    if (allowedMimes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('File type not allowed'), false);
    }
  }
});

// Routes
router.post('/conversations', chatController.createConversation);
router.post('/conversations/:sessionId/messages', upload.array('files', 5), chatController.sendMessage);
router.get('/conversations/:sessionId/messages', chatController.getMessages);
router.get('/users/:userId/conversations', chatController.getConversations);
router.delete('/conversations/:sessionId', chatController.deleteConversation);
router.post('/conversations/:sessionId/backup', chatController.backupConversation);

module.exports = router;