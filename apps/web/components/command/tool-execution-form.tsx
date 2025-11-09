'use client'

import React, { useState } from 'react'
import { X, Play, Loader2 } from 'lucide-react'
import { ToolSpec } from '@/lib/hooks/use-tool-registry'
import { cn } from '@/lib/utils/cn'

interface ToolExecutionFormProps {
  tool: ToolSpec
  onExecute: (toolName: string, args: Record<string, any>) => Promise<void>
  onClose: () => void
}

export function ToolExecutionForm({ tool, onExecute, onClose }: ToolExecutionFormProps) {
  const [formData, setFormData] = useState<Record<string, any>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [executing, setExecuting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate required fields
    const newErrors: Record<string, string> = {}
    tool.required?.forEach(field => {
      if (!formData[field] || (Array.isArray(formData[field]) && formData[field].length === 0)) {
        newErrors[field] = 'This field is required'
      }
    })

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    setExecuting(true)
    try {
      await onExecute(tool.name, formData)
      onClose()
    } catch (error) {
      console.error('Tool execution failed:', error)
      // Show error to user
    } finally {
      setExecuting(false)
    }
  }

  const renderField = (fieldName: string, fieldSchema: any) => {
    const isRequired = tool.required?.includes(fieldName)
    const value = formData[fieldName] || ''
    const error = errors[fieldName]

    if (fieldSchema.type === 'array' && fieldSchema.items?.type === 'object') {
      // Handle array of objects (e.g., tasks array)
      return (
        <div key={fieldName} className="space-y-2">
          <label className="block text-sm font-medium text-ink-primary">
            {fieldName} {isRequired && <span className="text-red-500">*</span>}
          </label>
          <div className="space-y-2">
            {(formData[fieldName] || []).map((item: any, index: number) => (
              <div key={index} className="border border-border-subtle rounded-lg p-3 space-y-2">
                {Object.keys(fieldSchema.items.properties || {}).map(subField => (
                  <div key={subField}>
                    <input
                      type="text"
                      placeholder={subField}
                      value={item[subField] || ''}
                      onChange={(e) => {
                        const newArray = [...(formData[fieldName] || [])]
                        newArray[index] = { ...newArray[index], [subField]: e.target.value }
                        setFormData({ ...formData, [fieldName]: newArray })
                      }}
                      className="w-full px-3 py-2 border border-border-subtle rounded-md text-sm"
                    />
                  </div>
                ))}
              </div>
            ))}
            <button
              type="button"
              onClick={() => {
                setFormData({
                  ...formData,
                  [fieldName]: [...(formData[fieldName] || []), {}],
                })
              }}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              + Add {fieldName.slice(0, -1)}
            </button>
          </div>
        </div>
      )
    }

    if (fieldSchema.type === 'array' && fieldSchema.items?.type === 'string') {
      // Handle string array (e.g., labels)
      return (
        <div key={fieldName} className="space-y-2">
          <label className="block text-sm font-medium text-ink-primary">
            {fieldName} {isRequired && <span className="text-red-500">*</span>}
          </label>
          <input
            type="text"
            placeholder="Comma-separated values"
            value={Array.isArray(formData[fieldName]) ? formData[fieldName].join(', ') : value}
            onChange={(e) => {
              const values = e.target.value.split(',').map(v => v.trim()).filter(Boolean)
              setFormData({ ...formData, [fieldName]: values })
            }}
            className={cn(
              "w-full px-3 py-2 border rounded-md text-sm",
              error ? "border-red-500" : "border-border-subtle"
            )}
          />
          {error && <p className="text-xs text-red-500">{error}</p>}
        </div>
      )
    }

    // Handle string/number fields
    return (
      <div key={fieldName} className="space-y-2">
        <label className="block text-sm font-medium text-ink-primary">
          {fieldName} {isRequired && <span className="text-red-500">*</span>}
        </label>
        {fieldSchema.type === 'string' && fieldSchema.description?.includes('body') ? (
          <textarea
            placeholder={fieldSchema.description || fieldName}
            value={value}
            onChange={(e) => setFormData({ ...formData, [fieldName]: e.target.value })}
            className={cn(
              "w-full px-3 py-2 border rounded-md text-sm min-h-[100px]",
              error ? "border-red-500" : "border-border-subtle"
            )}
          />
        ) : (
          <input
            type={fieldSchema.type === 'number' ? 'number' : 'text'}
            placeholder={fieldSchema.description || fieldName}
            value={value}
            onChange={(e) => {
              const newValue = fieldSchema.type === 'number' 
                ? parseFloat(e.target.value) || 0 
                : e.target.value
              setFormData({ ...formData, [fieldName]: newValue })
            }}
            className={cn(
              "w-full px-3 py-2 border rounded-md text-sm",
              error ? "border-red-500" : "border-border-subtle"
            )}
          />
        )}
        {error && <p className="text-xs text-red-500">{error}</p>}
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-2xl bg-white rounded-xl shadow-lg">
        <div className="flex items-center justify-between border-b border-border-subtle px-6 py-4">
          <h2 className="text-lg font-semibold text-ink-primary">{tool.name}</h2>
          <button
            onClick={onClose}
            className="text-ink-tertiary hover:text-ink-primary"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <p className="text-sm text-ink-secondary mb-4">{tool.description}</p>

          {Object.entries(tool.parameters || {}).map(([fieldName, fieldSchema]) =>
            renderField(fieldName, fieldSchema)
          )}

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-border-subtle">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-ink-secondary hover:text-ink-primary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={executing}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {executing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Executing...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Execute
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

