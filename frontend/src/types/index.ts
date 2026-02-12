export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  avatar_url?: string;
  created_at?: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  owner_id: string;
  created_at?: string;
  updated_at?: string;
}

export interface Task {
  id: string;
  project_id: string;
  title: string;
  description?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at?: string;
  updated_at?: string;
}

export interface Agent {
  id: string;
  name: string;
  type: 'planner' | 'code' | 'web' | 'devops';
  description?: string;
  status: 'idle' | 'executing' | 'error';
}

export interface Message {
  id: string;
  user_id: string;
  content: string;
  role: 'user' | 'assistant';
  created_at?: string;
}
