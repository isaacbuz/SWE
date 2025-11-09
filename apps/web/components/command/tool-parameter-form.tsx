'use client'

import React, { useState, useEffect } from 'react'
import { ToolSpec, ToolExecutionRequest } from '@/lib/api/tools'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select } from '@/components/ui/select'
import { Loader2 } from 'lucide-react'

interface ToolParameterFormProps {
  tool: ToolSpec
  onExecute: (request: ToolExecutionRequest) => Promise<void>
  onCancel: () => void
}

export function ToolParameterForm({ tool, onExecute, onCancel }: ToolParameterFormProps) {
  const [inputs, setInputs] = useState<Record<string, any>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isExecuting, setIsExecuting] = useState(false)

  // Initialize inputs from schema
  useEffect(() => {
    const initial: Record<string, any> = {}
    const schema = tool.jsonSchema
    const properties = schema.properties || {}
    const required = schema.required || []

    Object.keys(properties).forEach((key) => {
      const prop = properties[key]
      if (prop.default !== undefined) {
        initial[key] = prop.default
      } else if (prop.type === 'string') {
        initial[key] = prop.type === 'array' ? '' : ''
      } else if (prop.type === 'number') {
        initial[key] = 0
      } else if (prop.type === 'boolean') {
        initial[key] = false
      } else if (prop.type === 'array') {
        initial[key] = []
      } else if (prop.type === 'object') {
        initial[key] = {}
      }
    })

    setInputs(initial)
  }, [tool])

  const validateInputs = (): boolean => {
    const schema = tool.jsonSchema
    const required = schema.required || []
    const newErrors: Record<string, string> = {}

    required.forEach((key: string) => {
      if (!inputs[key] || (typeof inputs[key] === 'string' && !inputs[key].trim())) {
        newErrors[key] = 'This field is required'
      }
    })

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateInputs()) {
      return
    }

    setIsExecuting(true)
    try {
      await onExecute({
        toolName: tool.name,
        arguments: inputs,
      })
    } finally {
      setIsExecuting(false)
    }
  }

  const updateInput = (key: string, value: any) => {
    setInputs((prev) => ({ ...prev, [key]: value }))
    if (errors[key]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[key]
        return newErrors
      })
    }
  }

  const renderInput = (key: string, prop: any) => {
    const value = inputs[key]
    const error = errors[key]
    const isRequired = tool.jsonSchema.required?.includes(key)

    if (prop.type === 'string' && prop.enum) {
      // Select dropdown for enums
      return (
        <div key={key} className="space-y-2">
          <Label htmlFor={key}>
            {prop.description || key}
            {isRequired && <span className="text-red-500"> *</span>}
          </Label>
          <Select
            id={key}
            value={value || ''}
            onValueChange={(val) => updateInput(key, val)}
          >
            {prop.enum.map((option: string) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </Select>
          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>
      )
    }

    if (prop.type === 'string' && (prop.format === 'textarea' || prop.description?.includes('markdown'))) {
      // Textarea for long text
      return (
        <div key={key} className="space-y-2">
          <Label htmlFor={key}>
            {prop.description || key}
            {isRequired && <span className="text-red-500"> *</span>}
          </Label>
          <Textarea
            id={key}
            value={value || ''}
            onChange={(e) => updateInput(key, e.target.value)}
            placeholder={prop.description}
            rows={4}
          />
          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>
      )
    }

    if (prop.type === 'boolean') {
      // Checkbox for boolean
      return (
        <div key={key} className="flex items-center space-x-2">
          <input
            type="checkbox"
            id={key}
            checked={value || false}
            onChange={(e) => updateInput(key, e.target.checked)}
            className="rounded border-gray-300"
          />
          <Label htmlFor={key}>
            {prop.description || key}
            {isRequired && <span className="text-red-500"> *</span>}
          </Label>
          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>
      )
    }

    if (prop.type === 'number') {
      // Number input
      return (
        <div key={key} className="space-y-2">
          <Label htmlFor={key}>
            {prop.description || key}
            {isRequired && <span className="text-red-500"> *</span>}
          </Label>
          <Input
            id={key}
            type="number"
            value={value || ''}
            onChange={(e) => updateInput(key, Number(e.target.value))}
            placeholder={prop.description}
          />
          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>
      )
    }

    // Default: text input
    return (
      <div key={key} className="space-y-2">
        <Label htmlFor={key}>
          {prop.description || key}
          {isRequired && <span className="text-red-500"> *</span>}
        </Label>
        <Input
          id={key}
          type="text"
          value={value || ''}
          onChange={(e) => updateInput(key, e.target.value)}
          placeholder={prop.description}
        />
        {error && <p className="text-sm text-red-500">{error}</p>}
      </div>
    )
  }

  const schema = tool.jsonSchema
  const properties = schema.properties || {}

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4">
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold">{tool.name}</h3>
          <p className="text-sm text-gray-600">{tool.description}</p>
        </div>

        {Object.keys(properties).map((key) => renderInput(key, properties[key]))}
      </div>

      <div className="flex gap-2 justify-end">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isExecuting}>
          Cancel
        </Button>
        <Button type="submit" disabled={isExecuting}>
          {isExecuting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Executing...
            </>
          ) : (
            'Execute'
          )}
        </Button>
      </div>
    </form>
  )
}

