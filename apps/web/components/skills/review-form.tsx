'use client'

import { useState } from 'react'
import { Star } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { useCreateSkillReview } from '@/lib/hooks/use-skills'

interface ReviewFormProps {
  skillId: string
  onSuccess?: () => void
}

export function ReviewForm({ skillId, onSuccess }: ReviewFormProps) {
  const [rating, setRating] = useState(0)
  const [hoverRating, setHoverRating] = useState(0)
  const [title, setTitle] = useState('')
  const [reviewText, setReviewText] = useState('')
  
  const createReview = useCreateSkillReview()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (rating === 0) {
      alert('Please select a rating')
      return
    }

    try {
      await createReview.mutateAsync({
        skillId,
        review: {
          rating,
          title: title.trim() || undefined,
          review_text: reviewText.trim() || undefined,
        },
      })
      
      // Reset form
      setRating(0)
      setTitle('')
      setReviewText('')
      
      if (onSuccess) {
        onSuccess()
      }
    } catch (error: any) {
      alert(error.message || 'Failed to submit review')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label>Rating *</Label>
        <div className="flex items-center gap-1 mt-2">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              onClick={() => setRating(star)}
              onMouseEnter={() => setHoverRating(star)}
              onMouseLeave={() => setHoverRating(0)}
              className="focus:outline-none"
            >
              <Star
                className={`h-6 w-6 ${
                  star <= (hoverRating || rating)
                    ? 'fill-yellow-400 text-yellow-400'
                    : 'text-gray-300'
                } transition-colors`}
              />
            </button>
          ))}
          {rating > 0 && (
            <span className="ml-2 text-sm text-muted-foreground">
              {rating} {rating === 1 ? 'star' : 'stars'}
            </span>
          )}
        </div>
      </div>

      <div>
        <Label htmlFor="review-title">Title (optional)</Label>
        <Input
          id="review-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Brief summary of your review"
          maxLength={255}
        />
      </div>

      <div>
        <Label htmlFor="review-text">Review (optional)</Label>
        <Textarea
          id="review-text"
          value={reviewText}
          onChange={(e) => setReviewText(e.target.value)}
          placeholder="Share your experience with this Skill..."
          rows={5}
        />
      </div>

      <div className="flex justify-end gap-2">
        <Button
          type="submit"
          disabled={createReview.isPending || rating === 0}
        >
          {createReview.isPending ? 'Submitting...' : 'Submit Review'}
        </Button>
      </div>
    </form>
  )
}

