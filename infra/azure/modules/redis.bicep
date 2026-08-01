@description('Azure region.')
param location string

@description('Redis cache resource name.')
param redisName string

resource redis 'Microsoft.Cache/redis@2024-03-01' = {
  name: redisName
  location: location
  properties: {
    sku: {
      name: 'Basic'
      family: 'C'
      capacity: 0
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    redisConfiguration: {
      'maxmemory-policy': 'allkeys-lru'
    }
  }
}

var hostName = redis.properties.hostName
var primaryKey = redis.listKeys().primaryKey
var redisUrl = 'rediss://:${primaryKey}@${hostName}:6380/0'

output hostName string = hostName
output redisUrl string = redisUrl
