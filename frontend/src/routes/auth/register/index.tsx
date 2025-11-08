import { createFileRoute, Link } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'
import { useAuth } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { RegisterData } from '@/lib/types'

function GoogleIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
  )
}

export const Route = createFileRoute('/auth/register/')({
  component: RegisterPage,
})

function RegisterPage() {
  const { register: registerUser } = useAuth({ fetchUser: false })
  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegisterData>()
  
  const password = watch('password')

  const onSubmit = async (data: RegisterData) => {
    try {
      await registerUser.mutateAsync({
        email: data.email,
        password: data.password
      })
      // Don't navigate - user needs to verify email first
    } catch (error) {
      console.error('Registration failed:', error)
    }
  }

  const handleGoogleSignIn = () => {
    window.location.href = '/api/auth/google/login'
  }

  return (
    <div className="min-h-screen bg-background dither-bg font-mono-jetbrains flex items-center justify-center px-4">
      <div className="w-full max-w-md space-y-8">
        {/* Main title */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-black dither-text leading-none">
            RETRIEVER.<span className="font-bold">SH</span>
          </h1>
          <div className="h-1 bg-foreground dither-border mx-auto w-32"></div>
          <p className="text-lg text-muted-foreground font-mono-jetbrains">
            Create your search API account
          </p>
        </div>

        {/* Register form container */}
        <div className="bg-card border-2 border-foreground dither-border sharp-corners p-8 space-y-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <div className="text-xs font-bold mb-2">// EMAIL</div>
              <Input
                type="email"
                placeholder="Enter your email"
                className="bg-background border-foreground sharp-corners font-mono-jetbrains"
                {...register('email', {
                  required: 'Email is required',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Invalid email address'
                  }
                })}
              />
              {errors.email && (
                <p className="text-sm text-destructive font-mono-jetbrains">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <div className="text-xs font-bold mb-2">// PASSWORD</div>
              <Input
                type="password"
                placeholder="Create a password"
                className="bg-background border-foreground sharp-corners font-mono-jetbrains"
                {...register('password', {
                  required: 'Password is required',
                  minLength: {
                    value: 8,
                    message: 'Password must be at least 8 characters'
                  }
                })}
              />
              {errors.password && (
                <p className="text-sm text-destructive font-mono-jetbrains">{errors.password.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <div className="text-xs font-bold mb-2">// CONFIRM PASSWORD</div>
              <Input
                type="password"
                placeholder="Confirm your password"
                className="bg-background border-foreground sharp-corners font-mono-jetbrains"
                {...register('confirmPassword', {
                  required: 'Please confirm your password',
                  validate: value => value === password || 'Passwords do not match'
                })}
              />
              {errors.confirmPassword && (
                <p className="text-sm text-destructive font-mono-jetbrains">{errors.confirmPassword.message}</p>
              )}
            </div>

            {registerUser.isError && (
              <div className="bg-destructive/10 border border-destructive p-3 sharp-corners">
                <p className="text-sm text-destructive font-mono-jetbrains">
                  {String((registerUser.error as any)?.message || 'Registration failed')}
                </p>
              </div>
            )}

            {registerUser.isSuccess && (
              <div className="bg-green-600/10 border border-green-600 p-4 sharp-corners">
                <p className="text-sm text-green-600 dark:text-green-400 font-mono-jetbrains font-bold mb-2">
                  // REGISTRATION SUCCESSFUL!
                </p>
                <p className="text-sm text-green-600 dark:text-green-400 font-mono-jetbrains">
                  {registerUser.data?.message || 'Please check your email to verify your account.'}
                </p>
              </div>
            )}

            <Button
              type="submit"
              className="w-full bg-foreground text-background font-bold hover:bg-muted hover:text-foreground transition-all duration-200 dither-text sharp-corners border-2 border-foreground py-3"
              disabled={registerUser.isPending}
            >
              {registerUser.isPending ? '[ CREATING ACCOUNT... ]' : '[ CREATE ACCOUNT ]'}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t-2 border-foreground dither-border"></span>
            </div>
            <div className="relative flex justify-center">
              <span className="bg-card px-4 text-xs font-bold text-muted-foreground">
                // OR CONTINUE WITH
              </span>
            </div>
          </div>

          {/* Google Sign In */}
          <Button
            type="button"
            className="w-full bg-card text-foreground border-2 border-foreground font-bold hover:bg-foreground hover:text-background transition-all duration-200 dither-text sharp-corners py-3"
            onClick={handleGoogleSignIn}
          >
            <GoogleIcon />
            <span className="ml-2">[ CONTINUE WITH GOOGLE ]</span>
          </Button>
        </div>

        {/* Links */}
        <div className="text-center space-y-4">
          <div className="flex justify-center text-sm font-mono-jetbrains">
            <Link
              to="/auth/login"
              search={{ redirect: undefined }}
              className="text-muted-foreground hover:text-foreground transition-colors duration-200"
            >
              [ ALREADY HAVE AN ACCOUNT? SIGN IN ]
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
