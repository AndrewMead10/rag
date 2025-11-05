import { useState, type ReactNode } from 'react'
import { createFileRoute, redirect, Link } from '@tanstack/react-router'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { api, useCreateProject, useProjects } from '@/lib/api'
import type { ProjectCreatePayload } from '@/lib/types'
import { queryClient } from '@/routes/__root'
import { formatNumber, formatVectorLimit } from '@/utils/format'

export const Route = createFileRoute('/projects/')({
  beforeLoad: async () => {
    try {
      await queryClient.ensureQueryData({
        queryKey: ['user'],
        queryFn: api.auth.getCurrentUser,
      })
      await queryClient.ensureQueryData({
        queryKey: ['projects'],
        queryFn: api.projects.list,
      })
    } catch {
      throw redirect({ to: '/auth/login', search: { redirect: undefined } })
    }
  },
  component: ProjectsPage,
})

function ProjectsPage() {
  const { data, isLoading, error } = useProjects()
  const createProject = useCreateProject()
  const [showCreate, setShowCreate] = useState(false)
  const [formState, setFormState] = useState<ProjectCreatePayload>({
    name: '',
    description: '',
  })

  const upgrade = useMutation({
    mutationFn: api.billing.upgrade,
    onSuccess: (url) => {
      toast.success('Redirecting to Polar Checkout...')
      window.location.href = url
    },
    onError: (err: any) => {
      toast.error(err?.message || 'Unable to start upgrade')
    },
  })

  const topUp = useMutation({
    mutationFn: async (quantity: number) => api.billing.topUp(quantity),
    onSuccess: (url) => {
      toast.success('Redirecting to Polar Checkout...')
      window.location.href = url
    },
    onError: (err: any) => {
      toast.error(err?.message || 'Unable to purchase top-up')
    },
  })

  const portal = useMutation({
    mutationFn: api.billing.portal,
    onSuccess: (url) => {
      window.location.href = url
    },
    onError: (err: any) => {
      toast.error(err?.message || 'Unable to open billing portal')
    },
  })

  const enterpriseRequest = useMutation({
    mutationFn: api.billing.enterprise,
    onSuccess: () => toast.success('Thanks! We will reach out shortly.'),
    onError: (err: any) => toast.error(err?.message || 'Unable to submit request'),
  })

  const handleCreateProject = async () => {
    if (data?.needs_subscription) {
      toast.error('Start a subscription to create projects.')
      return
    }
    try {
      const result = await createProject.mutateAsync(formState)
      setShowCreate(false)
      setFormState({ name: '', description: '' })
      toast.success('Project created. API key copied to clipboard.')
      try {
        await navigator.clipboard.writeText(result.ingest_api_key)
      } catch {
        toast('API Key', { description: result.ingest_api_key })
      }
    } catch (err: any) {
      toast.error(err?.message || 'Failed to create project')
    }
  }

  const handleTopUpClick = () => {
    const value = window.prompt('How many million vectors would you like to purchase?', '1')
    if (!value) return
    const quantity = Number.parseInt(value, 10)
    if (Number.isNaN(quantity) || quantity <= 0) {
      toast.error('Enter a positive integer quantity')
      return
    }
    topUp.mutate(quantity)
  }

  const handleEnterpriseRequest = () => {
    const message = window.prompt('Tell us what you need for dedicated deployments:')
    if (!message) return
    enterpriseRequest.mutate(message)
  }

  if (isLoading) {
    return <div className="max-w-7xl mx-auto py-10 px-4">Loading projects...</div>
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto py-10 px-4 text-red-600">
        Failed to load projects: {String((error as any)?.message || 'Unknown error')}
      </div>
    )
  }

  const plan = data?.plan
  const needsSubscription = data?.needs_subscription ?? false
  const usage = data?.usage
  const projects = data?.projects ?? []
  const vectorLimit = usage?.vector_limit ?? null
  const vectorPercent = vectorLimit
    ? Math.min(100, Math.round((usage!.total_vectors / vectorLimit) * 100))
    : 0
  const projectLimit = usage?.project_limit ?? null
  const projectPercent = projectLimit
    ? Math.min(100, Math.round((usage!.project_count / projectLimit) * 100))
    : 0
  const approxVectorsPerProject =
    plan && plan.project_limit && plan.project_limit > 0 && vectorLimit
      ? Math.floor(vectorLimit / plan.project_limit)
      : null

  return (
    <div className="max-w-7xl mx-auto py-10 px-4 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Projects</h1>
          <p className="text-muted-foreground">Manage retrieval workspaces, usage, and billing.</p>
        </div>
        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogTrigger asChild>
            <Button disabled={needsSubscription}>
              {needsSubscription ? 'Subscription Required' : 'Create Project'}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>New Project</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <Label htmlFor="project-name">Name</Label>
                <Input
                  id="project-name"
                  placeholder="My App"
                  value={formState.name}
                  onChange={(event) => setFormState((prev) => ({ ...prev, name: event.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="project-description">Description (optional)</Label>
                <Textarea
                  id="project-description"
                  rows={3}
                  value={formState.description ?? ''}
                  onChange={(event) =>
                    setFormState((prev) => ({ ...prev, description: event.target.value }))
                  }
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowCreate(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreateProject}
                disabled={!formState.name || createProject.isPending || data?.needs_subscription}
              >
                {createProject.isPending ? 'Creating...' : 'Create'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {needsSubscription && (
        <Card className="border-dashed">
          <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle className="text-xl">No Active Subscription</CardTitle>
              <CardDescription>
                Start a plan to unlock project creation, vector storage, and API access.
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button onClick={() => upgrade.mutate()} disabled={upgrade.isPending}>
                {upgrade.isPending ? 'Preparing checkout…' : 'Get a Subscription'}
              </Button>
              <Button variant="outline" asChild>
                <Link to="/" hash="pricing">
                  View Pricing
                </Link>
              </Button>
            </div>
          </CardHeader>
        </Card>
      )}

      {!needsSubscription && plan && usage && (
        <Card>
          <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle className="text-xl">{plan.name} Plan</CardTitle>
              <CardDescription>
                {plan.slug === 'testing'
                  ? 'Trial the platform on Testing and upgrade when ready.'
                  : 'Your active subscription'}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              {plan.slug === 'testing' && (
                <Button onClick={() => upgrade.mutate()} disabled={upgrade.isPending}>
                  {upgrade.isPending ? 'Redirecting...' : 'Upgrade to Building'}
                </Button>
              )}
              {plan.allow_topups && (
                <Button variant="outline" onClick={handleTopUpClick} disabled={topUp.isPending}>
                  {topUp.isPending ? 'Preparing...' : 'Buy Vector Top-Up'}
                </Button>
              )}
              {plan.slug !== 'testing' && (
                <Button variant="ghost" onClick={() => portal.mutate()} disabled={portal.isPending}>
                  Billing Portal
                </Button>
              )}
              <Button variant="ghost" onClick={handleEnterpriseRequest} disabled={enterpriseRequest.isPending}>
                Contact Enterprise
              </Button>
            </div>
          </CardHeader>
          <CardContent className="grid gap-6 md:grid-cols-3">
            <MetricCard title="Query QPS" value={`${plan.query_qps_limit}`} help="per second" />
            <MetricCard title="Ingest QPS" value={`${plan.ingest_qps_limit}`} help="per second" />
            <MetricCard
              title="Vectors"
              value={formatVectorLimit(usage.total_vectors, vectorLimit)}
              help={
                approxVectorsPerProject
                  ? `≈ ${formatNumber(approxVectorsPerProject)} per project`
                  : vectorLimit === null
                    ? 'Per project unlimited'
                    : undefined
              }
            >
              {vectorLimit && (
                <Progress value={vectorPercent} className="mt-2" />
              )}
            </MetricCard>
            <MetricCard title="Projects" value={`${usage.project_count}`}> 
              {projectLimit && (
                <Progress value={projectPercent} className="mt-2" />
              )}
            </MetricCard>
            <MetricCard title="Total Queries" value={formatNumber(usage.total_queries)} />
            <MetricCard title="Ingest Requests" value={formatNumber(usage.total_ingest_requests)} />
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Projects</CardTitle>
          <CardDescription>Each project has its own vector store and API key.</CardDescription>
        </CardHeader>
        <CardContent>
          {projects.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              {needsSubscription
                ? 'Choose a subscription to start creating projects.'
                : 'No projects yet. Create one to get started.'}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Vectors</TableHead>
                  <TableHead>Embedding</TableHead>
                  <TableHead>Hybrid Weights</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {projects.map((project) => (
                  <TableRow key={project.id}>
                    <TableCell className="font-medium">
                      <div className="flex flex-col">
                        <span>{project.name}</span>
                        {project.description && (
                          <span className="text-xs text-muted-foreground">{project.description}</span>
                        )}
                        <Badge variant="outline" className="mt-1 w-fit">
                          ID #{project.id}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>{formatNumber(project.vector_count)}</TableCell>
                    <TableCell>
                      <div className="flex flex-col text-sm">
                        <span>{project.embedding_provider}</span>
                        <span className="text-muted-foreground">
                          {project.embedding_model}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        vector {project.hybrid_weight_vector.toFixed(2)} / text {project.hybrid_weight_text.toFixed(2)}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

interface MetricCardProps {
  title: string
  value: string
  help?: string
  children?: ReactNode
}

function MetricCard({ title, value, help, children }: MetricCardProps) {
  return (
    <div className="rounded-lg border p-4 bg-muted/30">
      <div className="text-sm text-muted-foreground">{title}</div>
      <div className="text-2xl font-semibold">{value}</div>
      {help && <div className="text-xs text-muted-foreground">{help}</div>}
      {children}
    </div>
  )
}
