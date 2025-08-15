// API Configuration
let API_URL = localStorage.getItem("apiUrl") || "https://api.acebuddy.quest";
let USER_ID = localStorage.getItem("userId") || "default";
let DEFAULT_MODEL = localStorage.getItem("defaultModel") || "llama3.2:1b";

// State Management
let currentTab = "chat";
let chatHistory = [];
let tasks = [];
let knowledgeStats = {};

// Initialize app on load
document.addEventListener("DOMContentLoaded", () => {
  loadSettings();
  switchTab("chat");

  // Initialize chat with a welcome message
  console.log("Initializing chat interface...");
  console.log("API URL:", API_URL);
  console.log("Default Model:", DEFAULT_MODEL);

  // Check connection first
  checkConnection()
    .then(() => {
      // Load other components after connection check
      generateBriefing();
      loadTasks();
      loadKnowledgeStats();
      loadAnalytics();
    })
    .catch((err) => {
      console.error("Initial connection check failed:", err);
      showNotification("Failed to connect to API. Please check settings.", "error");
    });

  // Auto-refresh certain data
  setInterval(checkConnection, 30000); // Check connection every 30s
  setInterval(loadAnalytics, 60000); // Refresh analytics every minute
});

// ============= API Helper Functions =============
async function apiCall(endpoint, method = "GET", body = null) {
  try {
    const options = {
      method,
      headers: {
        "Content-Type": "application/json",
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(`${API_URL}${endpoint}`, options);

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("API Call Error:", error);
    showNotification("API Error: " + error.message, "error");
    throw error;
  }
}

// ============= Connection Status =============
async function checkConnection() {
  try {
    await apiCall("/health");
    updateConnectionStatus(true);
  } catch {
    updateConnectionStatus(false);
  }
}

function updateConnectionStatus(isConnected) {
  const statusElement = document.getElementById("connectionStatus");
  if (isConnected) {
    statusElement.innerHTML = '<i class="fas fa-circle text-green-400 mr-2"></i>Connected';
    statusElement.title = `Connected to ${API_URL}`;
  } else {
    statusElement.innerHTML = '<i class="fas fa-circle text-red-400 mr-2"></i>Disconnected';
    statusElement.title = `Unable to connect to ${API_URL}`;

    // Show a notification if we lose connection
    if (document.visibilityState === "visible") {
      addChatMessage("Connection to AI service lost. Please check if the API gateway is running.", "assistant", true);
    }
  }
}

// ============= Tab Management =============
function switchTab(tabName) {
  // Hide all tabs
  const tabs = ["chat", "briefing", "tasks", "knowledge", "workflows", "search", "analytics"];
  tabs.forEach((tab) => {
    const element = document.getElementById(`${tab}Tab`);
    if (element) {
      element.classList.add("hidden");
    }
  });

  // Show selected tab
  const selectedTab = document.getElementById(`${tabName}Tab`);
  if (selectedTab) {
    selectedTab.classList.remove("hidden");
  }

  // Update sidebar
  document.querySelectorAll(".sidebar-item").forEach((item) => {
    item.classList.remove("active-tab");
  });
  event.target?.closest(".sidebar-item")?.classList.add("active-tab");

  currentTab = tabName;

  // Load tab-specific data
  if (tabName === "tasks") {
    loadTasks();
  } else if (tabName === "knowledge") {
    loadKnowledgeStats();
  } else if (tabName === "workflows") {
    loadWorkflowHistory();
  } else if (tabName === "analytics") {
    loadAnalytics();
  }
}

// ============= Chat Functions =============
async function sendMessage() {
  const input = document.getElementById("chatInput");
  const message = input.value.trim();

  if (!message) {
    showNotification("Please enter a message", "warning");
    return;
  }

  // Add user message to chat immediately for acknowledgment
  addChatMessage(message, "user");

  // Store the message in history
  chatHistory.push({ role: "user", content: message });

  // Clear input immediately to show we've received it
  input.value = "";
  input.disabled = true; // Disable input while processing

  // Disable send button too
  const sendButton = document.getElementById("sendButton");
  if (sendButton) sendButton.disabled = true;

  // Show typing indicator with a small delay for better UX
  setTimeout(() => {
    const typingId = addTypingIndicator();

    // Send to AI asynchronously
    sendToAI(message, typingId).catch((err) => {
      console.error("Failed to send message:", err);
      removeTypingIndicator(typingId);

      // Re-enable controls
      input.disabled = false;
      const sendButton = document.getElementById("sendButton");
      if (sendButton) sendButton.disabled = false;
      input.focus();
    });
  }, 100);
}

async function sendToAI(message, typingId) {
  const input = document.getElementById("chatInput");
  const sendButton = document.getElementById("sendButton");

  try {
    console.log("Sending message to AI:", message);

    // Send to AI with proper error handling
    const response = await apiCall("/api/ai/chat", "POST", {
      model: DEFAULT_MODEL,
      messages: chatHistory,
      stream: false,
    });

    // Remove typing indicator
    removeTypingIndicator(typingId);

    // Process and display AI response
    if (response && response.message && response.message.content) {
      const aiResponse = response.message.content;
      addChatMessage(aiResponse, "assistant");
      chatHistory.push({ role: "assistant", content: aiResponse });
      console.log("AI response received:", aiResponse);
    } else if (response && response.response) {
      // Handle alternative response format
      const aiResponse = response.response;
      addChatMessage(aiResponse, "assistant");
      chatHistory.push({ role: "assistant", content: aiResponse });
      console.log("AI response received:", aiResponse);
    } else {
      throw new Error("Invalid response format from AI");
    }
  } catch (error) {
    console.error("Error sending message to AI:", error);
    removeTypingIndicator(typingId);

    // Show more detailed error message
    const errorMessage = error.message?.includes("service unavailable")
      ? "The AI service is currently unavailable. Please check if Ollama is running."
      : "Sorry, I encountered an error processing your request. Please try again.";

    addChatMessage(errorMessage, "assistant", true);
  } finally {
    // Re-enable input and send button
    input.disabled = false;
    if (sendButton) sendButton.disabled = false;
    input.focus();
  }
}

function addChatMessage(message, role, isError = false) {
  const messagesContainer = document.getElementById("chatMessages");
  const messageDiv = document.createElement("div");
  messageDiv.className = "message-bubble";

  // Add timestamp
  const timestamp = new Date().toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });

  if (role === "user") {
    messageDiv.innerHTML = `
            <div class="flex items-start space-x-3 justify-end">
                <div class="text-right">
                    <div class="bg-indigo-500 text-white rounded-lg p-3 max-w-md">
                        <p class="text-sm">${escapeHtml(message)}</p>
                    </div>
                    <span class="text-xs text-gray-400 mt-1">${timestamp}</span>
                </div>
                <div class="bg-gray-300 text-gray-700 rounded-full w-8 h-8 flex items-center justify-center">
                    <i class="fas fa-user text-sm"></i>
                </div>
            </div>
        `;
  } else {
    const bgColor = isError ? "bg-red-100" : "bg-gray-100";
    const iconColor = isError ? "bg-red-500" : "bg-indigo-500";
    messageDiv.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="${iconColor} text-white rounded-full w-8 h-8 flex items-center justify-center">
                    <i class="fas ${isError ? "fa-exclamation-triangle" : "fa-robot"} text-sm"></i>
                </div>
                <div>
                    <div class="${bgColor} rounded-lg p-3 max-w-md">
                        <p class="text-sm whitespace-pre-wrap">${escapeHtml(message)}</p>
                    </div>
                    <span class="text-xs text-gray-400 mt-1">${timestamp}</span>
                </div>
            </div>
        `;
  }

  messagesContainer.appendChild(messageDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addTypingIndicator() {
  const messagesContainer = document.getElementById("chatMessages");
  const indicatorId = "typing-" + Date.now();
  const indicatorDiv = document.createElement("div");
  indicatorDiv.id = indicatorId;
  indicatorDiv.className = "message-bubble";
  indicatorDiv.innerHTML = `
        <div class="flex items-start space-x-3">
            <div class="bg-indigo-500 text-white rounded-full w-8 h-8 flex items-center justify-center">
                <i class="fas fa-robot text-sm"></i>
            </div>
            <div class="bg-gray-100 rounded-lg p-3">
                <div class="flex items-center space-x-2">
                    <div class="flex space-x-1">
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                        <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                    </div>
                    <span class="text-xs text-gray-500 ml-2">AI is thinking...</span>
                </div>
            </div>
        </div>
    `;

  messagesContainer.appendChild(indicatorDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  return indicatorId;
}

function removeTypingIndicator(id) {
  const element = document.getElementById(id);
  if (element) {
    element.remove();
  }
}

// ============= Daily Briefing =============
async function generateBriefing() {
  const container = document.getElementById("briefingContent");
  container.innerHTML = `
        <div class="text-center py-12">
            <div class="loader mx-auto mb-4"></div>
            <p class="text-gray-500">Generating your briefing...</p>
        </div>
    `;

  try {
    const response = await apiCall("/api/workflow/execute", "POST", {
      workflow_path: "daily_briefing",
      inputs: {
        user_id: USER_ID,
        include_past_briefings: true,
      },
    });

    // Poll for result
    setTimeout(async () => {
      const briefing = await getBriefingResult(response.job_id);
      displayBriefing(briefing);
    }, 2000);
  } catch (error) {
    container.innerHTML = `
            <div class="text-center py-12 text-red-500">
                <i class="fas fa-exclamation-triangle text-4xl mb-4"></i>
                <p>Failed to generate briefing</p>
            </div>
        `;
  }
}

async function getBriefingResult(jobId) {
  // Mock briefing data for now
  return {
    weather: {
      location: "London",
      temperature: "18°C",
      conditions: "Partly cloudy",
      forecast: "Clear skies expected later",
    },
    news: [
      { category: "Tech", title: "AI Breakthrough Announced", summary: "Major advancement in LLM technology..." },
      { category: "World", title: "Climate Summit Progress", summary: "Nations agree on new targets..." },
      { category: "Business", title: "Market Update", summary: "Stocks rise on positive earnings..." },
    ],
    tasks: [
      { time: "09:00", title: "Team Meeting", priority: "high" },
      { time: "14:00", title: "Project Review", priority: "medium" },
    ],
    ai_insights: "Based on your schedule, consider blocking time for deep work between 10-12. Weather is perfect for an afternoon walk.",
  };
}

function displayBriefing(briefing) {
  const container = document.getElementById("briefingContent");
  container.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Weather -->
            <div class="border rounded-lg p-4">
                <h3 class="font-semibold mb-3 flex items-center">
                    <i class="fas fa-cloud-sun mr-2 text-yellow-500"></i>
                    Weather in ${briefing.weather.location}
                </h3>
                <p class="text-2xl font-bold">${briefing.weather.temperature}</p>
                <p class="text-gray-600">${briefing.weather.conditions}</p>
                <p class="text-sm text-gray-500 mt-2">${briefing.weather.forecast}</p>
            </div>

            <!-- Tasks -->
            <div class="border rounded-lg p-4">
                <h3 class="font-semibold mb-3 flex items-center">
                    <i class="fas fa-tasks mr-2 text-blue-500"></i>
                    Today's Tasks
                </h3>
                ${briefing.tasks
                  .map(
                    (task) => `
                    <div class="flex justify-between items-center py-1">
                        <span class="text-sm">${task.time} - ${task.title}</span>
                        <span class="text-xs px-2 py-1 rounded bg-${task.priority === "high" ? "red" : "yellow"}-100">
                            ${task.priority}
                        </span>
                    </div>
                `,
                  )
                  .join("")}
            </div>
        </div>

        <!-- News -->
        <div class="border rounded-lg p-4 mt-6">
            <h3 class="font-semibold mb-3 flex items-center">
                <i class="fas fa-newspaper mr-2 text-green-500"></i>
                Headlines
            </h3>
            <div class="space-y-3">
                ${briefing.news
                  .map(
                    (item) => `
                    <div class="border-l-3 border-indigo-500 pl-3">
                        <span class="text-xs text-gray-500 uppercase">${item.category}</span>
                        <h4 class="font-medium">${item.title}</h4>
                        <p class="text-sm text-gray-600">${item.summary}</p>
                    </div>
                `,
                  )
                  .join("")}
            </div>
        </div>

        <!-- AI Insights -->
        <div class="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-4 mt-6">
            <h3 class="font-semibold mb-2 flex items-center">
                <i class="fas fa-lightbulb mr-2 text-purple-500"></i>
                AI Insights
            </h3>
            <p class="text-sm">${briefing.ai_insights}</p>
        </div>
    `;
}

// ============= Task Management =============
async function loadTasks() {
  try {
    const response = await apiCall("/api/workflow/execute", "POST", {
      workflow_path: "task_automation",
      inputs: {
        action: "list",
        user_id: USER_ID,
      },
    });

    // Mock tasks for now
    tasks = [
      { id: "1", title: "Review code", status: "todo", priority: "high", due_date: "2024-01-15" },
      { id: "2", title: "Write documentation", status: "in_progress", priority: "medium", due_date: "2024-01-16" },
      { id: "3", title: "Deploy to production", status: "todo", priority: "urgent", due_date: "2024-01-14" },
    ];

    displayTasks(tasks);
  } catch (error) {
    console.error("Failed to load tasks:", error);
  }
}

function displayTasks(taskList) {
  const container = document.getElementById("tasksList");

  if (taskList.length === 0) {
    container.innerHTML = '<p class="text-gray-500 text-center py-8">No tasks found</p>';
    return;
  }

  container.innerHTML = taskList
    .map(
      (task) => `
        <div class="border rounded-lg p-4 hover:shadow-md transition">
            <div class="flex justify-between items-start">
                <div class="flex-1">
                    <h4 class="font-medium">${escapeHtml(task.title)}</h4>
                    <div class="flex items-center space-x-3 mt-2">
                        <span class="text-xs px-2 py-1 rounded bg-${getPriorityColor(task.priority)}-100">
                            ${task.priority}
                        </span>
                        <span class="text-xs px-2 py-1 rounded bg-${getStatusColor(task.status)}-100">
                            ${task.status}
                        </span>
                        <span class="text-xs text-gray-500">
                            <i class="far fa-calendar mr-1"></i>
                            ${formatDate(task.due_date)}
                        </span>
                    </div>
                </div>
                <div class="flex space-x-2">
                    <button onclick="updateTaskStatus('${task.id}')" class="text-blue-500 hover:text-blue-700">
                        <i class="fas fa-check"></i>
                    </button>
                    <button onclick="deleteTask('${task.id}')" class="text-red-500 hover:text-red-700">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `,
    )
    .join("");
}

function filterTasks(status) {
  if (status === "all") {
    displayTasks(tasks);
  } else {
    const filtered = tasks.filter((t) => t.status === status);
    displayTasks(filtered);
  }
}

async function createTask() {
  const title = document.getElementById("taskTitle").value;
  const description = document.getElementById("taskDescription").value;
  const priority = document.getElementById("taskPriority").value;
  const dueDate = document.getElementById("taskDueDate").value;

  if (!title) {
    showNotification("Task title is required", "error");
    return;
  }

  try {
    await apiCall("/api/workflow/execute", "POST", {
      workflow_path: "task_automation",
      inputs: {
        action: "create",
        title,
        description,
        priority,
        due_date: dueDate,
        user_id: USER_ID,
      },
    });

    closeTaskModal();
    loadTasks();
    showNotification("Task created successfully", "success");
  } catch (error) {
    showNotification("Failed to create task", "error");
  }
}

// ============= Knowledge Management =============
async function loadKnowledgeStats() {
  try {
    const response = await apiCall("/api/workflow/execute", "POST", {
      workflow_path: "knowledge_management",
      inputs: {
        action: "stats",
        user_id: USER_ID,
      },
    });

    // Mock stats for now
    knowledgeStats = {
      total_documents: 12,
      total_chunks: 156,
      total_vectors: 156,
      sources: {
        manual: 8,
        web: 4,
      },
    };

    displayKnowledgeStats(knowledgeStats);
  } catch (error) {
    console.error("Failed to load knowledge stats:", error);
  }
}

function displayKnowledgeStats(stats) {
  const container = document.getElementById("knowledgeStats");
  container.innerHTML = `
        <div class="grid grid-cols-4 gap-4 text-center">
            <div>
                <p class="text-2xl font-bold">${stats.total_documents}</p>
                <p class="text-sm text-gray-500">Documents</p>
            </div>
            <div>
                <p class="text-2xl font-bold">${stats.total_chunks}</p>
                <p class="text-sm text-gray-500">Chunks</p>
            </div>
            <div>
                <p class="text-2xl font-bold">${stats.total_vectors}</p>
                <p class="text-sm text-gray-500">Vectors</p>
            </div>
            <div>
                <p class="text-2xl font-bold">${Object.keys(stats.sources).length}</p>
                <p class="text-sm text-gray-500">Sources</p>
            </div>
        </div>
    `;
}

async function searchKnowledge() {
  const query = document.getElementById("knowledgeSearch").value;
  if (!query) return;

  const container = document.getElementById("knowledgeResults");
  container.innerHTML = '<div class="loader mx-auto"></div>';

  try {
    const response = await apiCall("/api/memory/search", "POST", {
      collection: "knowledge_base",
      query,
      limit: 5,
    });

    displayKnowledgeResults(response.result || []);
  } catch (error) {
    container.innerHTML = '<p class="text-red-500">Search failed</p>';
  }
}

function displayKnowledgeResults(results) {
  const container = document.getElementById("knowledgeResults");

  if (results.length === 0) {
    container.innerHTML = '<p class="text-gray-500 text-center">No results found</p>';
    return;
  }

  container.innerHTML = results
    .map(
      (result) => `
        <div class="border rounded-lg p-4">
            <div class="flex justify-between items-start mb-2">
                <h4 class="font-medium">${escapeHtml(result.payload?.title || "Untitled")}</h4>
                <span class="text-xs text-gray-500">Score: ${result.score?.toFixed(2)}</span>
            </div>
            <p class="text-sm text-gray-600">${escapeHtml(result.payload?.content || "")}</p>
            <div class="mt-2 text-xs text-gray-400">
                Source: ${result.payload?.source || "Unknown"}
            </div>
        </div>
    `,
    )
    .join("");
}

async function addDocument() {
  const title = document.getElementById("docTitle").value;
  const content = document.getElementById("docContent").value;
  const source = document.getElementById("docSource").value || "manual";

  if (!title || !content) {
    showNotification("Title and content are required", "error");
    return;
  }

  try {
    await apiCall("/api/memory/store", "POST", {
      collection: "knowledge_base",
      documents: [
        {
          text: content,
          title,
          source,
          metadata: {
            user_id: USER_ID,
            created_at: new Date().toISOString(),
          },
        },
      ],
    });

    closeDocumentModal();
    loadKnowledgeStats();
    showNotification("Document added successfully", "success");
  } catch (error) {
    showNotification("Failed to add document", "error");
  }
}

async function addUrl() {
  const url = document.getElementById("urlInput").value;

  if (!url) {
    showNotification("URL is required", "error");
    return;
  }

  try {
    await apiCall("/api/workflow/execute", "POST", {
      workflow_path: "knowledge_management",
      inputs: {
        action: "ingest_url",
        url,
        user_id: USER_ID,
      },
    });

    closeUrlModal();
    loadKnowledgeStats();
    showNotification("URL content added successfully", "success");
  } catch (error) {
    showNotification("Failed to add URL content", "error");
  }
}

// ============= Workflow Management =============
async function runWorkflow(workflowName) {
  showNotification(`Running ${workflowName} workflow...`, "info");

  try {
    const response = await apiCall("/api/workflow/execute", "POST", {
      workflow_path: workflowName,
      inputs: {
        user_id: USER_ID,
      },
    });

    showNotification(`Workflow ${workflowName} started successfully`, "success");
    loadWorkflowHistory();
  } catch (error) {
    showNotification(`Failed to run workflow: ${workflowName}`, "error");
  }
}

async function loadWorkflowHistory() {
  const container = document.getElementById("workflowHistory");

  // Mock workflow history
  const history = [
    { name: "daily_briefing", status: "completed", time: "2 hours ago" },
    { name: "task_automation", status: "running", time: "30 minutes ago" },
    { name: "knowledge_sync", status: "completed", time: "1 day ago" },
  ];

  container.innerHTML = history
    .map(
      (item) => `
        <div class="flex justify-between items-center p-3 border rounded">
            <div>
                <span class="font-medium">${item.name}</span>
                <span class="text-xs text-gray-500 ml-2">${item.time}</span>
            </div>
            <span class="text-xs px-2 py-1 rounded bg-${item.status === "completed" ? "green" : "yellow"}-100">
                ${item.status}
            </span>
        </div>
    `,
    )
    .join("");
}

// ============= Web Search =============
async function performWebSearch() {
  const query = document.getElementById("webSearchInput").value;
  const category = document.getElementById("searchCategory").value;

  if (!query) return;

  const container = document.getElementById("searchResults");
  container.innerHTML = '<div class="loader mx-auto"></div>';

  try {
    const response = await apiCall(`/api/search?q=${encodeURIComponent(query)}&categories=${category}`);
    displaySearchResults(response.results || []);
  } catch (error) {
    container.innerHTML = '<p class="text-red-500">Search failed</p>';
  }
}

function displaySearchResults(results) {
  const container = document.getElementById("searchResults");

  if (results.length === 0) {
    container.innerHTML = '<p class="text-gray-500 text-center">No results found</p>';
    return;
  }

  container.innerHTML = results
    .map(
      (result) => `
        <div class="border rounded-lg p-4 hover:shadow-md transition">
            <a href="${result.url}" target="_blank" class="text-blue-600 hover:text-blue-800">
                <h4 class="font-medium">${escapeHtml(result.title)}</h4>
            </a>
            <p class="text-sm text-gray-600 mt-1">${escapeHtml(result.content)}</p>
            <div class="mt-2 text-xs text-gray-400">
                ${result.engine} • ${result.url}
            </div>
        </div>
    `,
    )
    .join("");
}

// ============= Analytics =============
async function loadAnalytics() {
  // Mock analytics data
  document.getElementById("totalTasks").textContent = "24";
  document.getElementById("totalDocs").textContent = "12";
  document.getElementById("totalQueries").textContent = "156";
  document.getElementById("totalWorkflows").textContent = "8";

  // Recent activity
  const activityContainer = document.getElementById("recentActivity");
  const activities = [
    { type: "task", action: "created", time: "5 min ago" },
    { type: "query", action: "executed", time: "15 min ago" },
    { type: "document", action: "added", time: "1 hour ago" },
    { type: "workflow", action: "completed", time: "2 hours ago" },
  ];

  activityContainer.innerHTML = activities
    .map(
      (activity) => `
        <div class="flex justify-between items-center py-2 border-b">
            <span class="text-sm">
                <i class="fas fa-${getActivityIcon(activity.type)} mr-2 text-gray-400"></i>
                ${activity.type} ${activity.action}
            </span>
            <span class="text-xs text-gray-500">${activity.time}</span>
        </div>
    `,
    )
    .join("");

  // System health
  const healthContainer = document.getElementById("systemHealth");
  const services = [
    { name: "Ollama", status: "healthy" },
    { name: "Qdrant", status: "healthy" },
    { name: "Redis", status: "healthy" },
    { name: "Windmill", status: "healthy" },
  ];

  healthContainer.innerHTML = services
    .map(
      (service) => `
        <div class="flex justify-between items-center">
            <span class="text-sm">${service.name}</span>
            <span class="flex items-center">
                <i class="fas fa-circle text-${service.status === "healthy" ? "green" : "red"}-400 text-xs mr-1"></i>
                <span class="text-xs text-gray-500">${service.status}</span>
            </span>
        </div>
    `,
    )
    .join("");
}

// ============= Modal Management =============
function openTaskModal() {
  document.getElementById("taskModal").classList.add("active");
}

function closeTaskModal() {
  document.getElementById("taskModal").classList.remove("active");
  // Clear form
  document.getElementById("taskTitle").value = "";
  document.getElementById("taskDescription").value = "";
  document.getElementById("taskPriority").value = "medium";
  document.getElementById("taskDueDate").value = "";
}

function openDocumentModal() {
  document.getElementById("documentModal").classList.add("active");
}

function closeDocumentModal() {
  document.getElementById("documentModal").classList.remove("active");
  // Clear form
  document.getElementById("docTitle").value = "";
  document.getElementById("docContent").value = "";
  document.getElementById("docSource").value = "";
}

function openUrlModal() {
  document.getElementById("urlModal").classList.add("active");
}

function closeUrlModal() {
  document.getElementById("urlModal").classList.remove("active");
  document.getElementById("urlInput").value = "";
}

function openSettings() {
  document.getElementById("settingsModal").classList.add("active");
  // Load current settings
  document.getElementById("apiUrl").value = API_URL;
  document.getElementById("defaultModel").value = DEFAULT_MODEL;
  document.getElementById("userId").value = USER_ID;
}

function closeSettings() {
  document.getElementById("settingsModal").classList.remove("active");
}

function saveSettings() {
  API_URL = document.getElementById("apiUrl").value;
  DEFAULT_MODEL = document.getElementById("defaultModel").value;
  USER_ID = document.getElementById("userId").value;

  // Save to localStorage
  localStorage.setItem("apiUrl", API_URL);
  localStorage.setItem("defaultModel", DEFAULT_MODEL);
  localStorage.setItem("userId", USER_ID);

  closeSettings();
  showNotification("Settings saved", "success");

  // Reload data with new settings
  checkConnection();
  loadTasks();
  loadKnowledgeStats();
}

function loadSettings() {
  // Determine API URL based on environment
  const hostname = window.location.hostname;
  let defaultApiUrl = "http://localhost:3000";

  // If we're on acebuddy.quest domain, use the API subdomain
  if (hostname.includes("acebuddy.quest")) {
    defaultApiUrl = "https://api.acebuddy.quest";
  } else if (hostname !== "localhost" && hostname !== "127.0.0.1") {
    // If on a different host (e.g., local network IP), use the same host
    defaultApiUrl = `http://${hostname}:3000`;
  }

  API_URL = localStorage.getItem("apiUrl") || defaultApiUrl;
  DEFAULT_MODEL = localStorage.getItem("defaultModel") || "llama3.2:1b";
  USER_ID = localStorage.getItem("userId") || "default";
}

// Show notification toast message
function showNotification(message, type = "info") {
  // Create notification element
  const notification = document.createElement("div");
  notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg text-white z-50 ${
    type === "success" ? "bg-green-500" : type === "error" ? "bg-red-500" : type === "warning" ? "bg-yellow-500" : "bg-blue-500"
  } transition-opacity duration-300`;

  notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${
              type === "success"
                ? "fa-check-circle"
                : type === "error"
                  ? "fa-exclamation-circle"
                  : type === "warning"
                    ? "fa-exclamation-triangle"
                    : "fa-info-circle"
            } mr-2"></i>
            <span>${escapeHtml(message)}</span>
        </div>
    `;

  document.body.appendChild(notification);

  // Auto-remove after 3 seconds
  setTimeout(() => {
    notification.style.opacity = "0";
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 300);
  }, 3000);
}

// ============= Helper Functions =============
function escapeHtml(text) {
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}

function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function getPriorityColor(priority) {
  const colors = {
    urgent: "red",
    high: "orange",
    medium: "yellow",
    low: "green",
  };
  return colors[priority] || "gray";
}

function getStatusColor(status) {
  const colors = {
    todo: "blue",
    in_progress: "yellow",
    done: "green",
    cancelled: "gray",
  };
  return colors[status] || "gray";
}

function getActivityIcon(type) {
  const icons = {
    task: "check-square",
    query: "search",
    document: "file-alt",
    workflow: "project-diagram",
    chat: "comments",
    knowledge: "brain",
  };
  return icons[type] || "circle";
}
