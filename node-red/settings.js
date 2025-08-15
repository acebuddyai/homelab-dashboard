/**
 * Node-RED Settings File for Homelab AI Assistant
 *
 * This file contains the runtime settings for Node-RED.
 * It defines various configuration options including security,
 * projects, logging, and editor settings.
 *
 * For more information see: https://nodered.org/docs/user-guide/runtime/configuration
 */

module.exports = {
    // Flow file settings
    flowFile: 'flows.json',
    flowFilePretty: true,

    // Credential secret - IMPORTANT: Change this in production!
    // This can be set via NODE_RED_CREDENTIAL_SECRET environment variable
    credentialSecret: process.env.NODE_RED_CREDENTIAL_SECRET || false,

    // User Directory - where flows and credentials are stored
    userDir: '/data',

    // Node-RED server port
    uiPort: process.env.PORT || 1880,

    // API Maximum Request Size
    apiMaxLength: '50mb',

    // Admin Authentication
    // Uncomment and configure to enable authentication
    // adminAuth: {
    //     type: "credentials",
    //     users: [{
    //         username: "admin",
    //         password: "$2b$08$zZWtXTja0fB8GB.2Z8dun.kYJr9m9BJMvVHB.FqG9M1jibQ9Hihze", // password
    //         permissions: "*"
    //     }],
    //     default: {
    //         permissions: "read"
    //     }
    // },

    // HTTP Node Authentication
    // httpNodeAuth: {user:"user",pass:"$2b$08$zZWtXTja0fB8GB.2Z8dun.kYJr9m9BJMvVHB.FqG9M1jibQ9Hihze"},

    // Static content authentication
    // httpStaticAuth: {user:"user",pass:"$2b$08$zZWtXTja0fB8GB.2Z8dun.kYJr9m9BJMvVHB.FqG9M1jibQ9Hihze"},

    // HTTPS Configuration (if needed)
    // https: {
    //     key: require("fs").readFileSync('/data/certificates/node-red-key.pem'),
    //     cert: require("fs").readFileSync('/data/certificates/node-red-cert.pem')
    // },

    // Enable HTTP request node to use proxy
    // httpRequestTimeout: 120000,

    // Logging Configuration
    logging: {
        // Console logging
        console: {
            level: "info",
            metrics: false,
            audit: false
        }
    },

    // Context Storage
    // Store context in filesystem for persistence
    contextStorage: {
        default: {
            module: "memory"
        },
        file: {
            module: "localfilesystem",
            config: {
                dir: "/data/context",
                flushInterval: 30
            }
        }
    },

    // Export settings
    exportGlobalContextKeys: false,

    // External modules settings
    externalModules: {
        autoInstall: false,
        autoInstallRetry: 30,
        palette: {
            allowInstall: true,
            allowUpdate: true,
            allowUpload: true,
            allowList: ['*'],
            denyList: [],
            allowUpdateList: ['*'],
            denyUpdateList: []
        },
        modules: {
            allowInstall: true,
            allowList: [],
            denyList: []
        }
    },

    // Editor Theme Configuration
    editorTheme: {
        page: {
            title: "Node-RED - Homelab AI",
            favicon: "/data/favicon.ico",
            css: "/data/theme.css",
            scripts: []
        },
        header: {
            title: "Node-RED - Homelab AI Assistant",
            image: null,
            url: "https://acebuddy.quest"
        },
        deployButton: {
            type: "simple",
            label: "Deploy",
            icon: "/data/deploy-icon.png"
        },
        menu: {
            "menu-item-help": {
                label: "Node-RED Documentation",
                url: "https://nodered.org/docs/"
            }
        },
        login: {
            image: "/data/login-logo.png"
        },
        logout: {
            redirect: "/"
        },
        palette: {
            allowInstall: true,
            catalogues: [
                'https://catalogue.nodered.org/catalogue.json'
            ],
            theme: [
                {
                    category: "*.label",
                    type: "text",
                    style: {
                        "fill": "#000000"
                    }
                }
            ]
        },
        projects: {
            enabled: process.env.NODE_RED_ENABLE_PROJECTS === "true" || false,
            workflow: {
                mode: "manual"
            }
        },
        theme: "default",
        codeEditor: {
            lib: "monaco",
            options: {
                theme: "vs",
                fontSize: 14,
                fontFamily: "'Cascadia Code', 'Fira Code', 'Consolas', 'Courier New', monospace",
                fontLigatures: true,
                minimap: {
                    enabled: true
                }
            }
        }
    },

    // Function Nodes Configuration
    functionGlobalContext: {
        // Add global libraries/objects available to all function nodes
        // os: require('os'),
        // moment: require('moment')
    },

    // Function node settings
    functionExternalModules: true,
    functionTimeout: 0,

    // Debug node settings
    debugMaxLength: 1000,
    debugUseColors: true,

    // MQTT settings
    mqttReconnectTime: 15000,
    serialReconnectTime: 15000,

    // TCP server settings
    tcpMsgQueueSize: 2000,
    inboundWebSocketTimeout: 5000,

    // WebSocket ping settings
    webSocketNodeVerifyClient: false,

    // UI settings
    ui: {
        path: "/",
        middleware: function(req, res, next) {
            // Custom middleware if needed
            next();
        }
    },

    // Node settings
    nodeMessageBufferMaxLength: 0,

    // Disable tour on first run
    tours: false,

    // API rate limiting
    rateLimit: {
        windowMs: 1000,
        max: 10
    },

    // Health check endpoint
    healthCheck: {
        path: '/health',
        handler: function(req, res) {
            res.send({
                status: 'healthy',
                version: process.env.NODE_RED_VERSION || 'latest',
                timestamp: new Date().toISOString()
            });
        }
    },

    // Custom API endpoints for Homelab integration
    httpAdminMiddleware: function(req, res, next) {
        // Add CORS headers for Homelab services
        res.header("Access-Control-Allow-Origin", "*");
        res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization");
        next();
    },

    // httpNodeMiddleware: function(req, res, next) {
    //     // Custom middleware for HTTP nodes
    //     next();
    // },

    // Enable safe mode to start without flows
    safeMode: process.env.NODE_RED_ENABLE_SAFE_MODE === "true" || false,

    // Disable editor to run in headless mode
    disableEditor: false,

    // HTTP settings
    httpAdminRoot: '/',
    httpNodeRoot: '/',
    httpStatic: '/data/static/',

    // CORS settings
    httpNodeCors: {
        origin: "*",
        methods: "GET,PUT,POST,DELETE"
    },

    // API Security
    apiUserKey: false,

    // Node installation directory
    nodesDir: '/data/nodes',

    // Flow storage API settings
    storageModule: require("./storage"),

    // Execution mode
    runtimeState: {
        enabled: false,
        ui: false
    }
};
