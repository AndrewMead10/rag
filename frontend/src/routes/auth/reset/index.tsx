import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
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
    <div className="min-h-screen bg-background dither-bg font-mono-jetbrains flex items-center justify-center px-4">
      <div className="w-full max-w-md space-y-8">
        {/* Main title */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-black dither-text leading-none">
            RETRIEVER.<span className="font-bold">SH</span>
          </h1>
          <div className="h-1 bg-foreground dither-border mx-auto w-32"></div>
          <p className="text-lg text-muted-foreground font-mono-jetbrains">
            {token ? 'Reset your password' : 'Request a password reset'}
          </p>
        </div>

        {/* Reset form container */}
        <div className="bg-card border-2 border-foreground dither-border sharp-corners p-8 space-y-6">
          {!token ? (
            <form onSubmit={handleSubmit(onRequest)} className="space-y-4">
              <div className="space-y-2">
                <div className="text-xs font-bold mb-2">// EMAIL</div>
                <Input
                  type="email"
                  placeholder="Enter your email"
                  className="bg-background border-foreground sharp-corners font-mono-jetbrains"
                  {...register('email', { required: 'Email is required' })}
                />
                {errors.email && (
                  <p className="text-sm text-destructive font-mono-jetbrains">{String(errors.email.message)}</p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full bg-foreground text-background font-bold hover:bg-muted hover:text-foreground transition-all duration-200 dither-text sharp-corners border-2 border-foreground py-3"
                disabled={isSubmitting}
              >
                {isSubmitting ? '[ SENDING... ]' : '[ SEND RESET LINK ]'}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleSubmit(onConfirm)} className="space-y-4">
              <div className="space-y-2">
                <div className="text-xs font-bold mb-2">// NEW PASSWORD</div>
                <Input
                  type="password"
                  placeholder="Enter new password"
                  className="bg-background border-foreground sharp-corners font-mono-jetbrains"
                  {...register('new_password', {
                    required: 'Password is required',
                    minLength: { value: 8, message: 'Password must be at least 8 characters' }
                  })}
                />
                {errors.new_password && (
                  <p className="text-sm text-destructive font-mono-jetbrains">{String(errors.new_password.message)}</p>
                )}
              </div>

              <div className="space-y-2">
                <div className="text-xs font-bold mb-2">// CONFIRM PASSWORD</div>
                <Input
                  type="password"
                  placeholder="Confirm new password"
                  className="bg-background border-foreground sharp-corners font-mono-jetbrains"
                  {...register('confirm_password', {
                    required: 'Please confirm your password',
                    validate: (v) => v === password || 'Passwords do not match'
                  })}
                />
                {errors.confirm_password && (
                  <p className="text-sm text-destructive font-mono-jetbrains">{String(errors.confirm_password.message)}</p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full bg-foreground text-background font-bold hover:bg-muted hover:text-foreground transition-all duration-200 dither-text sharp-corners border-2 border-foreground py-3"
                disabled={isSubmitting}
              >
                {isSubmitting ? '[ UPDATING... ]' : '[ RESET PASSWORD ]'}
              </Button>
            </form>
          )}
        </div>

        {/* Links */}
        <div className="text-center space-y-4">
          <div className="flex justify-center text-sm font-mono-jetbrains">
            <Link
              to="/auth/login"
              search={{ redirect: undefined }}
              className="text-muted-foreground hover:text-foreground transition-colors duration-200"
            >
              [ BACK TO SIGN IN ]
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
