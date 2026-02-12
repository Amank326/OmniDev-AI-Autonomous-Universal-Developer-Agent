'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useProjectWebSocket } from '@/hooks/useWebSocket';
import { useAuthStore } from '@/store/auth';
import { CheckCircle, Circle, AlertCircle, Trash2, Edit2 } from 'lucide-react';

interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed';
  priority: 'low' | 'medium' | 'high';
  project_id: string;
  created_at: string;
  updated_at: string;
}

interface RealtimeTasksProps {
  projectId: string;
  tasks: Task[];
  onTasksChange: (tasks: Task[]) => void;
  onDeleteTask: (taskId: string) => Promise<void>;
}

export const RealtimeTasks: React.FC<RealtimeTasksProps> = ({
  projectId,
  tasks: initialTasks,
  onTasksChange,
  onDeleteTask,
}) => {
  const { user } = useAuthStore();
  const [tasks, setTasks] = useState<Task[]>(initialTasks);
  const [activeUsers, setActiveUsers] = useState<string[]>([]);
  const [deleting, setDeleting] = useState<string | null>(null);

  const { isConnected, send } = useProjectWebSocket(
    projectId,
    user?.id || '',
    {
      onTaskCreated: (task) => {
        console.log('Task created:', task);
        setTasks((prev) => {
          const exists = prev.find((t) => t.id === task.id);
          if (exists) return prev;
          return [task, ...prev];
        });
        onTasksChange([...tasks, task]);
      },
      onTaskUpdated: (task) => {
        console.log('Task updated:', task);
        setTasks((prev) =>
          prev.map((t) => (t.id === task.id ? task : t))
        );
        onTasksChange(
          tasks.map((t) => (t.id === task.id ? task : t))
        );
      },
      onTaskDeleted: (taskId) => {
        console.log('Task deleted:', taskId);
        setTasks((prev) => prev.filter((t) => t.id !== taskId));
        onTasksChange(tasks.filter((t) => t.id !== taskId));
      },
      onTaskStatusUpdated: (task) => {
        console.log('Task status updated:', task);
        setTasks((prev) =>
          prev.map((t) => (t.id === task.id ? task : t))
        );
        onTasksChange(
          tasks.map((t) => (t.id === task.id ? task : t))
        );
      },
      onUserJoined: (users) => {
        console.log('Users in room:', users);
        setActiveUsers(users);
      },
    }
  );

  const getStatusIcon = (status: Task['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'in_progress':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      default:
        return <Circle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getPriorityColor = (priority: Task['priority']) => {
    switch (priority) {
      case 'high':
        return 'bg-red-900/20 text-red-400 border-red-700';
      case 'medium':
        return 'bg-yellow-900/20 text-yellow-400 border-yellow-700';
      default:
        return 'bg-blue-900/20 text-blue-400 border-blue-700';
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    setDeleting(taskId);
    try {
      await onDeleteTask(taskId);
    } catch (error) {
      console.error('Failed to delete task:', error);
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="space-y-4">
      {/* Connection Status & Active Users */}
      <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg border border-slate-600">
        <div className="flex items-center gap-3">
          <div
            className={`w-3 h-3 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-sm text-slate-300">
            {isConnected ? 'Real-time connected' : 'Connecting...'}
          </span>
        </div>
        <div className="text-xs text-slate-400">
          {activeUsers.length} user{activeUsers.length !== 1 ? 's' : ''} viewing
        </div>
      </div>

      {/* Tasks List */}
      <div className="space-y-2">
        {tasks.length === 0 ? (
          <div className="text-center py-8 text-slate-400">
            No tasks yet. Create one to get started.
          </div>
        ) : (
          tasks.map((task) => (
            <div
              key={task.id}
              className="p-4 bg-slate-700/50 rounded-lg border border-slate-600 hover:border-slate-500 transition group"
            >
              <div className="flex items-start gap-4">
                {/* Status Icon */}
                <div className="mt-1">{getStatusIcon(task.status)}</div>

                {/* Task Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <h4 className="font-medium text-slate-100 truncate">
                        {task.title}
                      </h4>
                      <p className="text-sm text-slate-400 line-clamp-2 mt-1">
                        {task.description}
                      </p>
                    </div>
                    <span
                      className={`px-2 py-1 text-xs rounded font-medium border whitespace-nowrap ${getPriorityColor(
                        task.priority
                      )}`}
                    >
                      {task.priority}
                    </span>
                  </div>

                  {/* Metadata */}
                  <div className="flex items-center gap-2 mt-3 text-xs text-slate-500">
                    <span>
                      Updated{' '}
                      {new Date(task.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition">
                  <button
                    className="p-1.5 rounded hover:bg-slate-600 text-slate-400 hover:text-slate-200 transition"
                    title="Edit task"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteTask(task.id)}
                    disabled={deleting === task.id}
                    className="p-1.5 rounded hover:bg-red-900/30 text-slate-400 hover:text-red-400 transition disabled:opacity-50"
                    title="Delete task"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Real-time Status */}
      {isConnected && (
        <div className="text-xs text-slate-500 text-center">
          ✓ Updates appear automatically as they happen
        </div>
      )}
    </div>
  );
};
