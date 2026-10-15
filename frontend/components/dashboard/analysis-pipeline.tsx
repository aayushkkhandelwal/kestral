import { Check, Loader2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { PIPELINE_STEPS } from '@/lib/dashboard-data'
import { cn } from '@/lib/utils'
import { SectionHeader } from './section-header'

export function AnalysisPipeline({ activeStep, processing }: { activeStep: number; processing: boolean }) {
  const completedCount = processing ? activeStep : PIPELINE_STEPS.length

  return (
    <section aria-labelledby="pipeline-heading" className="flex flex-col gap-4">
      <div id="pipeline-heading">
        <SectionHeader
          title="Analysis Pipeline"
          description={
            processing ? `Running ${PIPELINE_STEPS[activeStep]}...` : 'All stages complete. Best evidence frame selected.'
          }
          action={
            <Badge variant={processing ? 'default' : 'secondary'} className="tabular-nums">
              {completedCount}/{PIPELINE_STEPS.length} stages
            </Badge>
          }
        />
      </div>

      <div className="overflow-x-auto rounded-xl bg-card p-6 border">
        <ol className="flex min-w-[720px] items-start">
          {PIPELINE_STEPS.map((step, index) => {
            const isComplete = !processing || index < activeStep
            const isActive = processing && index === activeStep
            const isLast = index === PIPELINE_STEPS.length - 1

            return (
              <li
                key={step}
                className="relative flex flex-1 flex-col items-center gap-3 text-center"
                aria-current={isActive ? 'step' : undefined}
              >
                {!isLast && (
                  <span
                    aria-hidden="true"
                    className={cn(
                      'absolute top-4 left-[calc(50%+22px)] h-px w-[calc(100%-44px)] transition-colors duration-500',
                      isComplete && (!processing || index + 1 <= activeStep) ? 'bg-primary' : 'bg-border',
                    )}
                  />
                )}
                <span
                  className={cn(
                    'relative z-10 flex size-8 items-center justify-center rounded-full text-xs font-medium transition-all duration-300',
                    isComplete && 'bg-primary text-primary-foreground',
                    isActive && 'bg-primary/15 text-primary ring-2 ring-primary ring-offset-2 ring-offset-card',
                    !isComplete && !isActive && 'bg-muted text-muted-foreground',
                  )}
                >
                  {isComplete ? (
                    <Check className="size-4" aria-hidden="true" />
                  ) : isActive ? (
                    <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                  ) : (
                    index + 1
                  )}
                </span>
                <span
                  className={cn(
                    'text-xs leading-tight',
                    isActive ? 'font-medium text-foreground' : isComplete ? 'text-foreground' : 'text-muted-foreground',
                  )}
                >
                  {step}
                  <span className="sr-only">
                    {isComplete ? ' (complete)' : isActive ? ' (in progress)' : ' (pending)'}
                  </span>
                </span>
              </li>
            )
          })}
        </ol>
      </div>
    </section>
  )
}
