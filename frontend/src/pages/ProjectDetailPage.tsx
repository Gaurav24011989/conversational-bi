import { useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, ApiClientError } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { addStoredConversation, getStoredConversations } from '../utils/storage'
import type { DataSourceResponse, DataSourceType, ProjectResponse } from '../types/api'

const DEFAULT_PORTS: Record<DataSourceType, number> = {
  postgresql: 5432,
  mysql: 3306,
  mongodb: 27017,
  elasticsearch: 9200,
}

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { token } = useAuth()
  const [project, setProject] = useState<ProjectResponse | null>(null)
  const [datasources, setDatasources] = useState<DataSourceResponse[]>([])
  const [conversations, setConversations] = useState(
  () => (projectId ? getStoredConversations(projectId) : []),
  )
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showDsForm, setShowDsForm] = useState(false)
  const [dsName, setDsName] = useState('')
  const [dsType, setDsType] = useState<DataSourceType>('postgresql')
  const [dsHost, setDsHost] = useState('localhost')
  const [dsPort, setDsPort] = useState(5432)
  const [dsDatabase, setDsDatabase] = useState('')
  const [dsUsername, setDsUsername] = useState('')
  const [dsPassword, setDsPassword] = useState('')
  const [creating, setCreating] = useState(false)
  const [testResult, setTestResult] = useState<string | null>(null)
  const [startingConversation, setStartingConversation] = useState<string | null>(null)

  useEffect(() => {
    if (!token || !projectId) return
    setLoading(true)
    Promise.all([
      api.getProject(token, projectId),
      api.listDatasources(token, projectId),
    ])
      .then(([proj, ds]) => {
        setProject(proj)
        setDatasources(ds)
      })
      .catch((err) =>
        setError(err instanceof ApiClientError ? err.message : 'Failed to load project'),
      )
      .finally(() => setLoading(false))
  }, [token, projectId])

  function handleTypeChange(type: DataSourceType) {
    setDsType(type)
    setDsPort(DEFAULT_PORTS[type])
  }

  async function handleCreateDatasource(e: FormEvent) {
    e.preventDefault()
    if (!token || !projectId) return
    setCreating(true)
    setError(null)
    try {
      const ds = await api.createDatasource(token, projectId, {
        name: dsName,
        type: dsType,
        config: {
          host: dsHost,
          port: dsPort,
          database: dsDatabase,
          username: dsUsername,
          password: dsPassword,
        },
      })
      setDatasources((prev) => [ds, ...prev])
      setShowDsForm(false)
      setDsName('')
      setDsDatabase('')
      setDsUsername('')
      setDsPassword('')
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to create datasource')
    } finally {
      setCreating(false)
    }
  }

  async function handleTest(datasourceId: string) {
    if (!token) return
    setTestResult(null)
    try {
      const result = await api.testDatasource(token, datasourceId)
      setTestResult(
        result.success
          ? `Connected (${result.latency_ms ?? '?'} ms)`
          : `Failed: ${result.message}`,
      )
    } catch (err) {
      setTestResult(err instanceof ApiClientError ? err.message : 'Test failed')
    }
  }

  async function handleRefreshSchema(datasourceId: string) {
    if (!token) return
    setError(null)
    try {
      await api.refreshSchema(token, datasourceId)
      setTestResult('Schema refreshed successfully')
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Schema refresh failed')
    }
  }

  async function handleStartConversation(datasourceId: string) {
    if (!token || !projectId) return
    setStartingConversation(datasourceId)
    setError(null)
    try {
      const conv = await api.createConversation(token, projectId, { datasource_id: datasourceId })
      addStoredConversation({
        id: conv.id,
        projectId: conv.project_id,
        datasourceId: conv.datasource_id,
        title: conv.title,
        createdAt: conv.created_at,
      })
      setConversations(getStoredConversations(projectId))
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to start conversation')
    } finally {
      setStartingConversation(null)
    }
  }

  if (loading) {
    return <p data-testid="project-loading">Loading project…</p>
  }

  if (!project) {
    return <p data-testid="project-not-found">Project not found.</p>
  }

  return (
    <div className="page" data-testid="project-detail-page">
      <div className="page-header">
        <div>
          <Link to="/projects" className="back-link">
            ← Projects
          </Link>
          <h1>{project.name}</h1>
          {project.description && <p className="page-subtitle">{project.description}</p>}
        </div>
        <button
          type="button"
          onClick={() => setShowDsForm((v) => !v)}
          data-testid="new-datasource-button"
        >
          Add datasource
        </button>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" data-testid="project-error">
          {error}
        </div>
      )}
      {testResult && (
        <div className="alert alert-info" data-testid="datasource-test-result">
          {testResult}
        </div>
      )}

      {showDsForm && (
        <form className="card form-card" onSubmit={handleCreateDatasource} data-testid="datasource-form">
          <h2>Add datasource</h2>
          <label htmlFor="dsName">Name</label>
          <input
            id="dsName"
            value={dsName}
            onChange={(e) => setDsName(e.target.value)}
            required
            data-testid="datasource-name"
          />
          <label htmlFor="dsType">Type</label>
          <select
            id="dsType"
            value={dsType}
            onChange={(e) => handleTypeChange(e.target.value as DataSourceType)}
            data-testid="datasource-type"
          >
            <option value="postgresql">PostgreSQL</option>
            <option value="mysql">MySQL</option>
            <option value="mongodb">MongoDB</option>
            <option value="elasticsearch">Elasticsearch</option>
          </select>
          <div className="form-row">
            <div>
              <label htmlFor="dsHost">Host</label>
              <input
                id="dsHost"
                value={dsHost}
                onChange={(e) => setDsHost(e.target.value)}
                required
                data-testid="datasource-host"
              />
            </div>
            <div>
              <label htmlFor="dsPort">Port</label>
              <input
                id="dsPort"
                type="number"
                value={dsPort}
                onChange={(e) => setDsPort(Number(e.target.value))}
                required
                data-testid="datasource-port"
              />
            </div>
          </div>
          <label htmlFor="dsDatabase">Database / index</label>
          <input
            id="dsDatabase"
            value={dsDatabase}
            onChange={(e) => setDsDatabase(e.target.value)}
            required
            data-testid="datasource-database"
          />
          <div className="form-row">
            <div>
              <label htmlFor="dsUsername">Username</label>
              <input
                id="dsUsername"
                value={dsUsername}
                onChange={(e) => setDsUsername(e.target.value)}
                data-testid="datasource-username"
              />
            </div>
            <div>
              <label htmlFor="dsPassword">Password</label>
              <input
                id="dsPassword"
                type="password"
                value={dsPassword}
                onChange={(e) => setDsPassword(e.target.value)}
                data-testid="datasource-password"
              />
            </div>
          </div>
          <div className="form-actions">
            <button type="submit" disabled={creating} data-testid="create-datasource-submit">
              {creating ? 'Saving…' : 'Save datasource'}
            </button>
            <button type="button" onClick={() => setShowDsForm(false)}>
              Cancel
            </button>
          </div>
        </form>
      )}

      <section className="section">
        <h2>Data sources</h2>
        {datasources.length === 0 ? (
          <div className="empty-state card" data-testid="datasources-empty">
            <p>No data sources configured. Add one to start querying.</p>
          </div>
        ) : (
          <ul className="datasource-list" data-testid="datasource-list">
            {datasources.map((ds) => (
              <li key={ds.id} className="card datasource-card" data-testid={`datasource-${ds.id}`}>
                <div>
                  <h3>{ds.name}</h3>
                  <span className="badge">{ds.type}</span>
                </div>
                <div className="card-actions">
                  <button type="button" onClick={() => handleTest(ds.id)} data-testid={`test-${ds.id}`}>
                    Test connection
                  </button>
                  <button
                    type="button"
                    onClick={() => handleRefreshSchema(ds.id)}
                    data-testid={`refresh-schema-${ds.id}`}
                  >
                    Refresh schema
                  </button>
                  <button
                    type="button"
                    onClick={() => handleStartConversation(ds.id)}
                    disabled={startingConversation === ds.id}
                    data-testid={`start-conversation-${ds.id}`}
                  >
                    {startingConversation === ds.id ? 'Starting…' : 'New conversation'}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="section">
        <h2>Conversations</h2>
        {conversations.length === 0 ? (
          <div className="empty-state card" data-testid="conversations-empty">
            <p>No conversations yet. Start one from a data source above.</p>
          </div>
        ) : (
          <ul className="conversation-list" data-testid="conversation-list">
            {conversations.map((conv) => (
              <li key={conv.id}>
                <Link
                  to={`/projects/${projectId}/conversations/${conv.id}`}
                  className="card conversation-card"
                  data-testid={`conversation-link-${conv.id}`}
                >
                  <h3>{conv.title ?? 'Untitled conversation'}</h3>
                  <span className="meta">
                    {new Date(conv.createdAt).toLocaleString()}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
