using '../main.bicep'

param environmentName = 'test'
param postgresAdminPassword = readEnvironmentVariable('POSTGRES_ADMIN_PASSWORD', '')
param secretKey = readEnvironmentVariable('SECRET_KEY', '')
param encryptionKey = readEnvironmentVariable('ENCRYPTION_KEY', '')
param geminiApiKey = readEnvironmentVariable('GEMINI_API_KEY', '')
param containerImageTag = 'latest'
