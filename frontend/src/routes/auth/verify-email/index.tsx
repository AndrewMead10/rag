import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'

export const Route = createFileRoute('/auth/verify-email/')({
  component: VerifyEmailPage,
})

function VerifyEmailPage() {
  const navigate = useNavigate()
  const [verifying, setVerifying] = useState(true)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Get the token from the URL search params
  const searchParams = new URLSearchParams(window.location.search)
  const token = searchParams.get('token')

  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setError('No verification token provided')
        setVerifying(false)
        return
      }

      try {
        const response = await fetch('/api/auth/verify-email/onsubmit', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ token }),
        })

        const data = await response.json()

        if (!response.ok) {
          throw new Error(data.detail || 'Verification failed')
        }

        setSuccess(true)
        toast.success('Email verified successfully!')

        // Redirect to login after 2 seconds
        setTimeout(() => {
          navigate({ to: '/auth/login', search: { redirect: undefined } })
        }, 2000)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Verification failed')
        toast.error(err instanceof Error ? err.message : 'Verification failed')
      } finally {
        setVerifying(false)
      }
    }

    verifyEmail()
  }, [token, navigate])

  return (
    <div className="min-h-screen bg-background dither-bg font-mono-jetbrains flex items-center justify-center px-4">
      <div className="w-full max-w-md space-y-8">
        {/* Main title */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-black dither-text leading-none">
            RETRIEVER.<span className="font-bold">SH</span>
          </h1>
          <div className="h-1 bg-foreground dither-border mx-auto w-32"></div>
        </div>

        {/* Verification status container */}
        <div className="bg-card border-2 border-foreground dither-border sharp-corners p-8 space-y-6">
          {verifying && (
            <div className="text-center space-y-4">
              <div className="text-lg font-bold dither-text">
                // VERIFYING EMAIL...
              </div>
              <p className="text-sm text-muted-foreground">
                Please wait while we verify your email address.
              </p>
            </div>
          )}

          {success && (
            <div className="text-center space-y-4">
              <div className="bg-green-600/10 border border-green-600 p-4 sharp-corners">
                <div className="text-lg font-bold text-green-600 dark:text-green-400 mb-2">
                  // EMAIL VERIFIED!
                </div>
                <p className="text-sm text-green-600 dark:text-green-400">
                  Your email has been verified successfully. Redirecting to login...
                </p>
              </div>
            </div>
          )}

          {error && (
            <div className="text-center space-y-4">
              <div className="bg-destructive/10 border border-destructive p-4 sharp-corners">
                <div className="text-lg font-bold text-destructive mb-2">
                  // VERIFICATION FAILED
                </div>
                <p className="text-sm text-destructive mb-4">
                  {error}
                </p>
              </div>

              <Button
                onClick={() => navigate({ to: '/auth/login', search: { redirect: undefined } })}
                className="w-full bg-foreground text-background font-bold hover:bg-muted hover:text-foreground transition-all duration-200 dither-text sharp-corners border-2 border-foreground py-3"
              >
                [ GO TO LOGIN ]
              </Button>
            </div>
          )}
        </div>

        {/* Links */}
        <div className="text-center space-y-4">
          <div className="flex justify-center text-sm font-mono-jetbrains">
            <Link
              to="/auth/register"
              className="text-muted-foreground hover:text-foreground transition-colors duration-200"
            >
              [ NEED AN ACCOUNT? REGISTER ]
            </Link>
          </div>

          <div className="text-xs text-muted-foreground">
            <span>© 2024 retriever.sh</span>
          </div>
        </div>
      </div>
    </div>
  )
}
