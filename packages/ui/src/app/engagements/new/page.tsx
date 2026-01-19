'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useDataSources } from '@/lib/hooks/use-data-source';
import { useCreateEngagement } from '@/lib/hooks/use-engagement';
import type { EngagementPriority, DataSourceSummary } from '@/lib/api';
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Check,
  Database,
  FileText,
  Loader2,
  Plus,
  RefreshCw,
  Settings,
  X,
} from 'lucide-react';

const priorityOptions: { value: EngagementPriority; label: string; description: string }[] = [
  { value: 'low', label: 'Low', description: 'No immediate deadline' },
  { value: 'medium', label: 'Medium', description: 'Standard priority' },
  { value: 'high', label: 'High', description: 'Time-sensitive work' },
  { value: 'critical', label: 'Critical', description: 'Urgent, needs immediate attention' },
];

interface FormData {
  name: string;
  description: string;
  objective: string;
  priority: EngagementPriority;
  data_sources: string[];
  tags: string[];
  requires_approval: boolean;
}

const STEPS = [
  { id: 'basics', title: 'Basic Info', icon: FileText },
  { id: 'data', title: 'Data Sources', icon: Database },
  { id: 'config', title: 'Configuration', icon: Settings },
  { id: 'review', title: 'Review', icon: Check },
];

