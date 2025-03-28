
/**
 * Signal debugging and patching utility for WodaBrowser.
 * This script provides manual signal connection capabilities when normal
 * signal binding fails.
 */
(function() {
    // Store for all signal callbacks
    window._signalCallbacks = {};
    
    // Wait for window.fileSystemHandler to be available
    function waitForFileSystemHandler() {
        if (window.fileSystemHandler) {
            patchSignals();
        } else {
            setTimeout(waitForFileSystemHandler, 100);
        }
    }
    
    // Patch all signals
    function patchSignals() {
        console.log("Patching FileSystemHandler signals");
        const handler = window.fileSystemHandler;
        
        // Create signal handling system
        window._signalSystem = {
            registerCallback: function(signalName, callback) {
                if (!window._signalCallbacks[signalName]) {
                    window._signalCallbacks[signalName] = [];
                }
                window._signalCallbacks[signalName].push(callback);
                return callback; // Return the callback for later removal
            },
            
            removeCallback: function(signalName, callback) {
                if (window._signalCallbacks[signalName]) {
                    const index = window._signalCallbacks[signalName].indexOf(callback);
                    if (index !== -1) {
                        window._signalCallbacks[signalName].splice(index, 1);
                    }
                }
            },
            
            emitSignal: function(signalName, ...args) {
                console.log(`Emitting signal ${signalName} with args:`, args);
                if (window._signalCallbacks[signalName]) {
                    window._signalCallbacks[signalName].forEach(callback => {
                        try {
                            callback(...args);
                        } catch (e) {
                            console.error(`Error in signal ${signalName} callback:`, e);
                        }
                    });
                }
            }
        };
        
        // List of signals to patch
        const signals = [
            'fileRead', 'fileCreated', 'fileChanged', 'fileDeleted',
            'directoryCreated', 'directoryDeleted', 'errorOccurred'
        ];
        
        // Create fake signal objects
        signals.forEach(signalName => {
            // Create a signal object if it doesn't exist
            if (!handler[signalName]) {
                handler[signalName] = {
                    connect: function(callback) {
                        console.log(`Connecting callback to ${signalName}`);
                        return window._signalSystem.registerCallback(signalName, callback);
                    },
                    disconnect: function(callback) {
                        console.log(`Disconnecting callback from ${signalName}`);
                        window._signalSystem.removeCallback(signalName, callback);
                    }
                };
            }
        });
        
        // Override FileSystemHandler methods to manually emit signals
        const originalCreateFile = handler.createFile;
        handler.createFile = function(path, content) {
            console.log("Intercept createFile:", path);
            
            // Call original method
            originalCreateFile.call(handler, path, content);
            
            // Manually emit success signal after a delay
            setTimeout(() => {
                window._signalSystem.emitSignal('fileCreated', path);
            }, 500);
        };
        
        const originalCreateDirectory = handler.createDirectory;
        handler.createDirectory = function(path) {
            console.log("Intercept createDirectory:", path);
            
            // Call original method
            originalCreateDirectory.call(handler, path);
            
            // Manually emit success signal after a delay
            setTimeout(() => {
                window._signalSystem.emitSignal('directoryCreated', path);
            }, 500);
        };
        
        const originalChangeFileContent = handler.changeFileContent;
        handler.changeFileContent = function(path, content) {
            console.log("Intercept changeFileContent:", path);
            
            // Call original method
            originalChangeFileContent.call(handler, path, content);
            
            // Manually emit success signal after a delay
            setTimeout(() => {
                window._signalSystem.emitSignal('fileChanged', path);
            }, 500);
        };
        
        const originalDeleteFile = handler.deleteFile;
        handler.deleteFile = function(path) {
            console.log("Intercept deleteFile:", path);
            
            // Call original method
            originalDeleteFile.call(handler, path);
            
            // Manually emit success signal after a delay
            setTimeout(() => {
                window._signalSystem.emitSignal('fileDeleted', path);
            }, 500);
        };
        
        const originalDeleteDirectory = handler.deleteDirectory;
        handler.deleteDirectory = function(path) {
            console.log("Intercept deleteDirectory:", path);
            
            // Call original method
            originalDeleteDirectory.call(handler, path);
            
            // Manually emit success signal after a delay
            setTimeout(() => {
                window._signalSystem.emitSignal('directoryDeleted', path);
            }, 500);
        };
        
        console.log("Signal patching complete");
    }

    // Start waiting for FileSystemHandler
    waitForFileSystemHandler();
})();
