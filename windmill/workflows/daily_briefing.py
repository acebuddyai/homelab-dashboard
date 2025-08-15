#!/usr/bin/env python3
"""
Daily Briefing Workflow
Generates a comprehensive daily briefing with weather, news, tasks, and AI insights
"""

import os
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import redis
import hashlib

# Windmill imports
import wmill

class DailyBriefing:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://ollama:11434')
        self.searxng_url = os.getenv('SEARXNG_URL', 'http://searxng:8080')
        self.qdrant_url = os.getenv('QDRANT_URL', 'http://qdrant:6333')

    async def fetch_weather(self, location: str = None) -> Dict:
        """Fetch weather information using web search"""
        if not location:
            location = self.redis_client.get('user:location') or 'London'

        async with aiohttp.ClientSession() as session:
            try:
                # Search for weather
                params = {
                    'q': f'weather {location} today forecast',
                    'categories': 'general',
                    'format': 'json'
                }
                async with session.get(f'{self.searxng_url}/search', params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get('results', [])
                        if results:
                            # Extract weather info from search results
                            weather_text = results[0].get('content', 'Weather data unavailable')
                            return {
                                'location': location,
                                'summary': weather_text[:200],
                                'source': 'web_search'
                            }
            except Exception as e:
                print(f"Weather fetch error: {e}")

        return {
            'location': location,
            'summary': 'Weather information currently unavailable',
            'source': 'error'
        }

    async def fetch_news(self, categories: List[str] = None) -> List[Dict]:
        """Fetch news headlines from multiple categories"""
        if not categories:
            categories = ['technology', 'science', 'business']

        all_news = []
        async with aiohttp.ClientSession() as session:
            for category in categories:
                try:
                    params = {
                        'q': f'latest {category} news {datetime.now().strftime("%Y-%m-%d")}',
                        'categories': 'news',
                        'format': 'json',
                        'time_range': 'day'
                    }
                    async with session.get(f'{self.searxng_url}/search', params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            results = data.get('results', [])[:3]  # Top 3 per category
                            for result in results:
                                all_news.append({
                                    'category': category,
                                    'title': result.get('title', ''),
                                    'summary': result.get('content', '')[:150],
                                    'url': result.get('url', ''),
                                    'source': result.get('engine', 'unknown')
                                })
                except Exception as e:
                    print(f"News fetch error for {category}: {e}")

        return all_news

    async def fetch_tasks(self, user_id: str = 'default') -> List[Dict]:
        """Fetch tasks from cache or generate reminders"""
        # Check Redis for cached tasks
        tasks_key = f'tasks:{user_id}:{datetime.now().strftime("%Y-%m-%d")}'
        cached_tasks = self.redis_client.get(tasks_key)

        if cached_tasks:
            return json.loads(cached_tasks)

        # Generate default daily tasks/reminders
        default_tasks = [
            {'title': 'Review daily goals', 'priority': 'high', 'time': '09:00'},
            {'title': 'Check email and messages', 'priority': 'medium', 'time': '09:30'},
            {'title': 'Daily exercise', 'priority': 'high', 'time': '17:00'},
            {'title': 'Plan tomorrow', 'priority': 'medium', 'time': '20:00'}
        ]

        # Cache for the day
        self.redis_client.setex(tasks_key, 86400, json.dumps(default_tasks))
        return default_tasks

    async def get_ai_insights(self, context: Dict) -> str:
        """Generate AI insights based on the day's information"""
        async with aiohttp.ClientSession() as session:
            try:
                # Prepare context for AI
                prompt = f"""Based on today's information, provide 3 actionable insights or recommendations:

Weather: {context.get('weather', {}).get('summary', 'Not available')}
Top News: {', '.join([n['title'] for n in context.get('news', [])[:3]])}
Tasks: {len(context.get('tasks', []))} scheduled

Provide practical, personalized recommendations for the day."""

                payload = {
                    'model': os.getenv('DEFAULT_LLM_MODEL', 'llama3.2:latest'),
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.7,
                        'max_tokens': 200
                    }
                }

                async with session.post(f'{self.ollama_url}/api/generate', json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get('response', 'AI insights unavailable')
            except Exception as e:
                print(f"AI insights error: {e}")

        return "AI insights temporarily unavailable"

    async def search_previous_briefings(self, query: str) -> List[Dict]:
        """Search previous briefings from vector database"""
        async with aiohttp.ClientSession() as session:
            try:
                # First, get embedding for the query
                embed_payload = {
                    'model': 'all-minilm',
                    'prompt': query
                }
                async with session.post(f'{self.ollama_url}/api/embeddings', json=embed_payload) as resp:
                    if resp.status == 200:
                        embed_data = await resp.json()
                        embedding = embed_data.get('embedding')

                        # Search in Qdrant
                        search_payload = {
                            'vector': embedding,
                            'limit': 3,
                            'with_payload': True
                        }
                        async with session.post(
                            f'{self.qdrant_url}/collections/briefings/points/search',
                            json=search_payload
                        ) as search_resp:
                            if search_resp.status == 200:
                                search_data = await search_resp.json()
                                return search_data.get('result', [])
            except Exception as e:
                print(f"Search error: {e}")

        return []

    async def store_briefing(self, briefing: Dict) -> bool:
        """Store briefing in vector database for future reference"""
        async with aiohttp.ClientSession() as session:
            try:
                # Create text representation of briefing
                briefing_text = json.dumps(briefing, indent=2)

                # Get embedding
                embed_payload = {
                    'model': 'all-minilm',
                    'prompt': briefing_text[:1000]  # Limit text length
                }
                async with session.post(f'{self.ollama_url}/api/embeddings', json=embed_payload) as resp:
                    if resp.status == 200:
                        embed_data = await resp.json()
                        embedding = embed_data.get('embedding')

                        # Store in Qdrant
                        point_id = hashlib.md5(
                            f"{datetime.now().isoformat()}".encode()
                        ).hexdigest()[:16]

                        store_payload = {
                            'points': [{
                                'id': point_id,
                                'vector': embedding,
                                'payload': {
                                    'date': datetime.now().isoformat(),
                                    'briefing': briefing,
                                    'type': 'daily_briefing'
                                }
                            }]
                        }

                        # Ensure collection exists
                        await session.put(
                            f'{self.qdrant_url}/collections/briefings',
                            json={
                                'vectors': {
                                    'size': 384,
                                    'distance': 'Cosine'
                                }
                            }
                        )

                        # Store the point
                        async with session.put(
                            f'{self.qdrant_url}/collections/briefings/points',
                            json=store_payload
                        ) as store_resp:
                            return store_resp.status == 200
            except Exception as e:
                print(f"Store briefing error: {e}")

        return False

    async def generate_briefing(self, user_id: str = 'default', options: Dict = None) -> Dict:
        """Generate the complete daily briefing"""
        options = options or {}

        # Fetch all information in parallel
        weather_task = self.fetch_weather(options.get('location'))
        news_task = self.fetch_news(options.get('news_categories'))
        tasks_task = self.fetch_tasks(user_id)

        weather, news, tasks = await asyncio.gather(
            weather_task, news_task, tasks_task
        )

        # Generate AI insights
        context = {
            'weather': weather,
            'news': news,
            'tasks': tasks
        }
        ai_insights = await self.get_ai_insights(context)

        # Check for relevant past briefings
        past_briefings = await self.search_previous_briefings(
            f"briefing {datetime.now().strftime('%A')}"
        )

        # Compile the briefing
        briefing = {
            'date': datetime.now().isoformat(),
            'day': datetime.now().strftime('%A, %B %d, %Y'),
            'weather': weather,
            'news': news,
            'tasks': tasks,
            'ai_insights': ai_insights,
            'related_briefings': [
                {
                    'date': pb.get('payload', {}).get('date'),
                    'score': pb.get('score')
                }
                for pb in past_briefings
            ],
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'user_id': user_id,
                'version': '1.0'
            }
        }

        # Store the briefing
        await self.store_briefing(briefing)

        # Cache in Redis for quick access
        cache_key = f'briefing:{user_id}:{datetime.now().strftime("%Y-%m-%d")}'
        self.redis_client.setex(cache_key, 86400, json.dumps(briefing))

        return briefing

@wmill.main()
async def main(
    user_id: str = 'default',
    location: str = None,
    news_categories: List[str] = None,
    include_past_briefings: bool = True
):
    """
    Main entry point for Windmill workflow

    Args:
        user_id: User identifier for personalization
        location: Location for weather (auto-detected if not provided)
        news_categories: News categories to include
        include_past_briefings: Whether to search for related past briefings

    Returns:
        Complete daily briefing as formatted text and structured data
    """
    briefing_generator = DailyBriefing()

    options = {
        'location': location,
        'news_categories': news_categories
    }

    # Generate the briefing
    briefing = await briefing_generator.generate_briefing(user_id, options)

    # Format for display
    formatted_text = f"""
🌅 **Daily Briefing**
📅 {briefing['day']}

☁️ **Weather in {briefing['weather']['location']}**
{briefing['weather']['summary']}

📰 **Today's Headlines**
"""

    for news_item in briefing['news'][:5]:
        formatted_text += f"\n**[{news_item['category'].upper()}]** {news_item['title']}\n"
        formatted_text += f"   {news_item['summary']}...\n"

    formatted_text += f"\n✅ **Today's Tasks**\n"
    for task in briefing['tasks']:
        formatted_text += f"• {task['time']} - {task['title']} [{task['priority']}]\n"

    formatted_text += f"\n🤖 **AI Insights**\n{briefing['ai_insights']}\n"

    if briefing['related_briefings']:
        formatted_text += f"\n📚 **Related Past Briefings**\n"
        for related in briefing['related_briefings']:
            formatted_text += f"• {related['date']} (Relevance: {related['score']:.2f})\n"

    return {
        'formatted': formatted_text,
        'structured': briefing,
        'status': 'success',
        'cached_key': f'briefing:{user_id}:{datetime.now().strftime("%Y-%m-%d")}'
    }

# For testing locally
if __name__ == "__main__":
    import asyncio
    result = asyncio.run(main())
    print(result['formatted'])
