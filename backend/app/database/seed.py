"""Database seeding - Initial data population"""

from sqlalchemy.orm import Session
from app.database.config import SessionLocal, init_db
from app.database.models import User, Project, Task, Agent, AgentType, ProjectStatus, TaskStatus
from app.database.services import UserService, ProjectService, TaskService, AgentService
import uuid
from datetime import datetime, timedelta


def seed_database():
    """Populate database with sample data"""
    
    # Initialize database (create all tables)
    init_db()
    
    db = SessionLocal()
    
    try:
        # Clear existing data
        db.query(Task).delete()
        db.query(Agent).delete()
        db.query(Project).delete()
        db.query(User).delete()
        db.commit()
        
        print("🌱 Seeding database with initial data...")
        
        # 1. Create Users
        print("\n👥 Creating users...")
        users = [
            UserService.create_user(
                db, 
                username="admin",
                email="admin@omnidev.ai",
                hashed_password="$2b$12$fake_hashed_password_admin",  # In production, use bcrypt
                full_name="Admin User"
            ),
            UserService.create_user(
                db,
                username="dev1",
                email="dev1@omnidev.ai",
                hashed_password="$2b$12$fake_hashed_password_dev1",
                full_name="Developer One"
            ),
            UserService.create_user(
                db,
                username="dev2",
                email="dev2@omnidev.ai",
                hashed_password="$2b$12$fake_hashed_password_dev2",
                full_name="Developer Two"
            ),
        ]
        print(f"   ✅ Created {len(users)} users")
        
        # 2. Create Agents
        print("\n🤖 Creating agents...")
        agents = [
            AgentService.create_agent(db, "PlannerAgent", AgentType.PLANNER),
            AgentService.create_agent(db, "CodeAgent", AgentType.CODE),
            AgentService.create_agent(db, "WebAgent", AgentType.WEB),
            AgentService.create_agent(db, "DevOpsAgent", AgentType.DEVOPS),
        ]
        print(f"   ✅ Created {len(agents)} agents")
        
        # 3. Create Projects
        print("\n📁 Creating projects...")
        projects = [
            ProjectService.create_project(
                db,
                title="E-Commerce Platform",
                description="Build a full-featured e-commerce platform with mobile and web apps",
                project_type="web",
                owner_id=users[0].id,
                tech_stack=["React", "Node.js", "PostgreSQL", "Redis"]
            ),
            ProjectService.create_project(
                db,
                title="AI ChatBot",
                description="Develop an intelligent chatbot using LLMs",
                project_type="api",
                owner_id=users[1].id,
                tech_stack=["Python", "FastAPI", "OpenAI", "LangChain"]
            ),
            ProjectService.create_project(
                db,
                title="Mobile Banking App",
                description="Create a secure mobile banking application",
                project_type="mobile",
                owner_id=users[2].id,
                tech_stack=["Kotlin", "Jetpack Compose", "Spring Boot"]
            ),
        ]
        print(f"   ✅ Created {len(projects)} projects")
        
        # 4. Create Tasks
        print("\n📋 Creating tasks...")
        tasks = [
            # Project 1 tasks
            TaskService.create_task(
                db,
                title="Design Database Schema",
                project_id=projects[0].id,
                description="Design and create database schema for e-commerce",
                agent_type=AgentType.CODE,
                context={"framework": "PostgreSQL", "complexity": "high"}
            ),
            TaskService.create_task(
                db,
                title="Create User Authentication API",
                project_id=projects[0].id,
                description="Build JWT-based authentication endpoints",
                agent_type=AgentType.CODE,
                context={"framework": "Node.js", "auth_type": "JWT"}
            ),
            TaskService.create_task(
                db,
                title="Build Product Catalog Frontend",
                project_id=projects[0].id,
                description="Create product listing and filtering UI",
                agent_type=AgentType.WEB,
                context={"framework": "React", "components": 15}
            ),
            
            # Project 2 tasks
            TaskService.create_task(
                db,
                title="Integrate OpenAI API",
                project_id=projects[1].id,
                description="Connect to OpenAI GPT models",
                agent_type=AgentType.CODE,
                context={"model": "gpt-4", "api_version": "v1"}
            ),
            TaskService.create_task(
                db,
                title="Build Chat Interface",
                project_id=projects[1].id,
                description="Create a user-friendly chat UI",
                agent_type=AgentType.WEB,
                context={"framework": "React", "websocket": True}
            ),
            
            # Project 3 tasks
            TaskService.create_task(
                db,
                title="Setup Mobile UI Components",
                project_id=projects[2].id,
                description="Create reusable Jetpack Compose components",
                agent_type=AgentType.WEB,
                context={"framework": "Jetpack Compose", "components": 20}
            ),
        ]
        print(f"   ✅ Created {len(tasks)} tasks")
        
        # 5. Update some task statuses for variety
        print("\n🔄 Updating task statuses...")
        TaskService.update_task_status(db, tasks[0].id, TaskStatus.COMPLETED)
        TaskService.update_task_progress(db, tasks[0].id, 100.0, {"files_created": 3, "tables": 12})
        
        TaskService.update_task_status(db, tasks[1].id, TaskStatus.IN_PROGRESS)
        TaskService.update_task_progress(db, tasks[1].id, 65.0)
        
        TaskService.update_task_status(db, tasks[2].id, TaskStatus.IN_PROGRESS)
        TaskService.update_task_progress(db, tasks[2].id, 40.0)
        
        print("   ✅ Updated task statuses")
        
        # 6. Update agent statistics
        print("\n📊 Setting agent statistics...")
        AgentService.increment_agent_stats(db, agents[0].id, tasks_processed=25)
        AgentService.increment_agent_stats(db, agents[1].id, files_generated=87, tasks_processed=35)
        AgentService.increment_agent_stats(db, agents[2].id, components_created=52, tasks_processed=40)
        AgentService.increment_agent_stats(db, agents[3].id, deployments=15, tasks_processed=18)
        print("   ✅ Updated agent statistics")
        
        # 7. Update project statuses
        print("\n📈 Setting project statuses...")
        ProjectService.update_project_status(db, projects[0].id, ProjectStatus.IN_PROGRESS)
        ProjectService.update_project_status(db, projects[1].id, ProjectStatus.IN_PROGRESS)
        ProjectService.update_project_status(db, projects[2].id, ProjectStatus.PLANNING)
        print("   ✅ Updated project statuses")
        
        print("\n✅ Database seeding completed successfully!")
        print(f"\n📊 Summary:")
        print(f"   • Users: {len(users)}")
        print(f"   • Agents: {len(agents)}")
        print(f"   • Projects: {len(projects)}")
        print(f"   • Tasks: {len(tasks)}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
