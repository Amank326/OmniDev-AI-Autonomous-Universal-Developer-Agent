# Phase 4 Quick Start - Real-time Integration Guide

**Ready to use real-time features in your app?** Follow this quick guide.

---

## 🚀 For Web (Next.js) Developers

### Step 1: Import the Hook
```typescript
import { useProjectWebSocket } from '@/hooks/useWebSocket';
```

### Step 2: Use in Your Component
```typescript
export function MyProjectPage({ projectId, userId }) {
  const { isConnected, send } = useProjectWebSocket(
    projectId,
    userId,
    {
      onTaskCreated: (task) => {
        console.log('New task:', task);
        // Update your state here
      },
      onTaskUpdated: (task) => {
        // Handle task update
      },
      onTaskDeleted: (taskId) => {
        // Handle task deletion
      },
    }
  );

  return (
    <div>
      <span>{isConnected ? '🟢 Connected' : '⚪ Disconnected'}</span>
      {/* Your project UI */}
    </div>
  );
}
```

### Step 3: Use the Provided Components
```typescript
import { RealtimeTasks } from '@/components/RealtimeTasks';
import { WebSocketStatus } from '@/components/WebSocketStatus';

export default function Dashboard() {
  return (
    <div>
      <RealtimeTasks 
        projectId="123"
        tasks={tasks}
        onTasksChange={setTasks}
        onDeleteTask={deleteTask}
      />
      <WebSocketStatus showDetails={true} />
    </div>
  );
}
```

---

## 📱 For Mobile (React Native) Developers

### Step 1: Import the Hook
```typescript
import { useProjectWebSocket } from '@/hooks/useWebSocket';
```

### Step 2: Use in Your Component
```typescript
export function ProjectScreen({ projectId, userId }) {
  const { isConnected } = useProjectWebSocket(
    projectId,
    userId,
    {
      onTaskCreated: (task) => {
        // Update FlatList data
        setTasks(prev => [task, ...prev]);
      },
      onTaskUpdated: (task) => {
        // Update task in list
        setTasks(prev =>
          prev.map(t => t.id === task.id ? task : t)
        );
      },
      onTaskDeleted: (taskId) => {
        // Remove from list
        setTasks(prev => prev.filter(t => t.id !== taskId));
      },
    }
  );

  return (
    <View>
      <Text>{isConnected ? '🟢 Connected' : '⚪ Disconnected'}</Text>
      {/* Your project UI */}
    </View>
  );
}
```

### Step 3: Use the Provided Component
```typescript
import { RealtimeTasks } from '@/components/RealtimeTasks';

export default function ProjectScreen() {
  return (
    <RealtimeTasks 
      projectId="123"
      initialTasks={tasks}
      onDeleteTask={deleteTask}
    />
  );
}
```

---

## 🔌 Testing Your Integration

### Test 1: Basic Connection
```typescript
const { isConnected } = useWebSocket({
  url: 'ws://localhost:8000/ws/project/test-id',
  userId: 'test-user',
  onConnect: () => console.log('Connected!'),
});

// Expected: "Connected!" appears in console after ~1s
```

### Test 2: Real-time Updates
1. Open app in two browser tabs/devices
2. Create a task in Tab A
3. Verify it appears instantly in Tab B
4. Disconnect Tab A (refresh page)
5. Update task in Tab B
6. Reconnect Tab A
7. Verify update is present

### Test 3: Auto-Reconnection
1. Open WebSocket inspector (DevTools → Network)
2. Create a task (see in inspector)
3. Close network in DevTools (offline mode)
4. Create another task (see in queue)
5. Restore network
6. Verify queued task was sent

---

## 📊 Message Examples

### Task Created
```json
{
  "type": "task_created",
  "task": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Implement auth",
    "description": "Add JWT authentication",
    "status": "pending",
    "priority": "high",
    "project_id": "project-123",
    "created_at": "2024-02-06T10:00:00Z",
    "updated_at": "2024-02-06T10:00:00Z"
  },
  "project_id": "project-123",
  "timestamp": "2024-02-06T10:00:00Z",
  "active_users": ["user-1", "user-2"],
  "active_count": 2
}
```

### Task Updated
```json
{
  "type": "task_updated",
  "task": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Implement auth",
    "status": "in_progress",
    "priority": "high",
    "updated_at": "2024-02-06T10:05:00Z"
  },
  "project_id": "project-123",
  "timestamp": "2024-02-06T10:05:00Z"
}
```

### User Joined
```json
{
  "type": "user_joined",
  "user_id": "new-user-id",
  "room_id": "project:project-123",
  "active_users": ["user-1", "user-2", "new-user-id"],
  "active_count": 3,
  "timestamp": "2024-02-06T10:10:00Z"
}
```

---

