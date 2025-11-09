'use client'

import { Star } from 'lucide-react'
import { SkillReview } from '@/lib/api/types'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface ReviewListProps {
  reviews: SkillReview[]
  skillId: string
}

export function ReviewList({ reviews }: ReviewListProps) {
  if (reviews.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>No reviews yet. Be the first to review this Skill!</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {reviews.map((review) => (
        <Card key={review.id} className="p-6">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="flex items-center">
                {[1, 2, 3, 4, 5].map((star) => (
                  <Star
                    key={star}
                    className={`h-4 w-4 ${
                      star <= review.rating
                        ? 'fill-yellow-400 text-yellow-400'
                        : 'text-gray-300'
                    }`}
                  />
                ))}
              </div>
              <span className="text-sm font-medium">{review.rating}/5</span>
            </div>
            <span className="text-sm text-muted-foreground">
              {new Date(review.created_at).toLocaleDateString()}
            </span>
          </div>

          {review.title && (
            <h4 className="font-semibold mb-2">{review.title}</h4>
          )}

          {review.review_text && (
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">
              {review.review_text}
            </p>
          )}

          {!review.title && !review.review_text && (
            <p className="text-sm text-muted-foreground italic">
              Rating only
            </p>
          )}
        </Card>
      ))}
    </div>
  )
}

