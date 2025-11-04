import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import { toast } from 'sonner'

export const Route = createFileRoute('/auth/reset/')({
  component: ResetPage,
})

function useQueryToken(): string | null {
  if (typeof window === 'undefined') return null
  const params = new URLSearchParams(window.location.search)
  return params.get('token')
}

function ResetPage() {
  const navigate = useNavigate()
  const token = useQueryToken()

  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm<any>()
  const password = watch('new_password')

  const onRequest = async (data: any) => {
    try {
      await api.auth.resetRequest(data.email)
      toast.success('If an account exists, a reset email has been sent.')
      navigate({ to: '/auth/login', search: { redirect: undefined } })
    } catch (err: any) {
      console.error(err)
      toast.error(err?.message || 'Failed to send reset email')
    }
  }

  const onConfirm = async (data: any) => {
    try {
      await api.auth.resetConfirm(token!, data.new_password)
      toast.success('Password has been reset. Please sign in.')
      navigate({ to: '/auth/login', search: { redirect: undefined } })
    } catch (err: any) {
      console.error(err)
      toast.error(err?.message || 'Failed to reset password')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Password Reset</CardTitle>
          <CardDescription>
            {token ? 'Enter a new password for your account' : 'Request a password reset link'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!token ? (
            <form onSubmit={handleSubmit(onRequest)} className="space-y-4">
              <div>
                <Input
                  type="email"
                  placeholder="Email"
                  {...register('email', { required: 'Email is required' })}
                />
                {errors.email && (
                  <p className="text-sm text-red-600 mt-1">{String(errors.email.message)}</p>
                )}
              </div>
              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? 'Sending...' : 'Send Reset Link'}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleSubmit(onConfirm)} className="space-y-4">
              <div>
                <Input
                  type="password"
                  placeholder="New Password"
                  {...register('new_password', { required: 'Password is required', minLength: { value: 8, message: 'Min length 8' } })}
                />
                {errors.new_password && (
                  <p className="text-sm text-red-600 mt-1">{String(errors.new_password.message)}</p>
                )}
              </div>
              <div>
                <Input
                  type="password"
                  placeholder="Confirm Password"
                  {...register('confirm_password', { required: 'Please confirm', validate: (v) => v === password || 'Passwords do not match' })}
                />
                {errors.confirm_password && (
                  <p className="text-sm text-red-600 mt-1">{String(errors.confirm_password.message)}</p>
                )}
              </div>
              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? 'Updating...' : 'Reset Password'}
              </Button>
            </form>
          )}

          <div className="mt-4 text-center">
            <Link to="/auth/login" search={{ redirect: undefined }} className="text-sm text-blue-600 hover:text-blue-500">
              Back to Sign In
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