export default function NewEngagementPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = React.useState(0);
  const [tagInput, setTagInput] = React.useState('');
  const [submitError, setSubmitError] = React.useState<string | null>(null);

  // Fetch data sources
  const {
    data: dataSourcesData,
    isLoading: isLoadingDataSources,
    isError: isDataSourcesError,
    error: dataSourcesError,
    refetch: refetchDataSources,
  } = useDataSources({ page_size: 100, status: 'active' });

  const dataSources = dataSourcesData?.items ?? [];

  // Create engagement mutation
  const createEngagementMutation = useCreateEngagement();

  const [formData, setFormData] = React.useState<FormData>({
    name: '',
    description: '',
    objective: '',
    priority: 'medium',
    data_sources: [],
    tags: [],
    requires_approval: true,
  });

  const [errors, setErrors] = React.useState<Partial<Record<keyof FormData, string>>>({});

  const updateField = <K extends keyof FormData>(field: K, value: FormData[K]) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
    setSubmitError(null);
  };

  const validateStep = (step: number): boolean => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};

    if (step === 0) {
      if (!formData.name.trim()) {
        newErrors.name = 'Name is required';
      }
      if (!formData.objective.trim()) {
        newErrors.objective = 'Objective is required';
      }
    }

    if (step === 1) {
      if (formData.data_sources.length === 0) {
        newErrors.data_sources = 'At least one data source is required';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const nextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep((prev) => Math.min(prev + 1, STEPS.length - 1));
    }
  };

  const prevStep = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  };

  const addTag = () => {
    const tag = tagInput.trim();
    if (tag && !formData.tags.includes(tag)) {
      updateField('tags', [...formData.tags, tag]);
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    updateField('tags', formData.tags.filter((t) => t !== tag));
  };

  const toggleDataSource = (id: string) => {
    const newSources = formData.data_sources.includes(id)
      ? formData.data_sources.filter((s) => s !== id)
      : [...formData.data_sources, id];
    updateField('data_sources', newSources);
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;

    setSubmitError(null);

    try {
      await createEngagementMutation.mutateAsync({
        name: formData.name,
        description: formData.description || undefined,
        objective: formData.objective,
        priority: formData.priority,
        data_sources: formData.data_sources.map((id) => {
          const source = dataSources.find((s) => s.id === id);
          return {
            source_id: id,
            source_type: source?.source_type || '',
            access_mode: 'read',
          };
        }),
        tags: formData.tags.length > 0 ? formData.tags : undefined,
        requires_approval: formData.requires_approval,
      });

      router.push('/engagements');
    } catch (error) {
      console.error('Failed to create engagement:', error);
      setSubmitError(
        error instanceof Error ? error.message : 'Failed to create engagement. Please try again.'
      );
    }
  };

  return (
    <div className="container max-w-4xl py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/engagements">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">New Engagement</h1>
          <p className="text-muted-foreground">
            Create a new data engagement
          </p>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-between">
        {STEPS.map((step, index) => {
          const Icon = step.icon;
          const isActive = index === currentStep;
          const isCompleted = index < currentStep;

          return (
            <React.Fragment key={step.id}>
              <button
                onClick={() => index < currentStep && setCurrentStep(index)}
                disabled={index > currentStep}
                className={`flex items-center gap-2 ${
                  index <= currentStep ? 'cursor-pointer' : 'cursor-not-allowed'
                }`}
              >
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full border-2 transition-colors ${
                    isCompleted
                      ? 'bg-primary border-primary text-primary-foreground'
                      : isActive
                      ? 'border-primary text-primary'
                      : 'border-muted text-muted-foreground'
                  }`}
                >
                  {isCompleted ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    <Icon className="h-5 w-5" />
                  )}
                </div>
                <span
                  className={`hidden sm:block text-sm font-medium ${
                    isActive ? 'text-foreground' : 'text-muted-foreground'
                  }`}
                >
                  {step.title}
                </span>
              </button>
              {index < STEPS.length - 1 && (
                <div
                  className={`flex-1 h-0.5 mx-4 ${
                    index < currentStep ? 'bg-primary' : 'bg-muted'
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Form Content */}
      <Card>
        <CardContent className="pt-6">
          {currentStep === 0 && (
            <div className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="name">
                  Engagement Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="name"
                  placeholder="e.g., Customer Analytics Pipeline"
                  value={formData.name}
                  onChange={(e) => updateField('name', e.target.value)}
                  className={errors.name ? 'border-destructive' : ''}
                />
                {errors.name && (
                  <p className="text-sm text-destructive">{errors.name}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <textarea
                  id="description"
                  placeholder="Describe the purpose of this engagement..."
                  value={formData.description}
                  onChange={(e) => updateField('description', e.target.value)}
                  className="w-full min-h-[100px] px-3 py-2 rounded-md border bg-background text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="objective">
                  Objective <span className="text-destructive">*</span>
                </Label>
                <textarea
                  id="objective"
                  placeholder="What is the main goal of this engagement?"
                  value={formData.objective}
                  onChange={(e) => updateField('objective', e.target.value)}
                  className={`w-full min-h-[80px] px-3 py-2 rounded-md border bg-background text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring ${
                    errors.objective ? 'border-destructive' : ''
                  }`}
                />
                {errors.objective && (
                  <p className="text-sm text-destructive">{errors.objective}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label>Priority</Label>
                <div className="grid gap-3 sm:grid-cols-2">
                  {priorityOptions.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => updateField('priority', option.value)}
                      className={`flex flex-col items-start p-3 rounded-lg border text-left transition-colors ${
                        formData.priority === option.value
                          ? 'border-primary bg-primary/5'
                          : 'border-muted hover:border-muted-foreground/50'
                      }`}
                    >
                      <span className="font-medium capitalize">{option.label}</span>
                      <span className="text-xs text-muted-foreground">
                        {option.description}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium">Select Data Sources</h3>
                <p className="text-sm text-muted-foreground">
                  Choose the data sources to use in this engagement
                </p>
              </div>

              {errors.data_sources && (
                <p className="text-sm text-destructive">{errors.data_sources}</p>
              )}

              {isLoadingDataSources ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mb-4" />
                  <p className="text-sm text-muted-foreground">Loading data sources...</p>
                </div>
              ) : isDataSourcesError ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <AlertCircle className="h-8 w-8 text-destructive mb-4" />
                  <h3 className="text-lg font-medium">Failed to load data sources</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    {dataSourcesError instanceof Error
                      ? dataSourcesError.message
                      : 'An unexpected error occurred'}
                  </p>
                  <Button onClick={() => refetchDataSources()} variant="outline">
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Retry
                  </Button>
                </div>
              ) : dataSources.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Database className="h-8 w-8 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium">No data sources available</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Create a data source first to use in this engagement.
                  </p>
                  <Button asChild>
                    <Link href="/data-sources/new">
                      <Plus className="mr-2 h-4 w-4" />
                      Add Data Source
                    </Link>
                  </Button>
                </div>
              ) : (
                <div className="grid gap-3">
                  {dataSources.map((source) => {
                    const isSelected = formData.data_sources.includes(source.id);
                    return (
                      <button
                        key={source.id}
                        type="button"
                        onClick={() => toggleDataSource(source.id)}
                        className={`flex items-center justify-between p-4 rounded-lg border text-left transition-colors ${
                          isSelected
                            ? 'border-primary bg-primary/5'
                            : 'border-muted hover:border-muted-foreground/50'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <Database
                            className={`h-5 w-5 ${
                              isSelected ? 'text-primary' : 'text-muted-foreground'
                            }`}
                          />
                          <div>
                            <p className="font-medium">{source.name}</p>
                            <p className="text-sm text-muted-foreground capitalize">
                              {source.source_type}
                            </p>
                          </div>
                        </div>
                        <div
                          className={`h-5 w-5 rounded-full border-2 flex items-center justify-center ${
                            isSelected
                              ? 'border-primary bg-primary'
                              : 'border-muted-foreground'
                          }`}
                        >
                          {isSelected && <Check className="h-3 w-3 text-primary-foreground" />}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}

              <Button variant="outline" asChild>
                <Link href="/data-sources/new">
                  <Plus className="mr-2 h-4 w-4" />
                  Add New Data Source
                </Link>
              </Button>
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="tags">Tags</Label>
                <div className="flex gap-2">
                  <Input
                    id="tags"
                    placeholder="Add a tag..."
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addTag();
                      }
                    }}
                  />
                  <Button type="button" variant="outline" onClick={addTag}>
                    Add
                  </Button>
                </div>
                {formData.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {formData.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-secondary text-secondary-foreground text-sm"
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
                )}
              </div>

              <div className="space-y-3">
                <Label>Approval Settings</Label>
                <button
                  type="button"
                  onClick={() => updateField('requires_approval', !formData.requires_approval)}
                  className={`flex items-center justify-between w-full p-4 rounded-lg border text-left transition-colors ${
                    formData.requires_approval
                      ? 'border-primary bg-primary/5'
                      : 'border-muted'
                  }`}
                >
                  <div>
                    <p className="font-medium">Require Approval</p>
                    <p className="text-sm text-muted-foreground">
                      Engagement must be approved before execution
                    </p>
                  </div>
                  <div
                    className={`h-5 w-5 rounded-full border-2 flex items-center justify-center ${
                      formData.requires_approval
                        ? 'border-primary bg-primary'
                        : 'border-muted-foreground'
                    }`}
                  >
                    {formData.requires_approval && (
                      <Check className="h-3 w-3 text-primary-foreground" />
                    )}
                  </div>
                </button>
              </div>
            </div>
          )}

          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium">Review & Create</h3>
                <p className="text-sm text-muted-foreground">
                  Review your engagement details before creating
                </p>
              </div>

              {submitError && (
                <div className="flex items-center gap-2 p-4 rounded-lg bg-destructive/10 text-destructive">
                  <AlertCircle className="h-5 w-5 flex-shrink-0" />
                  <p className="text-sm">{submitError}</p>
                </div>
              )}

              <div className="space-y-4">
                <div className="grid gap-4 p-4 rounded-lg bg-muted/50">
                  <div className="grid gap-1">
                    <span className="text-sm text-muted-foreground">Name</span>
                    <span className="font-medium">{formData.name}</span>
                  </div>

                  {formData.description && (
                    <div className="grid gap-1">
                      <span className="text-sm text-muted-foreground">Description</span>
                      <span>{formData.description}</span>
                    </div>
                  )}

                  <div className="grid gap-1">
                    <span className="text-sm text-muted-foreground">Objective</span>
                    <span>{formData.objective}</span>
                  </div>

                  <div className="grid gap-1">
                    <span className="text-sm text-muted-foreground">Priority</span>
                    <span className="capitalize">{formData.priority}</span>
                  </div>

                  <div className="grid gap-1">
                    <span className="text-sm text-muted-foreground">Data Sources</span>
                    <div className="flex flex-wrap gap-2">
                      {formData.data_sources.map((id) => {
                        const source = dataSources.find((s) => s.id === id);
                        return (
                          <span
                            key={id}
                            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-secondary text-sm"
                          >
                            <Database className="h-3 w-3" />
                            {source?.name || id}
                          </span>
                        );
                      })}
                    </div>
                  </div>

                  {formData.tags.length > 0 && (
                    <div className="grid gap-1">
                      <span className="text-sm text-muted-foreground">Tags</span>
                      <div className="flex flex-wrap gap-1">
                        {formData.tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-0.5 rounded-full bg-secondary text-sm"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="grid gap-1">
                    <span className="text-sm text-muted-foreground">Requires Approval</span>
                    <span>{formData.requires_approval ? 'Yes' : 'No'}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={prevStep}
          disabled={currentStep === 0}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Previous
        </Button>

        {currentStep < STEPS.length - 1 ? (
          <Button onClick={nextStep}>
            Next
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        ) : (
          <Button
            onClick={handleSubmit}
            disabled={createEngagementMutation.isPending}
          >
            {createEngagementMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Check className="mr-2 h-4 w-4" />
                Create Engagement
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}
