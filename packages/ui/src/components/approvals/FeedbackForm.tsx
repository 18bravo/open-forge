'use client';

import * as React from 'react';
import { Star, Loader2 } from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import {
  FeedbackForm as FeedbackFormType,
  FeedbackFormField,
  FeedbackType,
  FeedbackCategory,
  SubmitFeedbackRequest,
  getFeedbackTypeLabel,
  getCategoryLabel,
} from '@/types/feedback';

interface FeedbackFormProps {
  form?: FeedbackFormType;
  engagementId?: string;
  sourceType?: string;
  sourceId?: string;
  agentName?: string;
  onSubmit: (data: SubmitFeedbackRequest) => Promise<void>;
  onCancel?: () => void;
  className?: string;
}

export function FeedbackForm({
  form,
  engagementId,
  sourceType,
  sourceId,
  agentName,
  onSubmit,
  onCancel,
  className,
}: FeedbackFormProps) {
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [rating, setRating] = React.useState<number | undefined>();
  const [hoverRating, setHoverRating] = React.useState<number | undefined>();
  const [feedbackType, setFeedbackType] = React.useState<FeedbackType>(
    form?.feedback_type || FeedbackType.RATING
  );
  const [category, setCategory] = React.useState<FeedbackCategory>(
    form?.category || FeedbackCategory.AGENT_OUTPUT
  );
  const [title, setTitle] = React.useState('');
  const [description, setDescription] = React.useState('');
  const [formData, setFormData] = React.useState<Record<string, unknown>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const data: SubmitFeedbackRequest = {
        feedback_type: feedbackType,
        category,
        engagement_id: engagementId,
        rating,
        title: title || undefined,
        description: description || undefined,
        form_data: Object.keys(formData).length > 0 ? formData : undefined,
        source_type: sourceType,
        source_id: sourceId,
        agent_name: agentName,
      };

      await onSubmit(data);
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateFormData = (field: string, value: unknown) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <form onSubmit={handleSubmit} className={cn('space-y-6', className)}>
      {/* Form header */}
      {form ? (
        <div>
          <h3 className="text-lg font-semibold">{form.name}</h3>
          {form.description && (
            <p className="text-sm text-muted-foreground mt-1">{form.description}</p>
          )}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="grid gap-2">
            <Label htmlFor="feedback-type">Feedback Type</Label>
            <Select
              value={feedbackType}
              onValueChange={(v) => setFeedbackType(v as FeedbackType)}
            >
              <SelectTrigger id="feedback-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.values(FeedbackType).map((type) => (
                  <SelectItem key={type} value={type}>
                    {getFeedbackTypeLabel(type)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="category">Category</Label>
            <Select
              value={category}
              onValueChange={(v) => setCategory(v as FeedbackCategory)}
            >
              <SelectTrigger id="category">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.values(FeedbackCategory).map((cat) => (
                  <SelectItem key={cat} value={cat}>
                    {getCategoryLabel(cat)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      )}

      {/* Rating (if enabled or default) */}
      {(form?.include_rating ?? true) && (
        <div className="grid gap-2">
          <Label>Rating</Label>
          <StarRating
            value={rating}
            hoverValue={hoverRating}
            onChange={setRating}
            onHoverChange={setHoverRating}
            max={5}
          />
        </div>
      )}

      {/* Custom form fields */}
      {form?.fields.map((field) => (
        <FormField
          key={field.name}
          field={field}
          value={formData[field.name]}
          onChange={(value) => updateFormData(field.name, value)}
        />
      ))}

      {/* Title */}
      <div className="grid gap-2">
        <Label htmlFor="feedback-title">Title (optional)</Label>
        <Input
          id="feedback-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Brief summary of your feedback"
        />
      </div>

      {/* Comments (if enabled or default) */}
      {(form?.include_comments ?? true) && (
        <div className="grid gap-2">
          <Label htmlFor="feedback-description">
            Comments {feedbackType === FeedbackType.CORRECTION && <span className="text-red-500">*</span>}
          </Label>
          <Textarea
            id="feedback-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Provide additional details..."
            rows={4}
            required={feedbackType === FeedbackType.CORRECTION}
          />
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end gap-2">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Submit Feedback
        </Button>
      </div>
    </form>
  );
}

// Star Rating Component
interface StarRatingProps {
  value?: number;
  hoverValue?: number;
  onChange: (value: number) => void;
  onHoverChange: (value: number | undefined) => void;
  max?: number;
  className?: string;
}

function StarRating({
  value,
  hoverValue,
  onChange,
  onHoverChange,
  max = 5,
  className,
}: StarRatingProps) {
  const displayValue = hoverValue ?? value ?? 0;

  return (
    <div
      className={cn('flex items-center gap-1', className)}
      onMouseLeave={() => onHoverChange(undefined)}
    >
      {Array.from({ length: max }, (_, i) => i + 1).map((star) => (
        <button
          key={star}
          type="button"
          className="p-0.5 transition-transform hover:scale-110"
          onMouseEnter={() => onHoverChange(star)}
          onClick={() => onChange(star)}
        >
          <Star
            className={cn(
              'h-6 w-6 transition-colors',
              star <= displayValue
                ? 'fill-yellow-400 text-yellow-400'
                : 'text-muted-foreground'
            )}
          />
          <span className="sr-only">{star} stars</span>
        </button>
      ))}
      {displayValue > 0 && (
        <span className="ml-2 text-sm text-muted-foreground">
          {displayValue} / {max}
        </span>
      )}
    </div>
  );
}

// Dynamic Form Field Component
interface FormFieldProps {
  field: FeedbackFormField;
  value: unknown;
  onChange: (value: unknown) => void;
}

function FormField({ field, value, onChange }: FormFieldProps) {
  const id = `field-${field.name}`;

  switch (field.field_type) {
    case 'text':
      return (
        <div className="grid gap-2">
          <Label htmlFor={id}>
            {field.label}
            {field.required && <span className="text-red-500">*</span>}
          </Label>
          <Input
            id={id}
            value={(value as string) || ''}
            onChange={(e) => onChange(e.target.value)}
            required={field.required}
          />
        </div>
      );

    case 'textarea':
      return (
        <div className="grid gap-2">
          <Label htmlFor={id}>
            {field.label}
            {field.required && <span className="text-red-500">*</span>}
          </Label>
          <Textarea
            id={id}
            value={(value as string) || ''}
            onChange={(e) => onChange(e.target.value)}
            required={field.required}
            rows={3}
          />
        </div>
      );

    case 'select':
      return (
        <div className="grid gap-2">
          <Label htmlFor={id}>
            {field.label}
            {field.required && <span className="text-red-500">*</span>}
          </Label>
          <Select
            value={(value as string) || ''}
            onValueChange={onChange}
          >
            <SelectTrigger id={id}>
              <SelectValue placeholder="Select..." />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      );

    case 'radio':
      return (
        <div className="grid gap-2">
          <Label>
            {field.label}
            {field.required && <span className="text-red-500">*</span>}
          </Label>
          <div className="space-y-2">
            {field.options?.map((option) => (
              <label
                key={option}
                className="flex items-center gap-2 cursor-pointer"
              >
                <input
                  type="radio"
                  name={field.name}
                  value={option}
                  checked={value === option}
                  onChange={() => onChange(option)}
                  className="h-4 w-4"
                  required={field.required}
                />
                <span className="text-sm">{option}</span>
              </label>
            ))}
          </div>
        </div>
      );

    case 'checkbox':
      return (
        <div className="grid gap-2">
          <Label>
            {field.label}
            {field.required && <span className="text-red-500">*</span>}
          </Label>
          <div className="space-y-2">
            {field.options?.map((option) => {
              const currentValues = (value as string[]) || [];
              const isChecked = currentValues.includes(option);
              return (
                <label
                  key={option}
                  className="flex items-center gap-2 cursor-pointer"
                >
                  <Checkbox
                    checked={isChecked}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        onChange([...currentValues, option]);
                      } else {
                        onChange(currentValues.filter((v) => v !== option));
                      }
                    }}
                  />
                  <span className="text-sm">{option}</span>
                </label>
              );
            })}
          </div>
        </div>
      );

    case 'rating':
      return (
        <div className="grid gap-2">
          <Label>
            {field.label}
            {field.required && <span className="text-red-500">*</span>}
          </Label>
          <StarRating
            value={value as number}
            onChange={onChange as (v: number) => void}
            onHoverChange={() => {}}
          />
        </div>
      );

    default:
      return null;
  }
}

// Quick feedback component for inline use
export function QuickFeedback({
  sourceType,
  sourceId,
  onSubmit,
  className,
}: {
  sourceType: string;
  sourceId: string;
  onSubmit: (data: SubmitFeedbackRequest) => Promise<void>;
  className?: string;
}) {
  const [rating, setRating] = React.useState<number | undefined>();
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [submitted, setSubmitted] = React.useState(false);

  const handleRating = async (value: number) => {
    setRating(value);
    setIsSubmitting(true);

    try {
      await onSubmit({
        feedback_type: FeedbackType.RATING,
        category: FeedbackCategory.AGENT_OUTPUT,
        rating: value,
        source_type: sourceType,
        source_id: sourceId,
      });
      setSubmitted(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className={cn('text-sm text-muted-foreground', className)}>
        Thank you for your feedback!
      </div>
    );
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span className="text-sm text-muted-foreground">Rate this:</span>
      {isSubmitting ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <StarRating
          value={rating}
          onChange={handleRating}
          onHoverChange={() => {}}
          max={5}
        />
      )}
    </div>
  );
}
