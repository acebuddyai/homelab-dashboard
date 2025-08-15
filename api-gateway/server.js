const express = require('express');
const axios = require('axios');
const cors = require('cors');
const helmet = require('helmet');
require('dotenv').config();

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// ============= AI/LLM Endpoints =============
app.post('/api/ai/chat', async (req, res) => {
    try {
        const { model, messages, stream = false } = req.body;
        const ollamaUrl = process.env.OLLAMA_URL || 'http://ollama:11434';

        const response = await axios.post(`${ollamaUrl}/api/chat`, {
            model: model || 'llama3.2:latest',
            messages,
            stream
        });

        res.json(response.data);
    } catch (error) {
        console.error('AI Chat Error:', error.message);
        res.status(500).json({ error: 'AI service unavailable' });
    }
});

app.post('/api/ai/embeddings', async (req, res) => {
    try {
        const { text, model = 'all-minilm' } = req.body;
        const ollamaUrl = process.env.OLLAMA_URL || 'http://ollama:11434';

        const response = await axios.post(`${ollamaUrl}/api/embeddings`, {
            model,
            prompt: text
        });

        res.json(response.data);
    } catch (error) {
        console.error('Embeddings Error:', error.message);
        res.status(500).json({ error: 'Embedding service unavailable' });
    }
});

// ============= Memory/Knowledge Endpoints =============
app.post('/api/memory/store', async (req, res) => {
    try {
        const { collection = 'default', documents } = req.body;
        const ollamaUrl = process.env.OLLAMA_URL || 'http://ollama:11434';
        const qdrantUrl = process.env.QDRANT_URL || 'http://qdrant:6333';

        // Generate embeddings for documents
        const embeddings = await Promise.all(
            documents.map(async (doc) => {
                const embResponse = await axios.post(`${ollamaUrl}/api/embeddings`, {
                    model: 'all-minilm',
                    prompt: doc.text
                });
                return embResponse.data.embedding;
            })
        );

        // Store in Qdrant
        const points = documents.map((doc, i) => ({
            id: Date.now() + i,
            vector: embeddings[i],
            payload: doc
        }));

        await axios.put(`${qdrantUrl}/collections/${collection}/points`, {
            points
        });

        res.json({ success: true, stored: documents.length });
    } catch (error) {
        console.error('Memory Store Error:', error.message);
        res.status(500).json({ error: 'Memory service unavailable' });
    }
});

app.post('/api/memory/search', async (req, res) => {
    try {
        const { collection = 'default', query, limit = 5 } = req.body;
        const ollamaUrl = process.env.OLLAMA_URL || 'http://ollama:11434';
        const qdrantUrl = process.env.QDRANT_URL || 'http://qdrant:6333';

        // Generate embedding for query
        const embResponse = await axios.post(`${ollamaUrl}/api/embeddings`, {
            model: 'all-minilm',
            prompt: query
        });

        // Search in Qdrant
        const searchResponse = await axios.post(
            `${qdrantUrl}/collections/${collection}/points/search`,
            {
                vector: embResponse.data.embedding,
                limit
            }
        );

        res.json(searchResponse.data);
    } catch (error) {
        console.error('Memory Search Error:', error.message);
        res.status(500).json({ error: 'Memory search failed' });
    }
});

// ============= Workflow Endpoints =============
app.post('/api/workflow/execute', async (req, res) => {
    try {
        const { workflow_path, inputs } = req.body;
        const windmillUrl = process.env.WINDMILL_URL || 'http://windmill-server:8000';

        // For now, return a mock response
        res.json({
            job_id: `job_${Date.now()}`,
            status: 'queued',
            workflow_path,
            message: 'Workflow execution queued'
        });
    } catch (error) {
        console.error('Workflow Error:', error.message);
        res.status(500).json({ error: 'Workflow execution failed' });
    }
});

// ============= Search Endpoints =============
app.get('/api/search', async (req, res) => {
    try {
        const { q, categories = 'general' } = req.query;
        const searxngUrl = process.env.SEARXNG_URL || 'http://searxng:8080';

        const response = await axios.get(`${searxngUrl}/search`, {
            params: {
                q,
                categories,
                format: 'json'
            }
        });

        res.json(response.data);
    } catch (error) {
        console.error('Search Error:', error.message);
        res.status(500).json({ error: 'Search service unavailable' });
    }
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Something went wrong!' });
});

// Start server
app.listen(PORT, () => {
    console.log(`API Gateway running on port ${PORT}`);
});
