
// Inject this patch before the main browser_functions.js script
(function() {
    /**
     * This patch supports the enhanced signal handling system.
     * It creates proper signal objects on FileSystemHandler when 
     * they're not available directly.
     */
    window._patchFileSystemHandler = function(handler) {
        if (!handler) return;
        
        console.log("Patching FileSystemHandler signals");
        
        // Fix missing signals
        const signalNames = [
            'fileRead', 'fileCreated', 'fileChanged', 'fileDeleted',
            'directoryCreated', 'directoryDeleted', 'errorOccurred'
        ];
        
        signalNames.forEach(signalName => {
            if (typeof handler[signalName] === 'undefined') {
                console.log(`Creating proxy signal for ${signalName}`);
                
                // Create a signal object
                handler[signalName] = {
                    _callbacks: [],
                    
                    connect: function(callback) {
                        console.log(`Connecting callback to ${signalName}`);
                        this._callbacks.push(callback);
                        return true;
                    },
                    
                    disconnect: function(callback) {
                        console.log(`Disconnecting callback from ${signalName}`);
                        const index = this._callbacks.indexOf(callback);
                        if (index !== -1) {
                            this._callbacks.splice(index, 1);
                            return true;
                        }
                        return false;
                    },
                    
                    emit: function(...args) {
                        console.log(`Emitting ${signalName} with args:`, args);
                        this._callbacks.forEach(cb => {
                            try {
                                cb(...args);
                            } catch (e) {
                                console.error("Error in signal callback:", e);
                            }
                        });
                    }
                };
                
                // If signal handler exists for this signal
                const handlerId = `${handler.__id__}_${signalName}`;
                const signalHandler = channel.objects[handlerId];
                
                if (signalHandler && signalHandler.signalFired) {
                    console.log(`Found signal handler for ${signalName}`);
                    signalHandler.signalFired.connect(function(args) {
                        console.log(`Signal fired: ${signalName} with args:`, args);
                        if (Array.isArray(args)) {
                            handler[signalName].emit(...args);
                        } else {
                            handler[signalName].emit(args);
                        }
                    });
                }
            }
        });
        
        return handler;
    };
    
    // Original initialization function
    const originalInitializeChannel = window.initializeChannel;
    
    // Override the initialization function
    window.initializeChannel = function() {
        new QWebChannel(qt.webChannelTransport, function(channel) {
            console.log('Enhanced QWebChannel initialization started');
            
            // Make channel globally available
            window.channel = channel;
            
            // Debug channel objects
            console.log('Available channel objects:', Object.keys(channel.objects));
            
            // Get handlers from channel
            window.fileSystemHandler = channel.objects.fileSystemHandler;
            window.codeExecutor = channel.objects.codeExecutor;
            
            // Patch with enhanced signal support
            if (window.fileSystemHandler) {
                window._patchFileSystemHandler(window.fileSystemHandler);
            }
            
            // Continue with original initialization
            if (originalInitializeChannel) {
                originalInitializeChannel.call(window, channel);
            }
        });
    };
})();
