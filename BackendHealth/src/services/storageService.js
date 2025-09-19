const { PutObjectCommand, GetObjectCommand, DeleteObjectCommand } = require('@aws-sdk/client-s3');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');
const s3Client = require('../config/cloudstorage');
const { v4: uuidv4 } = require('uuid');

class StorageService {
  constructor() {
    this.bucketName = process.env.S3_BUCKET_NAME;
  }

  async uploadFile(file, folder = 'general') {
    const key = `${folder}/${uuidv4()}-${file.originalname}`;
    
    const command = new PutObjectCommand({
      Bucket: this.bucketName,
      Key: key,
      Body: file.buffer,
      ContentType: file.mimetype,
      Metadata: {
        originalName: file.originalname,
        uploadedAt: new Date().toISOString()
      }
    });

    try {
      await s3Client.send(command);
      return {
        key,
        url: `https://${this.bucketName}.s3.${process.env.AWS_REGION}.amazonaws.com/${key}`,
        size: file.size,
        mimeType: file.mimetype
      };
    } catch (error) {
      throw new Error(`Failed to upload file: ${error.message}`);
    }
  }

  async getSignedUrl(key, expiresIn = 3600) {
    const command = new GetObjectCommand({
      Bucket: this.bucketName,
      Key: key,
    });

    return await getSignedUrl(s3Client, command, { expiresIn });
  }

  async deleteFile(key) {
    const command = new DeleteObjectCommand({
      Bucket: this.bucketName,
      Key: key,
    });

    try {
      await s3Client.send(command);
      return true;
    } catch (error) {
      throw new Error(`Failed to delete file: ${error.message}`);
    }
  }

  // Backup conversation data to cloud storage
  async backupConversation(conversationId, data) {
    const key = `backups/conversations/${conversationId}/${Date.now()}.json`;
    
    const command = new PutObjectCommand({
      Bucket: this.bucketName,
      Key: key,
      Body: JSON.stringify(data, null, 2),
      ContentType: 'application/json'
    });

    await s3Client.send(command);
    return key;
  }
}

module.exports = new StorageService();