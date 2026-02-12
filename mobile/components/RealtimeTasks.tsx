import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  FlatList,
} from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useProjectWebSocket } from '@/hooks/useWebSocket';
import { useAuthStore } from '@/store/auth';

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
  initialTasks: Task[];
  onDeleteTask: (taskId: string) => Promise<void>;
}

export const RealtimeTasks: React.FC<RealtimeTasksProps> = ({
  projectId,
  initialTasks,
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
        setTasks((prev) => {
          const exists = prev.find((t) => t.id === task.id);
          if (exists) return prev;
          return [task, ...prev];
        });
      },
      onTaskUpdated: (task) => {
        setTasks((prev) =>
          prev.map((t) => (t.id === task.id ? task : t))
        );
      },
      onTaskDeleted: (taskId) => {
        setTasks((prev) => prev.filter((t) => t.id !== taskId));
      },
      onTaskStatusUpdated: (task) => {
        setTasks((prev) =>
          prev.map((t) => (t.id === task.id ? task : t))
        );
      },
      onUserJoined: (users) => {
        setActiveUsers(users);
      },
    }
  );

  const getStatusIcon = (status: Task['status']) => {
    switch (status) {
      case 'completed':
        return (
          <MaterialCommunityIcons
            name="check-circle"
            size={20}
            color="#10b981"
          />
        );
      case 'in_progress':
        return (
          <MaterialCommunityIcons
            name="alert-circle"
            size={20}
            color="#f59e0b"
          />
        );
      default:
        return (
          <MaterialCommunityIcons
            name="circle-outline"
            size={20}
            color="#6b7280"
          />
        );
    }
  };

  const getPriorityColor = (priority: Task['priority']) => {
    switch (priority) {
      case 'high':
        return '#ef4444';
      case 'medium':
        return '#f59e0b';
      default:
        return '#3b82f6';
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

  const renderTask = ({ item: task }: { item: Task }) => (
    <View style={styles.taskCard}>
      <View style={styles.taskContent}>
        <View style={styles.taskHeader}>
          <View style={{ marginRight: 12 }}>
            {getStatusIcon(task.status)}
          </View>
          <View style={styles.taskInfo}>
            <Text style={styles.taskTitle}>{task.title}</Text>
            <Text style={styles.taskDescription} numberOfLines={2}>
              {task.description}
            </Text>
          </View>
          <View
            style={[
              styles.priorityBadge,
              { backgroundColor: getPriorityColor(task.priority) + '20' },
            ]}
          >
            <Text
              style={[
                styles.priorityText,
                { color: getPriorityColor(task.priority) },
              ]}
            >
              {task.priority}
            </Text>
          </View>
        </View>
        <Text style={styles.taskDate}>
          Updated {new Date(task.updated_at).toLocaleDateString()}
        </Text>
      </View>
      <TouchableOpacity
        onPress={() => handleDeleteTask(task.id)}
        disabled={deleting === task.id}
      >
        {deleting === task.id ? (
          <ActivityIndicator color="#6b7280" size="small" />
        ) : (
          <MaterialCommunityIcons name="trash-can" size={20} color="#ef4444" />
        )}
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Connection Status */}
      <View
        style={[
          styles.statusBar,
          {
            backgroundColor: isConnected ? '#065f4620' : '#dc262620',
          },
        ]}
      >
        <View
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <View
            style={[
              styles.statusDot,
              {
                backgroundColor: isConnected ? '#10b981' : '#ef4444',
              },
            ]}
          />
          <Text style={styles.statusText}>
            {isConnected ? 'Real-time connected' : 'Connecting...'}
          </Text>
        </View>
        <Text style={styles.userCount}>
          {activeUsers.length} user{activeUsers.length !== 1 ? 's' : ''}
        </Text>
      </View>

      {/* Tasks List */}
      {tasks.length === 0 ? (
        <View style={styles.emptyState}>
          <MaterialCommunityIcons
            name="inbox-outline"
            size={48}
            color="#6b7280"
          />
          <Text style={styles.emptyText}>No tasks yet</Text>
          <Text style={styles.emptySubtext}>Create one to get started</Text>
        </View>
      ) : (
        <FlatList
          data={tasks}
          renderItem={renderTask}
          keyExtractor={(item) => item.id}
          scrollEnabled={false}
          ItemSeparatorComponent={() => <View style={{ height: 8 }} />}
        />
      )}

      {/* Real-time Status */}
      {isConnected && (
        <Text style={styles.realtimeHint}>
          ✓ Updates appear automatically as they happen
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    gap: 16,
  },
  statusBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#374151',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusText: {
    color: '#e5e7eb',
    fontSize: 12,
    fontWeight: '500',
  },
  userCount: {
    color: '#9ca3af',
    fontSize: 12,
  },
  taskCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#1f2937',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#374151',
  },
  taskContent: {
    flex: 1,
    marginRight: 12,
  },
  taskHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  taskInfo: {
    flex: 1,
  },
  taskTitle: {
    color: '#f3f4f6',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  taskDescription: {
    color: '#9ca3af',
    fontSize: 12,
    lineHeight: 16,
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  priorityText: {
    fontSize: 11,
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  taskDate: {
    color: '#6b7280',
    fontSize: 11,
    marginTop: 8,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    color: '#e5e7eb',
    fontSize: 16,
    fontWeight: '600',
    marginTop: 12,
  },
  emptySubtext: {
    color: '#9ca3af',
    fontSize: 14,
    marginTop: 4,
  },
  realtimeHint: {
    color: '#6b7280',
    fontSize: 11,
    textAlign: 'center',
    marginTop: 8,
  },
});
