/**
 * Node-RED Storage Module for Homelab AI Assistant
 *
 * This module provides custom storage implementation for Node-RED flows
 * and credentials. It extends the default file system storage with
 * additional features for the homelab environment.
 */

const fs = require('fs');
const path = require('path');
const util = require('util');

// Promisify fs functions
const readFile = util.promisify(fs.readFile);
const writeFile = util.promisify(fs.writeFile);
const mkdir = util.promisify(fs.mkdir);
const access = util.promisify(fs.access);

// Storage base directory
const BASE_DIR = process.env.NODE_RED_DATA_DIR || '/data';

// Ensure base directory exists
async function ensureDir(dir) {
    try {
        await access(dir);
    } catch (error) {
        await mkdir(dir, { recursive: true });
    }
}

module.exports = {
    init: async function(settings) {
        // Initialize storage
        this.settings = settings;

        // Ensure required directories exist
        await ensureDir(BASE_DIR);
        await ensureDir(path.join(BASE_DIR, 'flows'));
        await ensureDir(path.join(BASE_DIR, 'credentials'));
        await ensureDir(path.join(BASE_DIR, 'context'));
        await ensureDir(path.join(BASE_DIR, 'lib'));
        await ensureDir(path.join(BASE_DIR, 'backup'));

        console.log('Storage module initialized at:', BASE_DIR);
        return Promise.resolve();
    },

    getFlows: async function() {
        try {
            const flowFile = path.join(BASE_DIR, 'flows.json');
            const data = await readFile(flowFile, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            if (error.code === 'ENOENT') {
                // Return empty flows if file doesn't exist
                return [];
            }
            throw error;
        }
    },

    saveFlows: async function(flows) {
        const flowFile = path.join(BASE_DIR, 'flows.json');
        const backupFile = path.join(BASE_DIR, 'backup', `flows_${Date.now()}.json`);

        try {
            // Create backup of existing flows
            try {
                const existing = await readFile(flowFile, 'utf8');
                await writeFile(backupFile, existing);
            } catch (error) {
                // No existing file to backup
            }

            // Save new flows
            const data = JSON.stringify(flows, null, 2);
            await writeFile(flowFile, data, 'utf8');

            console.log('Flows saved successfully');
            return Promise.resolve();
        } catch (error) {
            console.error('Error saving flows:', error);
            throw error;
        }
    },

    getCredentials: async function() {
        try {
            const credFile = path.join(BASE_DIR, 'flows_cred.json');
            const data = await readFile(credFile, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            if (error.code === 'ENOENT') {
                return {};
            }
            throw error;
        }
    },

    saveCredentials: async function(credentials) {
        const credFile = path.join(BASE_DIR, 'flows_cred.json');
        const data = JSON.stringify(credentials, null, 2);
        await writeFile(credFile, data, 'utf8');
        return Promise.resolve();
    },

    getSettings: async function() {
        try {
            const settingsFile = path.join(BASE_DIR, '.config.json');
            const data = await readFile(settingsFile, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            if (error.code === 'ENOENT') {
                return {};
            }
            throw error;
        }
    },

    saveSettings: async function(settings) {
        const settingsFile = path.join(BASE_DIR, '.config.json');
        const data = JSON.stringify(settings, null, 2);
        await writeFile(settingsFile, data, 'utf8');
        return Promise.resolve();
    },

    getSessions: async function() {
        try {
            const sessionsFile = path.join(BASE_DIR, '.sessions.json');
            const data = await readFile(sessionsFile, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            if (error.code === 'ENOENT') {
                return {};
            }
            throw error;
        }
    },

    saveSessions: async function(sessions) {
        const sessionsFile = path.join(BASE_DIR, '.sessions.json');
        const data = JSON.stringify(sessions, null, 2);
        await writeFile(sessionsFile, data, 'utf8');
        return Promise.resolve();
    },

    getLibraryEntry: async function(type, path) {
        const libFile = path.join(BASE_DIR, 'lib', type, path);
        try {
            const data = await readFile(libFile, 'utf8');
            return data;
        } catch (error) {
            if (error.code === 'ENOENT') {
                return null;
            }
            throw error;
        }
    },

    saveLibraryEntry: async function(type, path, meta, body) {
        const libDir = path.join(BASE_DIR, 'lib', type);
        const libFile = path.join(libDir, path);

        await ensureDir(libDir);
        await writeFile(libFile, body, 'utf8');

        if (meta) {
            const metaFile = libFile + '.json';
            await writeFile(metaFile, JSON.stringify(meta, null, 2), 'utf8');
        }

        return Promise.resolve();
    }
};
