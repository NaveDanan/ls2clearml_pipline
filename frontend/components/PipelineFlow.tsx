'use client'

import { motion } from 'framer-motion'
import { Database, Webhook, Cloud, GitBranch, CheckCircle, XCircle, Loader2, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface StatusProps {
  status: 'connected' | 'error' | 'checking' | 'idle'
  message: string
}

interface PipelineFlowProps {
  status: {
    labelStudio: StatusProps
    webhookServer: StatusProps
    clearml: StatusProps
    pipeline: StatusProps
  }
}

const StatusIcon = ({ status }: { status: string }) => {
  switch (status) {
    case 'connected':
      return <CheckCircle className="w-5 h-5 text-[hsl(var(--verdigris))]" />
    case 'error':
      return <XCircle className="w-5 h-5 text-red-500" />
    case 'checking':
      return <Loader2 className="w-5 h-5 text-[hsl(var(--dark-cyan))] animate-spin" />
    case 'idle':
      return <AlertCircle className="w-5 h-5 text-[hsl(var(--muted-foreground))]" />
    default:
      return <AlertCircle className="w-5 h-5 text-[hsl(var(--muted-foreground))]" />
  }
}

const FlowCard = ({ 
  icon: Icon, 
  title, 
  description, 
  status, 
  message,
  delay = 0 
}: { 
  icon: any
  title: string
  description: string
  status: string
  message: string
  delay?: number
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
    >
      <Card className={`
        transition-all duration-300 hover:shadow-xl border-2
        ${status === 'connected' ? 'border-[hsl(var(--verdigris))]/50 bg-[hsl(var(--verdigris))]/5' : ''}
        ${status === 'error' ? 'border-red-500/50 bg-red-500/5' : ''}
        ${status === 'checking' ? 'border-[hsl(var(--dark-cyan))]/50 bg-[hsl(var(--dark-cyan))]/5' : ''}
      `}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`
                p-2 rounded-lg
                ${status === 'connected' ? 'bg-[hsl(var(--verdigris))]/20' : ''}
                ${status === 'error' ? 'bg-red-500/20' : ''}
                ${status === 'checking' ? 'bg-[hsl(var(--dark-cyan))]/20' : ''}
                ${status === 'idle' ? 'bg-[hsl(var(--muted))]/20' : ''}
              `}>
                <Icon className={`
                  w-6 h-6
                  ${status === 'connected' ? 'text-[hsl(var(--verdigris))]' : ''}
                  ${status === 'error' ? 'text-red-500' : ''}
                  ${status === 'checking' ? 'text-[hsl(var(--dark-cyan))]' : ''}
                  ${status === 'idle' ? 'text-[hsl(var(--muted-foreground))]' : ''}
                `} />
              </div>
              <div>
                <CardTitle className="text-lg">{title}</CardTitle>
                <p className="text-sm text-muted-foreground">{description}</p>
              </div>
            </div>
            <StatusIcon status={status} />
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm font-medium">{message}</p>
        </CardContent>
      </Card>
    </motion.div>
  )
}

const FlowConnector = ({ active }: { active: boolean }) => {
  return (
    <div className="flex justify-center my-4">
      <div className="relative">
        <div className="w-1 h-12 bg-gradient-to-b from-[hsl(var(--border))] to-[hsl(var(--muted))] rounded-full" />
        {active && (
          <motion.div
            className="absolute inset-0 w-1 bg-gradient-to-b from-[hsl(var(--verdigris))] to-[hsl(var(--dark-cyan))] rounded-full"
            initial={{ scaleY: 0, originY: 0 }}
            animate={{ scaleY: 1 }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        )}
        {active && (
          <motion.div
            className="absolute left-1/2 -translate-x-1/2 w-3 h-3 bg-[hsl(var(--verdigris))] rounded-full shadow-lg shadow-[hsl(var(--verdigris))]/50"
            animate={{ y: [0, 48, 0] }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        )}
      </div>
    </div>
  )
}

export default function PipelineFlow({ status }: PipelineFlowProps) {
  const isFlowActive = status.webhookServer.status === 'connected'

  return (
    <div className="max-w-3xl mx-auto">
      {/* Label Studio */}
      <FlowCard
        icon={Database}
        title="Label Studio"
        description="with PostgreSQL"
        status={status.labelStudio.status}
        message={status.labelStudio.message}
        delay={0}
      />

      <FlowConnector active={isFlowActive} />

      {/* Webhook Server */}
      <FlowCard
        icon={Webhook}
        title="Webhook Server"
        description="FastAPI"
        status={status.webhookServer.status}
        message={status.webhookServer.message}
        delay={0.1}
      />

      <FlowConnector active={isFlowActive} />

      {/* ClearML Dataset */}
      <FlowCard
        icon={Cloud}
        title="ClearML Dataset API"
        description="Dataset Versioning"
        status={status.clearml.status}
        message={status.clearml.message}
        delay={0.2}
      />

      <FlowConnector active={isFlowActive} />

      {/* ClearML Pipeline */}
      <FlowCard
        icon={GitBranch}
        title="ClearML Pipeline"
        description="Data Prep • Training • Evaluation"
        status={status.pipeline.status}
        message={status.pipeline.message}
        delay={0.3}
      />
    </div>
  )
}
