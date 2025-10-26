'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Activity, CheckCircle, Loader2, XCircle, AlertCircle, ChevronDown, ChevronRight } from 'lucide-react'

interface Event {
  type: string
  data: any
  timestamp: string
}

interface CurrentStep {
  step: string
  message: string
  timestamp: string | null
  status?: string
}

interface RealtimeMonitorProps {
  currentStep: CurrentStep
  events: Event[]
}

const StepIndicator = ({ step, isActive, isComplete, hasError }: { 
  step: string
  isActive: boolean
  isComplete: boolean
  hasError: boolean
}) => {
  return (
    <div className="flex items-center space-x-2">
      <div className={`
        w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300
        ${isActive ? 'bg-[hsl(var(--verdigris))]/20 ring-2 ring-[hsl(var(--verdigris))]' : ''}
        ${isComplete ? 'bg-[hsl(var(--verdigris))]/30' : ''}
        ${hasError ? 'bg-red-500/20 ring-2 ring-red-500' : ''}
        ${!isActive && !isComplete && !hasError ? 'bg-[hsl(var(--muted))]/20' : ''}
      `}>
        {isActive && <Loader2 className="w-4 h-4 text-[hsl(var(--verdigris))] animate-spin" />}
        {isComplete && !isActive && <CheckCircle className="w-4 h-4 text-[hsl(var(--verdigris))]" />}
        {hasError && <XCircle className="w-4 h-4 text-red-500" />}
        {!isActive && !isComplete && !hasError && <div className="w-2 h-2 rounded-full bg-[hsl(var(--muted-foreground))]" />}
      </div>
      <span className={`
        text-sm font-medium transition-colors
        ${isActive ? 'text-[hsl(var(--verdigris))]' : ''}
        ${isComplete ? 'text-[hsl(var(--foreground))]' : ''}
        ${hasError ? 'text-red-500' : ''}
        ${!isActive && !isComplete && !hasError ? 'text-[hsl(var(--muted-foreground))]' : ''}
      `}>
        {step}
      </span>
    </div>
  )
}

export default function RealtimeMonitor({ currentStep, events }: RealtimeMonitorProps) {
  const [expandedEvent, setExpandedEvent] = useState<number | null>(null)

  const steps = [
    { id: 'idle', label: 'Idle' },
    { id: 'webhook_received', label: 'Webhook Received' },
    { id: 'fetching_annotations', label: 'Fetching Annotations' },
    { id: 'creating_dataset', label: 'Creating Dataset' },
    { id: 'completed', label: 'Completed' },
  ]

  const getStepIndex = (stepId: string) => {
    return steps.findIndex(s => s.id === stepId)
  }

  const currentStepIndex = getStepIndex(currentStep.step)
  const hasError = currentStep.status === 'error'

  const toggleEvent = (index: number) => {
    setExpandedEvent(expandedEvent === index ? null : index)
  }

  return (
    <div className="space-y-6">
      {/* Current Step Card */}
      <Card className="border-2 border-[hsl(var(--border))]">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center space-x-2">
              <Activity className="w-5 h-5 text-[hsl(var(--verdigris))]" />
              <span>Pipeline Status</span>
            </CardTitle>
            <span className={`
              px-3 py-1 rounded-full text-xs font-medium
              ${currentStep.status === 'processing' ? 'bg-[hsl(var(--verdigris))]/20 text-[hsl(var(--verdigris))]' : ''}
              ${currentStep.status === 'success' ? 'bg-[hsl(var(--verdigris))]/30 text-[hsl(var(--verdigris))]' : ''}
              ${currentStep.status === 'error' ? 'bg-red-500/20 text-red-500' : ''}
              ${currentStep.status === 'idle' ? 'bg-[hsl(var(--muted))]/20 text-[hsl(var(--muted-foreground))]' : ''}
            `}>
              {currentStep.status || 'idle'}
            </span>
          </div>
        </CardHeader>
        <CardContent>
          {/* Steps Progress */}
          <div className="space-y-3 mb-6">
            {steps.map((step, index) => (
              <StepIndicator
                key={step.id}
                step={step.label}
                isActive={currentStepIndex === index && currentStep.status === 'processing'}
                isComplete={currentStepIndex > index || (currentStepIndex === index && currentStep.status === 'success')}
                hasError={currentStepIndex === index && hasError}
              />
            ))}
          </div>

          {/* Current Message */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep.message}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`
                p-4 rounded-lg border-l-4
                ${currentStep.status === 'processing' ? 'bg-[hsl(var(--verdigris))]/5 border-[hsl(var(--verdigris))]' : ''}
                ${currentStep.status === 'success' ? 'bg-[hsl(var(--verdigris))]/10 border-[hsl(var(--verdigris))]' : ''}
                ${currentStep.status === 'error' ? 'bg-red-500/5 border-red-500' : ''}
                ${currentStep.status === 'idle' ? 'bg-[hsl(var(--muted))]/5 border-[hsl(var(--muted))]' : ''}
              `}
            >
              <p className="text-sm font-medium">{currentStep.message}</p>
              {currentStep.timestamp && (
                <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">
                  {new Date(currentStep.timestamp).toLocaleTimeString()}
                </p>
              )}
            </motion.div>
          </AnimatePresence>
        </CardContent>
      </Card>

      {/* Recent Events */}
      <Card className="border-2 border-[hsl(var(--border))]">
        <CardHeader>
          <CardTitle className="text-lg">Recent Events</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {events.length === 0 ? (
              <p className="text-sm text-[hsl(var(--muted-foreground))] text-center py-4">
                No events yet
              </p>
            ) : (
              events.map((event, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`
                    rounded-lg bg-[hsl(var(--card))] border transition-all duration-200
                    ${expandedEvent === index 
                      ? 'border-[hsl(var(--verdigris))]' 
                      : 'border-[hsl(var(--border))] hover:border-[hsl(var(--verdigris))]/50'
                    }
                  `}
                >
                  <div 
                    className="p-3 cursor-pointer"
                    onClick={() => toggleEvent(index)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 flex items-start space-x-2">
                        {expandedEvent === index ? (
                          <ChevronDown className="w-4 h-4 text-[hsl(var(--verdigris))] mt-0.5 flex-shrink-0" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-[hsl(var(--muted-foreground))] mt-0.5 flex-shrink-0" />
                        )}
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <span className={`
                              w-2 h-2 rounded-full
                              ${event.type.includes('error') ? 'bg-red-500' : 'bg-[hsl(var(--verdigris))]'}
                            `} />
                            <span className="text-sm font-medium capitalize">
                              {event.type.replace(/_/g, ' ')}
                            </span>
                          </div>
                          {event.data && !expandedEvent && (
                            <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">
                              {typeof event.data === 'string' 
                                ? event.data.substring(0, 100)
                                : JSON.stringify(event.data).substring(0, 100)}
                              {JSON.stringify(event.data).length > 100 ? '...' : ''}
                            </p>
                          )}
                        </div>
                      </div>
                      <span className="text-xs text-[hsl(var(--muted-foreground))] whitespace-nowrap ml-2">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                  
                  {/* Expanded JSON View */}
                  <AnimatePresence>
                    {expandedEvent === index && event.data && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <div className="px-3 pb-3 pt-0">
                          <div className="bg-[hsl(var(--muted))]/30 rounded-md p-3 border border-[hsl(var(--border))]">
                            <pre className="text-xs font-mono text-[hsl(var(--foreground))] overflow-x-auto max-h-96 overflow-y-auto">
                              {JSON.stringify(event.data, null, 2)}
                            </pre>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
