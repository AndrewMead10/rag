import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'
import { useAuth } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { LoginData } from '@/lib/types'

export const Route = createFileRoute('/auth/login/')({
  component: LoginPage,
  validateSearch: (search: Record<string, unknown>) => ({
    redirect: typeof search.redirect === 'string' ? search.redirect : undefined,
  }),
})

function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const { register, handleSubmit, formState: { errors } } = useForm<LoginData>()
  const { redirect } = Route.useSearch()
  const targetPath = redirect ?? '/dashboard'

  const onSubmit = async (data: LoginData) => {
    try {
      await login.mutateAsync(data)
      navigate({ to: targetPath as any })
    } catch (error) {
      console.error('Login failed:', error)
    }
  }

  const handleGoogleSignIn = () => {
    const params = new URLSearchParams()
    if (redirect) {
      params.set('redirect', redirect)
    }
    const query = params.toString()
    window.location.href = query
      ? `/auth/google/login?${query}`
      : '/auth/google/login'
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sign In</CardTitle>
          <CardDescription>
            Enter your credentials to access your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <Input
                type="email"
                placeholder="Email"
                {...register('email', { 
                  required: 'Email is required',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Invalid email address'
                  }
                })}
              />
              {errors.email && (
                <p className="text-sm text-red-600 mt-1">{errors.email.message}</p>
              )}
            </div>
            
            <div>
              <Input
                type="password"
                placeholder="Password"
                {...register('password', { required: 'Password is required' })}
              />
              {errors.password && (
                <p className="text-sm text-red-600 mt-1">{errors.password.message}</p>
              )}
            </div>
            
            {login.isError && (
              <p className="text-sm text-red-600">
                {String((login.error as any)?.message || 'Login failed')}
              </p>
            )}
            
            <Button 
              type="submit" 
              className="w-full"
              disabled={login.isPending}
            >
              {login.isPending ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-gray-200" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-2 text-gray-500">
                  Or continue with
                </span>
              </div>
            </div>
            <Button
              type="button"
              variant="outline"
              className="mt-4 w-full"
              onClick={handleGoogleSignIn}
            >
              Continue with Google
            </Button>
          </div>
          
          <div className="mt-4 text-center">
            <Link
              to="/auth/reset"
              className="text-sm text-blue-600 hover:text-blue-500 mr-4"
            >
              Forgot your password?
            </Link>
            <Link
              to="/auth/register"
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              Don't have an account? Sign up
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
