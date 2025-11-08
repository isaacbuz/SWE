'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { WizardSteps } from '@/components/wizard/wizard-steps'
import { WizardNavigation } from '@/components/wizard/wizard-navigation'
import { mockAgents } from '@/lib/api/mock-data'
import { Rocket, Wrench, Bug, CheckCircle } from 'lucide-react'
import { useState } from 'react'

const steps = [
  { id: '1', title: 'Select Goal', description: 'Choose your objective' },
  { id: '2', title: 'Choose Agents', description: 'Pick your team' },
  { id: '3', title: 'Configure', description: 'Set parameters' },
  { id: '4', title: 'Review & Launch', description: 'Final review' },
]

const goals = [
  {
    id: 'mvp',
    icon: <Rocket className="w-8 h-8" />,
    title: 'Ship MVP',
    description: 'Plan, design, implement, test, deploy',
  },
  {
    id: 'refactor',
    icon: <Wrench className="w-8 h-8" />,
    title: 'Refactor Legacy',
    description: 'Analyze, plan migration, incremental updates',
  },
  {
    id: 'incident',
    icon: <Bug className="w-8 h-8" />,
    title: 'Fix Incident',
    description: 'Diagnose, patch, test, deploy hotfix',
  },
]

export default function CrewComposerPage() {
  const [currentStep, setCurrentStep] = useState(1)
  const [selectedGoal, setSelectedGoal] = useState<string | null>(null)
  const [selectedAgents, setSelectedAgents] = useState<string[]>([])
  const [budget, setBudget] = useState(50)

  const handleNext = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleComplete = () => {
    console.log('Launching crew...', {
      goal: selectedGoal,
      agents: selectedAgents,
      budget,
    })
  }

  const toggleAgent = (agentId: string) => {
    setSelectedAgents((prev) =>
      prev.includes(agentId)
        ? prev.filter((id) => id !== agentId)
        : [...prev, agentId]
    )
  }

  const canGoNext = () => {
    if (currentStep === 1) return selectedGoal !== null
    if (currentStep === 2) return selectedAgents.length > 0
    return true
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Crew Composer</h1>
        <p className="text-muted-foreground mt-1">
          Assemble your AI crew for complex workflows
        </p>
      </div>

      {/* Wizard Steps */}
      <WizardSteps steps={steps} currentStep={currentStep} />

      {/* Step Content */}
      <Card>
        <CardHeader>
          <CardTitle>{steps[currentStep - 1].title}</CardTitle>
          <CardDescription>{steps[currentStep - 1].description}</CardDescription>
        </CardHeader>
        <CardContent className="min-h-[400px]">
          {/* Step 1: Select Goal */}
          {currentStep === 1 && (
            <div className="grid gap-4 md:grid-cols-3">
              {goals.map((goal) => (
                <Card
                  key={goal.id}
                  className={`cursor-pointer transition-all ${
                    selectedGoal === goal.id
                      ? 'ring-2 ring-primary bg-primary/5'
                      : 'hover:shadow-md'
                  }`}
                  onClick={() => setSelectedGoal(goal.id)}
                >
                  <CardHeader>
                    <div className="text-primary mb-2">{goal.icon}</div>
                    <CardTitle className="text-lg">{goal.title}</CardTitle>
                    <CardDescription>{goal.description}</CardDescription>
                  </CardHeader>
                </Card>
              ))}
            </div>
          )}

          {/* Step 2: Choose Agents */}
          {currentStep === 2 && (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {mockAgents.map((agent) => (
                <Card
                  key={agent.id}
                  className={`cursor-pointer transition-all ${
                    selectedAgents.includes(agent.id)
                      ? 'ring-2 ring-primary bg-primary/5'
                      : 'hover:shadow-md'
                  }`}
                  onClick={() => toggleAgent(agent.id)}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        <div className="text-2xl">{agent.avatar || '🤖'}</div>
                        <div>
                          <CardTitle className="text-base">{agent.name}</CardTitle>
                          <CardDescription className="text-xs">
                            {agent.role}
                          </CardDescription>
                        </div>
                      </div>
                      {selectedAgents.includes(agent.id) && (
                        <CheckCircle className="w-5 h-5 text-primary" />
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-1">
                      {agent.skills.slice(0, 2).map((skill) => (
                        <Badge key={skill} variant="outline" className="text-xs">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Step 3: Configure */}
          {currentStep === 3 && (
            <div className="space-y-6 max-w-xl">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Cost Budget: ${budget}
                </label>
                <input
                  type="range"
                  min="10"
                  max="200"
                  value={budget}
                  onChange={(e) => setBudget(Number(e.target.value))}
                  className="w-full"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Model Preference
                </label>
                <select className="w-full border rounded-md p-2">
                  <option>Balanced (Claude + GPT-4)</option>
                  <option>Fast (Haiku + GPT-4o)</option>
                  <option>Premium (Opus + GPT-4)</option>
                </select>
              </div>
            </div>
          )}

          {/* Step 4: Review */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Crew Summary</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="text-sm font-medium text-muted-foreground mb-1">
                      Goal
                    </div>
                    <div className="text-lg">
                      {goals.find((g) => g.id === selectedGoal)?.title}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-muted-foreground mb-2">
                      Selected Agents
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {selectedAgents.map((agentId) => {
                        const agent = mockAgents.find((a) => a.id === agentId)
                        return (
                          <Badge key={agentId} variant="secondary">
                            {agent?.name}
                          </Badge>
                        )
                      })}
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4 pt-4 border-t">
                    <div>
                      <div className="text-sm text-muted-foreground">Est. Cost</div>
                      <div className="text-xl font-bold">${budget - 8} - ${budget + 8}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Est. Time</div>
                      <div className="text-xl font-bold">2-3 hours</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Agents</div>
                      <div className="text-xl font-bold">{selectedAgents.length}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </CardContent>

        <div className="px-6 pb-6">
          <WizardNavigation
            currentStep={currentStep}
            totalSteps={steps.length}
            onBack={handleBack}
            onNext={handleNext}
            onComplete={handleComplete}
            canGoNext={canGoNext()}
          />
        </div>
      </Card>
    </div>
  )
}
