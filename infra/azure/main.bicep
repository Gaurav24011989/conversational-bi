@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Short environment suffix used in resource names (e.g. test, dev).')
@minLength(2)
@maxLength(8)
param environmentName string = 'test'

@description('PostgreSQL administrator login name.')
param postgresAdminUser string = 'cbiadmin'

@secure()
@description('PostgreSQL administrator password.')
param postgresAdminPassword string

@secure()
@description('JWT signing secret for the API.')
param secretKey string

@secure()
@description('Fernet encryption key for datasource credentials.')
param encryptionKey string

@secure()
@description('Google Gemini API key for the query agent.')
param geminiApiKey string

@description('Container image tag deployed to Container Apps.')
param containerImageTag string = 'latest'

@description('Deploy Azure Static Web Apps for the React frontend.')
param deployStaticWebApp bool = true

var namePrefix = 'cbi-${environmentName}'
var postgresServerName = '${namePrefix}-pg'
var postgresDatabaseName = 'conversational_bi'
var acrName = replace('${namePrefix}acr', '-', '')
var redisName = '${namePrefix}-redis'
var containerAppsEnvName = '${namePrefix}-cae'
var apiAppName = '${namePrefix}-api'
var workerAppName = '${namePrefix}-worker'
var staticWebAppName = '${namePrefix}-web'

module acr 'modules/acr.bicep' = {
  name: 'acr'
  params: {
    location: location
    acrName: acrName
  }
}

module postgres 'modules/postgres.bicep' = {
  name: 'postgres'
  params: {
    location: location
    serverName: postgresServerName
    databaseName: postgresDatabaseName
    adminUser: postgresAdminUser
    adminPassword: postgresAdminPassword
  }
}

module redis 'modules/redis.bicep' = {
  name: 'redis'
  params: {
    location: location
    redisName: redisName
  }
}

module containerApps 'modules/container-apps.bicep' = {
  name: 'container-apps'
  params: {
    location: location
    environmentName: containerAppsEnvName
    apiAppName: apiAppName
    workerAppName: workerAppName
    acrLoginServer: acr.outputs.loginServer
    acrName: acr.outputs.name
    imageName: 'conversational-bi-api'
    imageTag: containerImageTag
    databaseUrl: postgres.outputs.databaseUrl
    redisUrl: redis.outputs.redisUrl
    secretKey: secretKey
    encryptionKey: encryptionKey
    geminiApiKey: geminiApiKey
  }
}

module staticWebApp 'modules/static-web-app.bicep' = if (deployStaticWebApp) {
  name: 'static-web-app'
  params: {
    location: location
    staticWebAppName: staticWebAppName
  }
}

output acrLoginServer string = acr.outputs.loginServer
output acrName string = acr.outputs.name
output apiUrl string = containerApps.outputs.apiUrl
output apiFqdn string = containerApps.outputs.apiFqdn
output postgresFqdn string = postgres.outputs.fqdn
output redisHostName string = redis.outputs.hostName
output staticWebAppName string = deployStaticWebApp ? staticWebApp.outputs.name : ''
output staticWebAppHostname string = deployStaticWebApp ? staticWebApp.outputs.defaultHostname : ''
output staticWebAppUrl string = deployStaticWebApp ? staticWebApp.outputs.defaultUrl : ''
output resourceGroupName string = resourceGroup().name
