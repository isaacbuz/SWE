"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import Link from "next/link";
import { useCreateSkill } from "@/lib/hooks/use-skills";

// Simple toast implementation (replace with proper toast library if available)
const toast = {
  success: (message: string) => {
    console.log("Success:", message);
    // In production, use a proper toast library
  },
  error: (message: string) => {
    console.error("Error:", message);
    alert(`Error: ${message}`);
  },
};

const categories = [
  "CODE_GENERATION",
  "TESTING",
  "CODE_REVIEW",
  "DOCUMENTATION",
  "ARCHITECTURE",
];

const visibilityOptions = [
  { value: "public", label: "Public" },
  { value: "private", label: "Private" },
  { value: "unlisted", label: "Unlisted" },
];

const licenseOptions = [
  "MIT",
  "Apache-2.0",
  "GPL-3.0",
  "BSD-3-Clause",
  "Proprietary",
];

type Step = "basic" | "prompt" | "schema" | "settings" | "review";

export default function CreateSkillPage() {
  const router = useRouter();
  const createSkill = useCreateSkill();

  const [currentStep, setCurrentStep] = useState<Step>("basic");
  const [formData, setFormData] = useState({
    // Basic Info
    name: "",
    slug: "",
    description: "",
    detailed_description: "",
    category: "",
    tags: [] as string[],

    // Prompt
    prompt_template: "",

    // Schemas
    input_schema: {} as Record<string, any>,
    output_schema: {} as Record<string, any>,

    // Settings
    visibility: "public",
    license: "MIT",
    pricing_model: "free",
    model_preferences: {} as Record<string, any>,
    validation_rules: [] as any[],
  });

  const [tagInput, setTagInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const steps: { id: Step; label: string }[] = [
    { id: "basic", label: "Basic Info" },
    { id: "prompt", label: "Prompt Template" },
    { id: "schema", label: "Input/Output Schema" },
    { id: "settings", label: "Settings" },
    { id: "review", label: "Review" },
  ];

  const currentStepIndex = steps.findIndex((s) => s.id === currentStep);
  const canGoNext = validateStep(currentStep);
  const canGoPrev = currentStepIndex > 0;

  function validateStep(step: Step): boolean {
    switch (step) {
      case "basic":
        return !!(
          formData.name &&
          formData.slug &&
          formData.description &&
          formData.category
        );
      case "prompt":
        return !!formData.prompt_template;
      case "schema":
        return !!(
          formData.input_schema &&
          Object.keys(formData.input_schema).length > 0 &&
          formData.output_schema &&
          Object.keys(formData.output_schema).length > 0
        );
      case "settings":
        return true; // All optional
      case "review":
        return true;
      default:
        return false;
    }
  }

  function handleNext() {
    if (canGoNext && currentStepIndex < steps.length - 1) {
      setCurrentStep(steps[currentStepIndex + 1].id);
    }
  }

  function handlePrev() {
    if (canGoPrev) {
      setCurrentStep(steps[currentStepIndex - 1].id);
    }
  }

  function addTag() {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({
        ...formData,
        tags: [...formData.tags, tagInput.trim()],
      });
      setTagInput("");
    }
  }

  function removeTag(tag: string) {
    setFormData({
      ...formData,
      tags: formData.tags.filter((t) => t !== tag),
    });
  }

  async function handleSubmit() {
    if (!validateStep("review")) {
      toast.error("Please complete all required fields");
      return;
    }

    setIsSubmitting(true);
    try {
      await createSkill.mutateAsync({
        name: formData.name,
        slug: formData.slug,
        description: formData.description,
        detailed_description: formData.detailed_description || undefined,
        category: formData.category,
        tags: formData.tags,
        prompt_template: formData.prompt_template,
        input_schema: formData.input_schema,
        output_schema: formData.output_schema,
        visibility: formData.visibility,
        license: formData.license,
        pricing_model: formData.pricing_model,
        model_preferences:
          Object.keys(formData.model_preferences).length > 0
            ? formData.model_preferences
            : undefined,
        validation_rules:
          formData.validation_rules.length > 0
            ? formData.validation_rules
            : undefined,
      });

      toast.success("Skill created successfully!");
      router.push(`/skills`);
    } catch (error: any) {
      toast.error(error.message || "Failed to create skill");
    } finally {
      setIsSubmitting(false);
    }
  }

  function generateSlug() {
    if (formData.name) {
      const slug = formData.name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)/g, "");
      setFormData({ ...formData, slug });
    }
  }

  return (
    <div className="container mx-auto py-8 max-w-4xl">
      <div className="mb-6">
        <Link href="/skills">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Marketplace
          </Button>
        </Link>
      </div>

      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Create New Skill</h1>
        <p className="text-muted-foreground">
          Build a reusable AI Skill for the marketplace
        </p>
      </div>

      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex flex-col items-center flex-1">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center border-2 ${
                    index <= currentStepIndex
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-muted border-muted-foreground/20"
                  }`}
                >
                  {index < currentStepIndex ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    <span>{index + 1}</span>
                  )}
                </div>
                <span className="mt-2 text-sm text-muted-foreground">
                  {step.label}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`h-0.5 flex-1 mx-2 ${
                    index < currentStepIndex ? "bg-primary" : "bg-muted"
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Form Content */}
      <div className="bg-card border rounded-lg p-6 mb-6">
        {currentStep === "basic" && (
          <div className="space-y-6">
            <div>
              <Label htmlFor="name">Skill Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => {
                  setFormData({ ...formData, name: e.target.value });
                }}
                placeholder="e.g., TypeScript API Generator"
              />
            </div>

            <div>
              <Label htmlFor="slug">Slug *</Label>
              <div className="flex gap-2">
                <Input
                  id="slug"
                  value={formData.slug}
                  onChange={(e) => {
                    setFormData({ ...formData, slug: e.target.value });
                  }}
                  placeholder="typescript-api-generator"
                />
                <Button type="button" variant="outline" onClick={generateSlug}>
                  Generate
                </Button>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                URL-friendly identifier (auto-generated from name)
              </p>
            </div>

            <div>
              <Label htmlFor="description">Short Description *</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => {
                  setFormData({ ...formData, description: e.target.value });
                }}
                placeholder="A brief description of what this Skill does"
                rows={3}
              />
            </div>

            <div>
              <Label htmlFor="detailed_description">Detailed Description</Label>
              <Textarea
                id="detailed_description"
                value={formData.detailed_description}
                onChange={(e) => {
                  setFormData({
                    ...formData,
                    detailed_description: e.target.value,
                  });
                }}
                placeholder="A comprehensive description with features, use cases, and examples"
                rows={5}
              />
            </div>

            <div>
              <Label htmlFor="category">Category *</Label>
              <Select
                id="category"
                value={formData.category}
                onChange={(e) => {
                  setFormData({ ...formData, category: e.target.value });
                }}
              >
                <option value="">Select a category</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat.replace(/_/g, " ")}
                  </option>
                ))}
              </Select>
            </div>

            <div>
              <Label>Tags</Label>
              <div className="flex gap-2 mb-2">
                <Input
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addTag();
                    }
                  }}
                  placeholder="Add a tag and press Enter"
                />
                <Button type="button" onClick={addTag}>
                  Add
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {formData.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-muted rounded-md text-sm"
                  >
                    {tag}
                    <button
                      type="button"
                      onClick={() => removeTag(tag)}
                      className="hover:text-destructive"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {currentStep === "prompt" && (
          <div className="space-y-4">
            <div>
              <Label htmlFor="prompt_template">Prompt Template *</Label>
              <p className="text-sm text-muted-foreground mb-2">
                Use Jinja2 syntax for variables: {"{{variable_name}}"}
              </p>
              <Textarea
                id="prompt_template"
                value={formData.prompt_template}
                onChange={(e) => {
                  setFormData({ ...formData, prompt_template: e.target.value });
                }}
                placeholder="Generate a {{language}} function that {{task}}..."
                rows={12}
                className="font-mono text-sm"
              />
            </div>
            <div className="bg-muted p-4 rounded-md">
              <p className="text-sm font-semibold mb-2">Template Tips:</p>
              <ul className="text-sm space-y-1 list-disc list-inside">
                <li>Use {"{{variable}}"} for user inputs</li>
                <li>
                  Use {"{% if condition %}...{% endif %}"} for conditionals
                </li>
                <li>Use {"{% for item in list %}...{% endfor %}"} for loops</li>
              </ul>
            </div>
          </div>
        )}

        {currentStep === "schema" && (
          <div className="space-y-6">
            <div>
              <Label htmlFor="input_schema">Input Schema (JSON) *</Label>
              <p className="text-sm text-muted-foreground mb-2">
                Define the JSON Schema for Skill inputs
              </p>
              <Textarea
                id="input_schema"
                value={JSON.stringify(formData.input_schema, null, 2)}
                onChange={(e) => {
                  try {
                    const schema = JSON.parse(e.target.value);
                    setFormData({ ...formData, input_schema: schema });
                  } catch {
                    // Invalid JSON, keep as is
                  }
                }}
                placeholder='{"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}'
                rows={10}
                className="font-mono text-sm"
              />
            </div>

            <div>
              <Label htmlFor="output_schema">Output Schema (JSON) *</Label>
              <p className="text-sm text-muted-foreground mb-2">
                Define the JSON Schema for Skill outputs
              </p>
              <Textarea
                id="output_schema"
                value={JSON.stringify(formData.output_schema, null, 2)}
                onChange={(e) => {
                  try {
                    const schema = JSON.parse(e.target.value);
                    setFormData({ ...formData, output_schema: schema });
                  } catch {
                    // Invalid JSON, keep as is
                  }
                }}
                placeholder='{"type": "object", "properties": {"result": {"type": "string"}}}'
                rows={10}
                className="font-mono text-sm"
              />
            </div>
          </div>
        )}

        {currentStep === "settings" && (
          <div className="space-y-6">
            <div>
              <Label htmlFor="visibility">Visibility</Label>
              <Select
                id="visibility"
                value={formData.visibility}
                onChange={(e) => {
                  setFormData({
                    ...formData,
                    visibility: e.target.value as any,
                  });
                }}
              >
                {visibilityOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </Select>
            </div>

            <div>
              <Label htmlFor="license">License</Label>
              <Select
                id="license"
                value={formData.license}
                onChange={(e) => {
                  setFormData({ ...formData, license: e.target.value });
                }}
              >
                {licenseOptions.map((lic) => (
                  <option key={lic} value={lic}>
                    {lic}
                  </option>
                ))}
              </Select>
            </div>

            <div>
              <Label htmlFor="pricing_model">Pricing Model</Label>
              <Select
                id="pricing_model"
                value={formData.pricing_model}
                onChange={(e) => {
                  setFormData({
                    ...formData,
                    pricing_model: e.target.value as any,
                  });
                }}
              >
                <option value="free">Free</option>
                <option value="paid">Paid</option>
                <option value="freemium">Freemium</option>
              </Select>
            </div>
          </div>
        )}

        {currentStep === "review" && (
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold mb-4">Review Your Skill</h3>
              <div className="space-y-4">
                <div>
                  <Label>Name</Label>
                  <p>{formData.name}</p>
                </div>
                <div>
                  <Label>Slug</Label>
                  <p className="font-mono text-sm">{formData.slug}</p>
                </div>
                <div>
                  <Label>Description</Label>
                  <p>{formData.description}</p>
                </div>
                <div>
                  <Label>Category</Label>
                  <p>{formData.category}</p>
                </div>
                <div>
                  <Label>Tags</Label>
                  <div className="flex flex-wrap gap-2">
                    {formData.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-1 bg-muted rounded-md text-sm"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={handlePrev} disabled={!canGoPrev}>
          Previous
        </Button>

        {currentStepIndex < steps.length - 1 ? (
          <Button onClick={handleNext} disabled={!canGoNext}>
            Next
          </Button>
        ) : (
          <Button onClick={handleSubmit} disabled={isSubmitting || !canGoNext}>
            {isSubmitting ? "Creating..." : "Create Skill"}
          </Button>
        )}
      </div>
    </div>
  );
}
