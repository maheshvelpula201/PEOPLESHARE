
import { useState, type FormEvent } from 'react'
import './LoginPage.css'

type LoginPageProps = {
  onLogin: (companyId: string, email: string, password: string) => Promise<void>
  onRegister: () => void
}

export default function LoginPage({ onLogin, onRegister }: LoginPageProps) {
  const [companyId, setCompanyId] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      await onLogin(companyId.trim(), email.trim(), password)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign in. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <section className="login-hero">
        <div className="login-brand">
          <span className="brand-mark">P</span>
          <span>People<span>Sphere</span></span>
        </div>

        <div className="hero-copy">
          <p className="hero-eyebrow">PEOPLE. PROGRESS. POSSIBILITIES.</p>
          <h1>Empower Your <span>Workforce.</span></h1>
          <div className="hero-accent" />
          <h2>Connect. Collaborate. Grow.</h2>
          <p className="hero-description">
            A smarter way to manage your people, attendance and workplace together.
          </p>

          <div className="hero-benefits">
            <div><span>01</span><p><strong>Manage Teams</strong><br />with Ease</p></div>
            <div><span>02</span><p><strong>Track Attendance</strong><br />Effortlessly</p></div>
            <div><span>03</span><p><strong>Handle Leaves</strong><br />Simplified</p></div>
            <div><span>04</span><p><strong>Stay Connected</strong><br />Always</p></div>
          </div>
        </div>

        <p className="hero-footer">A better workplace starts with better connections.</p>
      </section>

      <section className="login-panel">
        <div className="login-card">
          <div className="login-card-brand">
            <span className="brand-mark">P</span>
            <span>People<span>Sphere</span></span>
          </div>

          <div className="login-heading">
            <p className="login-eyebrow">WELCOME TO YOUR WORKSPACE</p>
            <h2>Welcome Back</h2>
            <p>Sign in to your PeopleSphere account</p>
          </div>

          <form onSubmit={handleSubmit}>
            <label htmlFor="companyId">Company ID</label>
            <input
              id="companyId"
              value={companyId}
              onChange={(event) => setCompanyId(event.target.value)}
              placeholder="Enter your company ID"
              autoComplete="organization"
              required
            />

            <label htmlFor="loginEmail">Email Address</label>
            <input
              id="loginEmail"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@company.com"
              autoComplete="username"
              required
            />

            <label htmlFor="loginPassword">Password</label>
            <div className="password-field">
              <input
                id="loginPassword"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter your password"
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword((value) => !value)}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>

            <div className="login-options">
              <label className="remember-option">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(event) => setRememberMe(event.target.checked)}
                />
                Remember me
              </label>
              <button type="button" className="text-action" disabled>
                Forgot password?
              </button>
            </div>

            {error && <p className="login-error" role="alert">{error}</p>}

            <button className="login-submit" type="submit" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
              {!loading && <span>→</span>}
            </button>
          </form>

          <div className="login-divider"><span>or</span></div>

          <div className="register-prompt">New to PeopleSphere?</div>
          <button className="register-button" onClick={onRegister}>
            Register Your Company <span>→</span>
          </button>

          <p className="login-security">● Secure <span>•</span> Trusted <span>•</span> Built for You</p>
        </div>
      </section>
    </div>
  )
}
