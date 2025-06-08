# Task: Django Project Setup

**ID**: TASK-021  
**Story**: [STORY-006: Document Upload Interface](../stories/STORY-006.md)  
**Assignee**: Backend Developer  
**Status**: Todo  
**Effort**: 1 day  
**Created**: 2024-03-19  
**Updated**: 2024-03-19

## Description

Set up the Django project structure with all necessary dependencies and configurations for the RAG system.
This includes setting up Django REST framework, Celery, Django Channels, and the development environment.

## Implementation Hints

- [ ] Create requirements.txt
  ```txt
  Django>=5.0.0
  djangorestframework>=3.14.0
  django-cors-headers>=4.3.0
  channels>=4.0.0
  celery>=5.3.0
  redis>=5.0.0
  llama-index>=0.9.0
  python-dotenv>=1.0.0
  ```
- [ ] Initialize Django project structure
  ```bash
  # Create and activate virtual environment
  python -m venv venv
  source venv/bin/activate  # or `venv\Scripts\activate` on Windows

  # Install dependencies
  pip install -r requirements.txt

  # Create Django project
  django-admin startproject rag_project
  cd rag_project

  # Create apps
  python manage.py startapp document_processor
  python manage.py startapp api
  ```
- [ ] Configure Django settings
  ```python
  # rag_project/settings.py
  INSTALLED_APPS = [
      # ...
      'rest_framework',
      'corsheaders',
      'channels',
      'document_processor',
      'api',
  ]

  CORS_ALLOWED_ORIGINS = [
      "http://localhost:5173",  # Vite default port
  ]

  CHANNEL_LAYERS = {
      'default': {
          'BACKEND': 'channels_redis.core.RedisChannelLayer',
          'CONFIG': {
              "hosts": [('127.0.0.1', 6379)],
          },
      },
  }
  ```
- [ ] Set up Celery configuration
  ```python
  # rag_project/celery.py
  from celery import Celery
  import os

  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_project.settings')

  app = Celery('rag_project')
  app.config_from_object('django.conf:settings', namespace='CELERY')
  app.autodiscover_tasks()
  ```
- [ ] Configure ASGI for WebSocket support
  ```python
  # rag_project/asgi.py
  from channels.routing import ProtocolTypeRouter

  application = ProtocolTypeRouter({
      # Empty for now, will be configured in TASK-019
  })
  ```

## Acceptance Criteria

- [ ] Django project successfully created with all required apps
- [ ] Dependencies installed and documented in requirements.txt
- [ ] Development environment configured with virtual environment
- [ ] Django REST framework properly configured
- [ ] CORS headers set up for frontend integration
- [ ] Celery configured with Redis as message broker
- [ ] Django Channels set up for WebSocket support
- [ ] Basic project structure documented

## Dependencies

- **Blocked by**: None
- **Blocks**: TASK-019 (Document Processing Integration)

---

**Implementer**: Backend Developer  
**Reviewer**: Lead Developer  
**Target Completion**: TBD