## ⚙️ Configuration

### Hook Options
```typescript
{
  url: 'ws://localhost:8000/ws/...',    // Required: WebSocket URL
  userId: 'user-123',                    // Required: User ID
  autoConnect: true,                     // Optional: Auto-connect on mount
  reconnectAttempts: 5,                  // Optional: Max reconnection tries
  reconnectDelay: 3000,                  // Optional: Initial delay (3s base)
  onMessage: (msg) => {},               // Optional: Message handler
  onConnect: () => {},                  // Optional: Connection callback
  onDisconnect: () => {},               // Optional: Disconnection callback
  onError: (error) => {},               // Optional: Error handler
}
```

### Environment Variables
**Web (.env.local):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Mobile (.env):**
```
EXPO_PUBLIC_API_URL=http://localhost:8000
```

---

## 🆘 Troubleshooting

### Connection Failed
**Check:**
1. Backend is running: `docker-compose ps`
2. Backend WebSocket is accessible: `netstat -an | grep 8000`
3. Firewall allows port 8000
4. URL is correct: `ws://localhost:8000`

### Messages Not Received
**Check:**
1. You're subscribed to the correct room
2. `user_id` parameter is provided
3. Connection status is `true`
4. Message type is in the allowed list

### Rapid Reconnections
**Check:**
1. Network connection is stable
2. Backend logs for errors: `docker-compose logs backend`
3. Server isn't rejecting connections
4. Firewall isn't blocking WebSocket

### Memory Leak
**Check:**
1. Component cleanup: `useEffect(() => { return () => { disconnect() } }, [])`
2. Event listener cleanup
3. Message queue isn't growing unbounded

---

## 💡 Best Practices

### 1. Always Cleanup on Unmount
```typescript
useEffect(() => {
  return () => {
    disconnect(); // Important!
  };
}, [disconnect]);
```

### 2. Handle Disconnections Gracefully
```typescript
{!isConnected && (
  <div className="banner">
    Connecting... {error && `(${error.message})`}
  </div>
)}
```

### 3. Show Connection Status to Users
```typescript
<ConnectionBadge
  connected={isConnected}
  connecting={isConnecting}
  error={error}
/>
```

### 4. Debounce Frequent Updates
```typescript
const handleUpdate = debounce((data) => {
  send({ type: 'update', data });
}, 300);
```

### 5. Queue Messages When Offline
```typescript
send(message); // Automatically queued if offline
// Sent when reconnected
```

---

## 📚 More Resources

- **Full Guide:** `/docs/WEBSOCKET_GUIDE.md`
- **Architecture:** `/docs/ARCHITECTURE.md`
- **API Reference:** `/BUILD_COMPLETE.md`
- **Examples:** `/frontend/src/components/` and `/mobile/components/`

---

## ✅ Verification Checklist

- [ ] Backend running: `docker-compose ps`
- [ ] WebSocket endpoint accessible: Check DevTools → Network
- [ ] Hook imported correctly
- [ ] User ID provided
- [ ] Handlers defined
- [ ] Component renders
- [ ] Connection status shows
- [ ] Messages received in console
- [ ] UI updates in real-time
- [ ] Reconnection works

---

## 🎯 Common Use Cases

### 1. Show Live Task List
```typescript
const { isConnected } = useProjectWebSocket(projectId, userId, {
  onTaskCreated: (task) => setTasks(prev => [task, ...prev]),
  onTaskUpdated: (task) => setTasks(prev => 
    prev.map(t => t.id === task.id ? task : t)
  ),
  onTaskDeleted: (taskId) => setTasks(prev => 
    prev.filter(t => t.id !== taskId)
  ),
});

return <TaskList tasks={tasks} connected={isConnected} />;
```

### 2. Show Who's Viewing
```typescript
const { isConnected } = useProjectWebSocket(projectId, userId, {
  onUserJoined: (users) => setActiveUsers(users),
  onUserLeft: (count) => setActiveCount(count),
});

return <UserList users={activeUsers} />;
```

### 3. Show Live Agent Status
```typescript
const { isConnected } = useAgentWebSocket(agentId, userId, {
  onExecutionUpdate: (data) => setProgress(data.progress),
  onExecutionComplete: (data) => setResult(data.result),
});

return <AgentProgress progress={progress} />;
```

### 4. Show Notifications
```typescript
const { isConnected } = useNotificationsWebSocket(userId, {
  onNotification: (notification) => {
    toast.show(notification.message);
  },
});
```

---

## 🎉 You're Ready!

Your app now supports real-time collaboration. Users will see updates instantly without refreshing.

**Happy building! 🚀**

---

**Last Updated:** February 6, 2026  
**Phase:** 4 - Real-time Collaboration  
**Status:** ✅ Production Ready
