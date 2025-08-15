#!/usr/bin/env python3
"""
Knowledge Management and RAG Workflow
Handles document storage, retrieval, and AI-augmented knowledge management
"""

import os
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import redis
import hashlib
import re
from urllib.parse import urlparse

# Windmill imports
import wmill

class KnowledgeManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://ollama:11434')
        self.qdrant_url = os.getenv('QDRANT_URL', 'http://qdrant:6333')
        self.searxng_url = os.getenv('SEARXNG_URL', 'http://searxng:8080')
        self.collection_name = 'knowledge_base'

        # Initialize collection on startup
        asyncio.create_task(self._ensure_collection())

    async def _ensure_collection(self):
        """Ensure the knowledge collection exists in Qdrant"""
        async with aiohttp.ClientSession() as session:
            try:
                # Check if collection exists
                async with session.get(f'{self.qdrant_url}/collections/{self.collection_name}') as resp:
                    if resp.status == 404:
                        # Create collection
                        await session.put(
                            f'{self.qdrant_url}/collections/{self.collection_name}',
                            json={
                                'vectors': {
                                    'size': 384,  # all-minilm embedding size
                                    'distance': 'Cosine'
                                }
                            }
                        )
            except Exception as e:
                print(f"Collection initialization error: {e}")

    async def ingest_document(
        self,
        content: str,
        title: str,
        source: str = "manual",
        metadata: Dict = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        user_id: str = "default"
    ) -> Dict:
        """Ingest a document into the knowledge base"""

        # Generate document ID
        doc_id = hashlib.md5(
            f"{title}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        # Split content into chunks
        chunks = self._chunk_text(content, chunk_size, chunk_overlap)

        # Process each chunk
        stored_chunks = []
        async with aiohttp.ClientSession() as session:
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_{i}"

                # Generate embedding
                embed_payload = {
                    'model': 'all-minilm',
                    'prompt': chunk
                }

                try:
                    async with session.post(f'{self.ollama_url}/api/embeddings', json=embed_payload) as resp:
                        if resp.status == 200:
                            embed_data = await resp.json()
                            embedding = embed_data.get('embedding')

                            # Prepare chunk metadata
                            chunk_metadata = {
                                'document_id': doc_id,
                                'chunk_index': i,
                                'title': title,
                                'source': source,
                                'content': chunk,
                                'created_at': datetime.now().isoformat(),
                                'user_id': user_id,
                                **(metadata or {})
                            }

                            # Store in Qdrant
                            point = {
                                'id': chunk_id,
                                'vector': embedding,
                                'payload': chunk_metadata
                            }

                            await session.put(
                                f'{self.qdrant_url}/collections/{self.collection_name}/points',
                                json={'points': [point]}
                            )

                            stored_chunks.append(chunk_id)
                except Exception as e:
                    print(f"Chunk storage error: {e}")

        # Store document metadata in Redis
        doc_key = f'document:{user_id}:{doc_id}'
        doc_metadata = {
            'id': doc_id,
            'title': title,
            'source': source,
            'chunks': stored_chunks,
            'total_chunks': len(chunks),
            'created_at': datetime.now().isoformat(),
            'metadata': metadata
        }
        self.redis_client.setex(doc_key, 2592000, json.dumps(doc_metadata))  # 30 days TTL

        return {
            'document_id': doc_id,
            'chunks_stored': len(stored_chunks),
            'total_chunks': len(chunks),
            'title': title,
            'status': 'success'
        }

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into overlapping chunks"""
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))

                # Start new chunk with overlap
                if overlap > 0 and len(current_chunk) > 1:
                    # Keep last few sentences for overlap
                    overlap_sentences = []
                    overlap_size = 0
                    for s in reversed(current_chunk):
                        overlap_size += len(s)
                        if overlap_size >= overlap:
                            break
                        overlap_sentences.insert(0, s)
                    current_chunk = overlap_sentences
                    current_size = sum(len(s) for s in current_chunk)
                else:
                    current_chunk = []
                    current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_size

        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    async def search_knowledge(
        self,
        query: str,
        limit: int = 5,
        filter_source: Optional[str] = None,
        user_id: str = "default"
    ) -> List[Dict]:
        """Search the knowledge base"""

        async with aiohttp.ClientSession() as session:
            try:
                # Generate query embedding
                embed_payload = {
                    'model': 'all-minilm',
                    'prompt': query
                }

                async with session.post(f'{self.ollama_url}/api/embeddings', json=embed_payload) as resp:
                    if resp.status == 200:
                        embed_data = await resp.json()
                        embedding = embed_data.get('embedding')

                        # Build filter
                        search_filter = {
                            'must': [
                                {'key': 'user_id', 'match': {'value': user_id}}
                            ]
                        }

                        if filter_source:
                            search_filter['must'].append({
                                'key': 'source',
                                'match': {'value': filter_source}
                            })

                        # Search in Qdrant
                        search_payload = {
                            'vector': embedding,
                            'limit': limit,
                            'with_payload': True,
                            'filter': search_filter
                        }

                        async with session.post(
                            f'{self.qdrant_url}/collections/{self.collection_name}/points/search',
                            json=search_payload
                        ) as search_resp:
                            if search_resp.status == 200:
                                search_data = await search_resp.json()
                                return [
                                    {
                                        'content': r['payload']['content'],
                                        'title': r['payload']['title'],
                                        'source': r['payload']['source'],
                                        'score': r['score'],
                                        'metadata': r['payload']
                                    }
                                    for r in search_data.get('result', [])
                                ]
            except Exception as e:
                print(f"Search error: {e}")

        return []

    async def rag_query(
        self,
        query: str,
        context_limit: int = 3,
        model: str = None,
        user_id: str = "default"
    ) -> Dict:
        """Perform RAG query - search knowledge and generate response"""

        # Search for relevant context
        context_docs = await self.search_knowledge(
            query=query,
            limit=context_limit,
            user_id=user_id
        )

        if not context_docs:
            # No relevant context found, use general knowledge
            context_text = "No specific context found in knowledge base."
        else:
            # Compile context from retrieved documents
            context_text = "\n\n".join([
                f"[Source: {doc['title']}]\n{doc['content']}"
                for doc in context_docs
            ])

        # Generate response using LLM with context
        async with aiohttp.ClientSession() as session:
            try:
                prompt = f"""Based on the following context, answer the query accurately.
If the context doesn't contain relevant information, say so and provide a general answer.

Context:
{context_text}

Query: {query}

Answer:"""

                payload = {
                    'model': model or os.getenv('DEFAULT_LLM_MODEL', 'llama3.2:latest'),
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.3,  # Lower temperature for factual responses
                        'max_tokens': 500
                    }
                }

                async with session.post(f'{self.ollama_url}/api/generate', json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response = data.get('response', 'Unable to generate response')
                    else:
                        response = "LLM service unavailable"
            except Exception as e:
                print(f"RAG generation error: {e}")
                response = f"Error generating response: {str(e)}"

        # Cache the query and response
        cache_key = f'rag_cache:{user_id}:{hashlib.md5(query.encode()).hexdigest()}'
        cache_data = {
            'query': query,
            'response': response,
            'context_docs': [{'title': d['title'], 'source': d['source']} for d in context_docs],
            'timestamp': datetime.now().isoformat()
        }
        self.redis_client.setex(cache_key, 3600, json.dumps(cache_data))  # 1 hour cache

        return {
            'query': query,
            'response': response,
            'context_used': len(context_docs),
            'sources': [{'title': d['title'], 'source': d['source'], 'score': d['score']} for d in context_docs],
            'cached': False
        }

    async def ingest_url(
        self,
        url: str,
        user_id: str = "default"
    ) -> Dict:
        """Ingest content from a URL"""

        async with aiohttp.ClientSession() as session:
            try:
                # Use Jina Reader or similar for web extraction
                reader_url = f"https://r.jina.ai/{url}"
                headers = {'Accept': 'application/json'}

                async with session.get(reader_url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data.get('content', '')
                        title = data.get('title', urlparse(url).netloc)
                    else:
                        # Fallback to basic fetch
                        async with session.get(url) as fallback_resp:
                            if fallback_resp.status == 200:
                                content = await fallback_resp.text()
                                # Simple HTML stripping (in production, use BeautifulSoup)
                                content = re.sub(r'<[^>]+>', '', content)
                                title = urlparse(url).netloc
                            else:
                                return {'error': f'Failed to fetch URL: {fallback_resp.status}'}

                # Ingest the content
                return await self.ingest_document(
                    content=content,
                    title=title,
                    source=url,
                    metadata={'type': 'web', 'url': url},
                    user_id=user_id
                )

            except Exception as e:
                return {'error': f'URL ingestion failed: {str(e)}'}

    async def get_knowledge_stats(self, user_id: str = "default") -> Dict:
        """Get statistics about the knowledge base"""

        # Get document count from Redis
        doc_pattern = f'document:{user_id}:*'
        doc_keys = self.redis_client.keys(doc_pattern)

        total_docs = len(doc_keys)
        total_chunks = 0
        sources = {}

        for key in doc_keys:
            doc_data = self.redis_client.get(key)
            if doc_data:
                doc = json.loads(doc_data)
                total_chunks += doc.get('total_chunks', 0)
                source = doc.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1

        # Get collection stats from Qdrant
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f'{self.qdrant_url}/collections/{self.collection_name}') as resp:
                    if resp.status == 200:
                        collection_data = await resp.json()
                        vectors_count = collection_data.get('result', {}).get('vectors_count', 0)
                    else:
                        vectors_count = 0
            except:
                vectors_count = 0

        return {
            'total_documents': total_docs,
            'total_chunks': total_chunks,
            'total_vectors': vectors_count,
            'sources': sources,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }

@wmill.main()
async def main(
    action: str,
    user_id: str = "default",
    **kwargs
):
    """
    Main entry point for knowledge management workflow

    Args:
        action: Action to perform (ingest, search, rag, ingest_url, stats)
        user_id: User identifier
        **kwargs: Additional parameters based on action

    Returns:
        Result of the requested action
    """
    km = KnowledgeManager()

    if action == "ingest":
        return await km.ingest_document(
            content=kwargs.get('content'),
            title=kwargs.get('title'),
            source=kwargs.get('source', 'manual'),
            metadata=kwargs.get('metadata'),
            chunk_size=kwargs.get('chunk_size', 500),
            chunk_overlap=kwargs.get('chunk_overlap', 50),
            user_id=user_id
        )

    elif action == "search":
        return await km.search_knowledge(
            query=kwargs.get('query'),
            limit=kwargs.get('limit', 5),
            filter_source=kwargs.get('filter_source'),
            user_id=user_id
        )

    elif action == "rag":
        return await km.rag_query(
            query=kwargs.get('query'),
            context_limit=kwargs.get('context_limit', 3),
            model=kwargs.get('model'),
            user_id=user_id
        )

    elif action == "ingest_url":
        return await km.ingest_url(
            url=kwargs.get('url'),
            user_id=user_id
        )

    elif action == "stats":
        return await km.get_knowledge_stats(user_id)

    else:
        return {'error': f'Unknown action: {action}'}

# For testing locally
if __name__ == "__main__":
    import asyncio
    # Example: Ingest a document
    result = asyncio.run(main(
        action="ingest",
        title="Test Document",
        content="This is a test document about artificial intelligence and machine learning."
    ))
    print(json.dumps(result, indent=2))
