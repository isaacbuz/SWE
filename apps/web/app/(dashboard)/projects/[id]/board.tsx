"use client";

import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/board/kanban-column";
import { IssueCard } from "@/components/board/issue-card";
import { mockIssues } from "@/lib/api/mock-data";
import { useState } from "react";

interface BoardViewProps {
  projectId: string;
}

export default function BoardView({ projectId }: BoardViewProps) {
  const [issues, setIssues] = useState(
    mockIssues.filter((i) => i.projectId === projectId),
  );
  const [activeId, setActiveId] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
  );

  const columns = {
    todo: issues.filter((i) => i.status === "todo"),
    in_progress: issues.filter((i) => i.status === "in_progress"),
    review: issues.filter((i) => i.status === "review"),
    done: issues.filter((i) => i.status === "done"),
  };

  const handleDragStart = (event: { active: { id: string } }) => {
    setActiveId(event.active.id);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over) return;

    const activeIssue = issues.find((i) => i.id === active.id);
    if (!activeIssue) return;

    // Determine new status based on drop target
    let newStatus = activeIssue.status;
    if (over.id === "todo" || columns.todo.some((i) => i.id === over.id)) {
      newStatus = "todo";
    } else if (
      over.id === "in_progress" ||
      columns.in_progress.some((i) => i.id === over.id)
    ) {
      newStatus = "in_progress";
    } else if (
      over.id === "review" ||
      columns.review.some((i) => i.id === over.id)
    ) {
      newStatus = "review";
    } else if (
      over.id === "done" ||
      columns.done.some((i) => i.id === over.id)
    ) {
      newStatus = "done";
    }

    setIssues((prevIssues) =>
      prevIssues.map((issue) =>
        issue.id === active.id ? { ...issue, status: newStatus as any } : issue,
      ),
    );

    setActiveId(null);
  };

  const activeIssue = activeId ? issues.find((i) => i.id === activeId) : null;

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="flex gap-4 overflow-x-auto pb-4">
        <KanbanColumn
          id="todo"
          title="To Do"
          count={columns.todo.length}
          items={columns.todo.map((i) => i.id)}
        >
          {columns.todo.map((issue) => (
            <IssueCard
              key={issue.id}
              id={issue.id}
              number={issue.number}
              title={issue.title}
              assignee={issue.assignee}
              priority={issue.priority}
              labels={issue.labels}
            />
          ))}
        </KanbanColumn>

        <KanbanColumn
          id="in_progress"
          title="In Progress"
          count={columns.in_progress.length}
          items={columns.in_progress.map((i) => i.id)}
        >
          {columns.in_progress.map((issue) => (
            <IssueCard
              key={issue.id}
              id={issue.id}
              number={issue.number}
              title={issue.title}
              assignee={issue.assignee}
              priority={issue.priority}
              labels={issue.labels}
            />
          ))}
        </KanbanColumn>

        <KanbanColumn
          id="review"
          title="Review"
          count={columns.review.length}
          items={columns.review.map((i) => i.id)}
        >
          {columns.review.map((issue) => (
            <IssueCard
              key={issue.id}
              id={issue.id}
              number={issue.number}
              title={issue.title}
              assignee={issue.assignee}
              priority={issue.priority}
              labels={issue.labels}
            />
          ))}
        </KanbanColumn>

        <KanbanColumn
          id="done"
          title="Done"
          count={columns.done.length}
          items={columns.done.map((i) => i.id)}
        >
          {columns.done.map((issue) => (
            <IssueCard
              key={issue.id}
              id={issue.id}
              number={issue.number}
              title={issue.title}
              assignee={issue.assignee}
              priority={issue.priority}
              labels={issue.labels}
            />
          ))}
        </KanbanColumn>
      </div>

      <DragOverlay>
        {activeIssue && (
          <IssueCard
            id={activeIssue.id}
            number={activeIssue.number}
            title={activeIssue.title}
            assignee={activeIssue.assignee}
            priority={activeIssue.priority}
            labels={activeIssue.labels}
          />
        )}
      </DragOverlay>
    </DndContext>
  );
}
