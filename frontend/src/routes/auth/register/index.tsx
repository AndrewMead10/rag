import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'
import { useAuth } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { RegisterData } from '@/lib/types'

export const Route = createFileRoute('/auth/register/')({
  component: RegisterPage,
})

function RegisterPage() {
  const navigate = useNavigate()
  const { register: registerUser } = useAuth()
  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegisterData>()
  
  const password = watch('password')

  const onSubmit = async (data: RegisterData) => {
    try {
      await registerUser.mutateAsync({
        email: data.email,
        password: data.password
      })
      navigate({ to: '/dashboard' })
    } catch (error) {
      console.error('Registration failed:', error)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Create Account</CardTitle>
          <CardDescription>
            Sign up to get started with your account
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
                {...register('password', { 
                  required: 'Password is required',
                  minLength: {
                    value: 8,
                    message: 'Password must be at least 8 characters'
                  }
                })}
              />
              {errors.password && (
                <p className="text-sm text-red-600 mt-1">{errors.password.message}</p>
              )}
            </div>
            
            <div>
              <Input
                type="password"
                placeholder="Confirm Password"
                {...register('confirmPassword', {
                  required: 'Please confirm your password',
                  validate: value => value === password || 'Passwords do not match'
                })}
              />
              {errors.confirmPassword && (
                <p className="text-sm text-red-600 mt-1">{errors.confirmPassword.message}</p>
              )}
            </div>
            
            {registerUser.isError && (
              <p className="text-sm text-red-600">
                {String((registerUser.error as any)?.message || 'Registration failed')}
              </p>
            )}
            
            {registerUser.isSuccess && (
              <p className="text-sm text-green-600">
                Account created successfully! Redirecting...
              </p>
            )}
            
            <Button 
              type="submit" 
              className="w-full"
              disabled={registerUser.isPending}
            >
              {registerUser.isPending ? 'Creating account...' : 'Create Account'}
            </Button>
          </form>
          
          <div className="mt-4 text-center">
            <Link
              to="/auth/login"
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              Already have an account? Sign in
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
