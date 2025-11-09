"use client";

import React, { useState } from "react";
import { Send } from "lucide-react";

export function PromptBar() {
  const [prompt, setPrompt] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    console.log("AI Prompt:", prompt);
    // This will be connected to the AI service
    setPrompt("");
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <input
        type="text"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Ask AI..."
        className="w-full rounded-lg border border-border-default bg-surface-secondary px-4 py-2 pr-10 text-sm outline-none transition-colors placeholder:text-ink-tertiary focus:border-brand-primary focus:bg-surface-primary"
      />
      <button
        type="submit"
        disabled={!prompt.trim()}
        className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-ink-tertiary transition-colors hover:text-brand-primary disabled:cursor-not-allowed disabled:opacity-50"
        aria-label="Send"
      >
        <Send className="h-4 w-4" />
      </button>
    </form>
  );
}
