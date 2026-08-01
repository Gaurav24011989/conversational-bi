@description('Azure region.')
param location string

@description('Globally unique ACR name (alphanumeric only).')
param acrName string

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

output loginServer string = acr.properties.loginServer
output name string = acr.name
