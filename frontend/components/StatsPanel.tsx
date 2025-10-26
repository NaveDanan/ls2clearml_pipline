'use client'

import { motion } from 'framer-motion'
import { FileText, Package, Clock, Activity, ListChecks, XCircle, Zap, Database, Calendar, Layers } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface StatsProps {
  stats: {
    totalAnnotations: number
    datasetVersion: string
    lastSync: string | null
    activeWebhooks: number
    tasksQueued?: number
    tasksCompleted?: number
    tasksFailed?: number
  }
  queueStats?: {
    queue_size: number
    total_tasks: number
    pending: number
    processing: number
    completed: number
    failed: number
    workers: number
    running: boolean
  }
  batchStats?: {
    total_annotations_batched: number
    total_datasets_created: number
    last_batch_process: string | null
    next_scheduled_process: string | null
    batch_interval_minutes: number
    total_pending_annotations: number
  }
  onProcessBatch?: () => void
}

const StatCard = ({ 
  icon: Icon, 
  label, 
  value, 
  delay = 0 
}: { 
  icon: any
  label: string
  value: string | number
  delay?: number
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3, delay }}
    >
      <Card className="hover:shadow-lg transition-shadow">
        <CardContent className="p-6">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-primary/10 rounded-lg">
              <Icon className="w-6 h-6 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">{label}</p>
              <p className="text-2xl font-bold">{value}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default function StatsPanel({ stats, queueStats, batchStats, onProcessBatch }: StatsProps) {
  // Check if using optimized server (has queue stats)
  const isOptimized = !!queueStats
  const hasBatchStats = !!batchStats

  const formatNextScheduled = (isoString: string | null) => {
    if (!isoString) return 'Not scheduled'
    const date = new Date(isoString)
    return date.toLocaleTimeString()
  }

  return (
    <div className="space-y-4 mb-8">
      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={FileText}
          label="Total Annotations"
          value={stats.totalAnnotations}
          delay={0}
        />
        <StatCard
          icon={Package}
          label="Dataset Version"
          value={stats.datasetVersion}
          delay={0.1}
        />
        <StatCard
          icon={Clock}
          label="Last Sync"
          value={stats.lastSync ? new Date(stats.lastSync).toLocaleTimeString() : 'Never'}
          delay={0.2}
        />
        <StatCard
          icon={Activity}
          label="Active Webhooks"
          value={stats.activeWebhooks}
          delay={0.3}
        />
      </div>

      {/* Batch Stats (Annotation Batching System) */}
      {hasBatchStats && batchStats && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Layers className="w-5 h-5 text-[hsl(var(--verdigris))]" />
              <h3 className="text-lg font-semibold text-[hsl(var(--foreground))]">Batch Annotation System</h3>
            </div>
            {onProcessBatch && (
              <Button
                onClick={onProcessBatch}
                size="sm"
                className="bg-[hsl(var(--verdigris))] hover:bg-[hsl(var(--dark-cyan))] text-white"
              >
                <Database className="w-4 h-4 mr-2" />
                Process Batches Now
              </Button>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              icon={Layers}
              label="Pending Annotations"
              value={batchStats.total_pending_annotations}
              delay={0}
            />
            <StatCard
              icon={Database}
              label="Datasets Created"
              value={batchStats.total_datasets_created}
              delay={0.1}
            />
            <StatCard
              icon={Calendar}
              label="Next Scheduled"
              value={formatNextScheduled(batchStats.next_scheduled_process)}
              delay={0.2}
            />
            <StatCard
              icon={Clock}
              label="Batch Interval"
              value={`${batchStats.batch_interval_minutes} min`}
              delay={0.3}
            />
          </div>
        </div>
      )}

      {/* Queue Stats (only for optimized server) */}
      {isOptimized && queueStats && (
        <div>
          <div className="flex items-center space-x-2 mb-3">
            <Zap className="w-5 h-5 text-[hsl(var(--verdigris))]" />
            <h3 className="text-lg font-semibold text-[hsl(var(--foreground))]">Task Queue Statistics</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              icon={Activity}
              label="Queue Size"
              value={queueStats.queue_size}
              delay={0}
            />
            <StatCard
              icon={ListChecks}
              label="Tasks Completed"
              value={`${queueStats.completed}/${queueStats.total_tasks}`}
              delay={0.1}
            />
            <StatCard
              icon={XCircle}
              label="Tasks Failed"
              value={queueStats.failed}
              delay={0.2}
            />
            <StatCard
              icon={Zap}
              label="Active Workers"
              value={`${queueStats.processing}/${queueStats.workers}`}
              delay={0.3}
            />
          </div>
        </div>
      )}
    </div>
  )
}
