import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiClientError } from '../api/client'
import { useAuth } from '../context/AuthContext'

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [orgName, setOrgName] = useState('')
  const [orgSlug, setOrgSlug] = useState('')
  const [slugTouched, setSlugTouched] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await register({
        email,
        password,
        full_name: fullName || undefined,
        org_name: orgName,
        org_slug: orgSlug,
      })
      navigate('/projects')
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Registration failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Create account</h1>
        <p className="auth-subtitle">Set up your organization and start querying data</p>
        <form onSubmit={handleSubmit} data-testid="register-form">
          {error && (
            <div className="alert alert-error" role="alert" data-testid="register-error">
              {error}
            </div>
          )}
          <label htmlFor="fullName">Full name</label>
          <input
            id="fullName"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            data-testid="register-full-name"
          />
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            data-testid="register-email"
          />
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            data-testid="register-password"
          />
          <label htmlFor="orgName">Organization name</label>
          <input
            id="orgName"
            value={orgName}
            onChange={(e) => {
              setOrgName(e.target.value)
              if (!slugTouched) setOrgSlug(slugify(e.target.value))
            }}
            required
            data-testid="register-org-name"
          />
          <label htmlFor="orgSlug">Organization slug</label>
          <input
            id="orgSlug"
            value={orgSlug}
            onChange={(e) => {
              setSlugTouched(true)
              setOrgSlug(e.target.value)
            }}
            required
            pattern="[a-z0-9-]+"
            data-testid="register-org-slug"
          />
          <button type="submit" disabled={submitting} data-testid="register-submit">
            {submitting ? 'Creating…' : 'Create account'}
          </button>
        </form>
        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
