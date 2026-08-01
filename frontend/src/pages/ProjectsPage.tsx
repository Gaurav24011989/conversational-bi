import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiClientError } from '../api/client'
import { useAuth } from '../context/AuthContext'
import type { ProjectResponse } from '../types/api'

export function ProjectsPage() {
  const { token, user } = useAuth()
  const [projects, setProjects] = useState<ProjectResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [creating, setCreating] = useState(false)

  async function loadProjects() {
    if (!token || !user) return
    setLoading(true)
    setError(null)
    try {
      const data = await api.listProjects(token, user.org_id)
      setProjects(data)
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to load projects')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProjects()
  }, [token, user])

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    if (!token || !user) return
    setCreating(true)
    setError(null)
    try {
      const project = await api.createProject(token, user.org_id, {
        name,
        description: description || undefined,
      })
      setProjects((prev) => [project, ...prev])
      setName('')
      setDescription('')
      setShowForm(false)
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Failed to create project')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="page" data-testid="projects-page">
      <div className="page-header">
        <div>
          <h1>Projects</h1>
          <p className="page-subtitle">Manage workspaces and data sources</p>
        </div>
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          data-testid="new-project-button"
        >
          New project
        </button>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" data-testid="projects-error">
          {error}
        </div>
      )}

      {showForm && (
        <form className="card form-card" onSubmit={handleCreate} data-testid="new-project-form">
          <h2>Create project</h2>
          <label htmlFor="projectName">Name</label>
          <input
            id="projectName"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            data-testid="project-name-input"
          />
          <label htmlFor="projectDesc">Description</label>
          <textarea
            id="projectDesc"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            data-testid="project-description-input"
          />
          <div className="form-actions">
            <button type="submit" disabled={creating} data-testid="create-project-submit">
              {creating ? 'Creating…' : 'Create'}
            </button>
            <button type="button" onClick={() => setShowForm(false)}>
              Cancel
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <p data-testid="projects-loading">Loading projects…</p>
      ) : projects.length === 0 ? (
        <div className="empty-state card" data-testid="projects-empty">
          <p>No projects yet. Create your first project to get started.</p>
        </div>
      ) : (
        <ul className="project-list" data-testid="project-list">
          {projects.map((project) => (
            <li key={project.id}>
              <Link
                to={`/projects/${project.id}`}
                className="card project-card"
                data-testid={`project-card-${project.id}`}
              >
                <h3>{project.name}</h3>
                {project.description && <p>{project.description}</p>}
                <span className="meta">Created {new Date(project.created_at).toLocaleDateString()}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
