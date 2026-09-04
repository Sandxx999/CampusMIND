import React, { useState } from 'react';
import axios from 'axios';

export default function FeedbackButtons({ queryId }) {
  const [feedbackState, setFeedbackState] = useState(null); // 'positive' | 'negative' | null
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFeedback = async (isPositive) => {
    if (feedbackState !== null || isSubmitting) return;
    setIsSubmitting(true);
    try {
      const token = localStorage.getItem('campusmind_token');
      await axios.post(
        'http://localhost:8000/api/chat/feedback',
        { query_id: queryId, is_positive: isPositive },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setFeedbackState(isPositive ? 'positive' : 'negative');
    } catch (err) {
      console.error('Feedback error:', err);
      setFeedbackState(isPositive ? 'positive' : 'negative');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (feedbackState !== null) {
    return (
      <div className="flex items-center gap-1.5 text-xs font-sans text-[#8FD9A8] font-medium bg-[#8FD9A8]/10 border border-[#8FD9A8]/30 px-2.5 py-1 rounded">
        <span>✅</span>
        <span>Feedback submitted</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => handleFeedback(true)}
        disabled={isSubmitting}
        className="text-xs font-sans text-[#FFF8F0]/90 hover:text-[#FFF8F0] bg-white/10 hover:bg-white/20 border border-white/20 px-2.5 py-1 rounded transition-colors"
      >
        This answered it
      </button>
      <button
        onClick={() => handleFeedback(false)}
        disabled={isSubmitting}
        className="text-xs font-sans text-[#FFF8F0]/70 hover:text-red-300 bg-black/20 hover:bg-red-950/40 border border-white/15 px-2.5 py-1 rounded transition-colors"
      >
        Not quite
      </button>
    </div>
  );
}
