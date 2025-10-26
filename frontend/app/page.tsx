'use client'

import { useEffect, useState, useCallback } from 'react'
import PipelineFlow from '@/components/PipelineFlow'
import StatsPanel from '@/components/StatsPanel'
import RealtimeMonitor from '@/components/RealtimeMonitor'
import { Card } from '@/components/ui/card'

type Status = 'idle' | 'checking' | 'connected' | 'error'

interface StatusState {
  status: Status
  message: string
}

export default function Home() {
  const [status, setStatus] = useState<{
    labelStudio: StatusState
    webhookServer: StatusState
    clearml: StatusState
    pipeline: StatusState
  }>({
    labelStudio: { status: 'checking', message: 'Connecting...' },
    webhookServer: { status: 'checking', message: 'Connecting...' },
    clearml: { status: 'checking', message: 'Connecting...' },
    pipeline: { status: 'idle', message: 'Ready' },
  })

  const [stats, setStats] = useState({
    totalAnnotations: 0,
    datasetVersion: '0.0.0',
    lastSync: null,
    activeWebhooks: 0,
    tasksQueued: 0,
    tasksCompleted: 0,
    tasksFailed: 0,
  })

  const [queueStats, setQueueStats] = useState<any>(null)
  const [batchStats, setBatchStats] = useState<any>(null)

  const [currentStep, setCurrentStep] = useState({
    step: 'idle',
    message: 'Waiting for events...',
    timestamp: null,
    status: 'idle'
  })

  const [events, setEvents] = useState<any[]>([])
  const [ws, setWs] = useState<WebSocket | null>(null)

  // WebSocket connection
  const connectWebSocket = useCallback(() => {
    const websocket = new WebSocket('ws://localhost:8000/ws')

    websocket.onopen = () => {
      console.log('WebSocket connected')
      setStatus(prev => ({
        ...prev,
        webhookServer: {
          status: 'connected',
          message: 'Server running'
        }
      }))
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('WebSocket message:', data)

      if (data.type === 'initial_state') {
        setStats({
          totalAnnotations: data.data.stats.total_annotations,
          datasetVersion: data.data.stats.dataset_version,
          lastSync: data.data.stats.last_sync,
          activeWebhooks: data.data.stats.active_webhooks,
          tasksQueued: data.data.stats.tasks_queued || 0,
          tasksCompleted: data.data.stats.tasks_completed || 0,
          tasksFailed: data.data.stats.tasks_failed || 0,
        })
        setCurrentStep(data.data.current_step)
        setEvents(data.data.recent_events || [])
        // Set queue stats if available (optimized server)
        if (data.data.queue_stats) {
          setQueueStats(data.data.queue_stats)
        }
        // Set batch stats if available
        if (data.data.batch_stats) {
          setBatchStats(data.data.batch_stats)
        }
      } else if (data.type === 'step_update') {
        setCurrentStep(data.data)
      } else if (data.type === 'stats_update') {
        setStats({
          totalAnnotations: data.data.total_annotations,
          datasetVersion: data.data.dataset_version,
          lastSync: data.data.last_sync,
          activeWebhooks: data.data.active_webhooks,
          tasksQueued: data.data.tasks_queued || 0,
          tasksCompleted: data.data.tasks_completed || 0,
          tasksFailed: data.data.tasks_failed || 0,
        })
      } else if (data.type === 'queue_stats_update') {
        // Update queue stats from optimized server
        setQueueStats(data.data)
      } else if (data.type === 'batch_stats_update') {
        // Update batch stats
        setBatchStats(data.data)
      } else {
        // Add other events to the list
        setEvents(prev => [data, ...prev].slice(0, 20))
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
      setStatus(prev => ({
        ...prev,
        webhookServer: {
          status: 'error',
          message: 'Connection error'
        }
      }))
    }

    websocket.onclose = () => {
      console.log('WebSocket disconnected')
      setStatus(prev => ({
        ...prev,
        webhookServer: {
          status: 'error',
          message: 'Server offline'
        }
      }))
      
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        if (websocket.readyState === WebSocket.CLOSED) {
          connectWebSocket()
        }
      }, 3000)
    }

    setWs(websocket)

    return websocket
  }, [])

  const handleProcessBatch = async () => {
    try {
      const response = await fetch('http://localhost:8000/batch/process-all', {
        method: 'POST',
      })
      const result = await response.json()
      console.log('Batch processing triggered:', result)
      // The UI will update via WebSocket when processing completes
    } catch (error) {
      console.error('Error triggering batch processing:', error)
    }
  }

  useEffect(() => {
    const websocket = connectWebSocket()

    // Simulate other status checks
    setTimeout(() => {
      setStatus(prev => ({
        ...prev,
        labelStudio: {
          status: 'connected',
          message: 'Label Studio running on :8080'
        },
        clearml: {
          status: 'connected',
          message: 'Connected to ClearML'
        }
      }))
    }, 1000)

    return () => {
      if (websocket) {
        websocket.close()
      }
    }
  }, [connectWebSocket])

  return (
    <main className="min-h-screen bg-background">
      <div className="container mx-auto p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-[hsl(var(--verdigris))] to-[hsl(var(--dark-cyan))] bg-clip-text text-transparent">
            Label Studio to ClearML Pipeline
          </h1>
          <p className="text-muted-foreground">
            Real-time monitoring and visualization of your ML annotation pipeline
          </p>
        </div>

        {/* Stats Panel */}
        <StatsPanel 
          stats={stats} 
          queueStats={queueStats} 
          batchStats={batchStats}
          onProcessBatch={handleProcessBatch}
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Pipeline Flow Visualization */}
          <Card className="p-8 shadow-lg">
            <PipelineFlow status={status} />
          </Card>

          {/* Real-time Monitor */}
          <div>
            <RealtimeMonitor currentStep={currentStep} events={events} />
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-muted-foreground">
          <p>
            Monitor your pipeline in real-time • 
            <a href="http://localhost:8080" target="_blank" className="ml-2 text-primary hover:underline">
              Open Label Studio
            </a> • 
            <a href="https://app.clear.ml" target="_blank" className="ml-2 text-primary hover:underline">
              Open ClearML
            </a>
          </p>
        </div>
      </div>
    </main>
  )
}
