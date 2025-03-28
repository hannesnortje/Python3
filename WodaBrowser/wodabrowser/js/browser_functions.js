(function() {
    // Initialize QWebChannel
    if (typeof qt === 'undefined') {
        window.qt = { webChannelTransport: null };
    }

    function initializeChannel() {
        new QWebChannel(qt.webChannelTransport, function(channel) {
            console.log('QWebChannel initialization started');
            
            // Debug channel objects
            console.log('Available channel objects:', Object.keys(channel.objects));
            
            window.fileSystemHandler = channel.objects.fileSystemHandler;
            window.codeExecutor = channel.objects.codeExecutor;
            
            // Debug FileSystemHandler
            if (window.fileSystemHandler) {
                console.log('FileSystemHandler methods:', Object.getOwnPropertyNames(window.fileSystemHandler));
                console.log('FileSystemHandler signals:', {
                    errorOccurred: typeof window.fileSystemHandler.errorOccurred,
                    fileCreated: typeof window.fileSystemHandler.fileCreated,
                    directoryCreated: typeof window.fileSystemHandler.directoryCreated
                });
            } else {
                console.error('FileSystemHandler not available in channel objects');
            }

            window.createFile = function(filePath, content) {
                console.log('createFile called with:', { filePath, content });
                return new Promise((resolve, reject) => {
                    if (!window.fileSystemHandler) {
                        console.error('FileSystemHandler is not initialized');
                        reject(new Error("FileSystemHandler not initialized"));
                        return;
                    }

                    if (!filePath) {
                        console.error('File path is required');
                        reject(new Error("File path is required"));
                        return;
                    }

                    console.log('Checking signals availability...');
                    const signals = {
                        errorOccurred: window.fileSystemHandler.errorOccurred,
                        fileCreated: window.fileSystemHandler.fileCreated
                    };
                    console.log('Signal objects:', signals);

                    if (!signals.errorOccurred || !signals.fileCreated) {
                        console.error('Required signals not available:', signals);
                        reject(new Error("Required signals are not available"));
                        return;
                    }

                    // Create handlers with debugging
                    const errorHandler = function(error) {
                        console.log('Error handler called:', error);
                        cleanup();
                        reject(new Error(error));
                    };

                    const successHandler = function(path) {
                        console.log('Success handler called:', path);
                        cleanup();
                        resolve(path);
                    };

                    const cleanup = function() {
                        console.log('Cleanup: disconnecting signals');
                        try {
                            signals.errorOccurred.disconnect(errorHandler);
                            signals.fileCreated.disconnect(successHandler);
                        } catch (e) {
                            console.error('Error during signal cleanup:', e);
                        }
                    };

                    try {
                        console.log('Connecting signals...');
                        signals.errorOccurred.connect(errorHandler);
                        signals.fileCreated.connect(successHandler);

                        console.log('Creating file...');
                        window.fileSystemHandler.createFile(filePath, content);
                        
                        // Set timeout
                        setTimeout(() => {
                            console.log('Operation timed out');
                            cleanup();
                            reject(new Error("Operation timed out"));
                        }, 5000);
                    } catch (error) {
                        console.error('Error during file creation:', error);
                        cleanup();
                        reject(new Error(`Failed to create file: ${error.message}`));
                    }
                });
            };

            window.createDirectory = function(dirPath) {
                console.log('createDirectory called with path:', dirPath);
                return new Promise((resolve, reject) => {
                    if (!window.fileSystemHandler) {
                        console.error('FileSystemHandler not initialized');
                        reject(new Error("FileSystemHandler not initialized"));
                        return;
                    }

                    // Debug handler object
                    console.log('FileSystemHandler object:', window.fileSystemHandler);
                    
                    // Verify signal existence
                    const signals = {
                        errorOccurred: window.fileSystemHandler.errorOccurred,
                        directoryCreated: window.fileSystemHandler.directoryCreated
                    };
                    console.log('Signal objects:', signals);

                    if (!signals.errorOccurred || !signals.directoryCreated) {
                        console.error('Required signals not available:', signals);
                        reject(new Error("Required signals not available"));
                        return;
                    }

                    try {
                        // Connect signals first
                        const errorHandler = function(error) {
                            console.log('Error occurred:', error);
                            cleanup();
                            reject(new Error(error));
                        };

                        const successHandler = function(path) {
                            console.log('Directory created:', path);
                            cleanup();
                            resolve(path);
                        };

                        const cleanup = function() {
                            try {
                                console.log('Disconnecting signals');
                                signals.errorOccurred.disconnect(errorHandler);
                                signals.directoryCreated.disconnect(successHandler);
                            } catch (e) {
                                console.warn('Error during cleanup:', e);
                            }
                        };

                        // Connect handlers
                        signals.errorOccurred.connect(errorHandler);
                        signals.directoryCreated.connect(successHandler);

                        // Call the method
                        console.log('Calling createDirectory method');
                        window.fileSystemHandler.createDirectory(dirPath);

                        // Set timeout for operation
                        setTimeout(() => {
                            console.log('Operation timed out');
                            cleanup();
                            reject(new Error("Operation timed out"));
                        }, 5000);

                    } catch (error) {
                        console.error('Error in createDirectory:', error);
                        reject(new Error(`Failed to create directory: ${error.message}`));
                    }
                });
            };

            window.changeFileContent = function(filePath, content) {
                console.log('changeFileContent called', filePath, content);
                return new Promise((resolve, reject) => {
                    if (!filePath) {
                        reject(new Error("File path is required"));
                        return;
                    }

                    let errorHandler = function(error) {
                        window.fileSystemHandler.errorOccurred.disconnect(errorHandler);
                        window.fileSystemHandler.fileChanged.disconnect(successHandler);
                        reject(new Error(error));
                    };

                    let successHandler = function(path) {
                        window.fileSystemHandler.errorOccurred.disconnect(errorHandler);
                        window.fileSystemHandler.fileChanged.disconnect(successHandler);
                        resolve(path);
                    };

                    if (window.fileSystemHandler.errorOccurred && window.fileSystemHandler.fileChanged) {
                        window.fileSystemHandler.errorOccurred.connect(errorHandler);
                        window.fileSystemHandler.fileChanged.connect(successHandler);
                        
                        try {
                            window.fileSystemHandler.changeFileContent(filePath, content);
                        } catch (error) {
                            window.fileSystemHandler.errorOccurred.disconnect(errorHandler);
                            window.fileSystemHandler.fileChanged.disconnect(successHandler);
                            reject(new Error(`Failed to change file content: ${error.message}`));
                        }
                    } else {
                        reject(new Error("Required signals are not available"));
                    }

                    setTimeout(() => {
                        window.fileSystemHandler.errorOccurred.disconnect(errorHandler);
                        window.fileSystemHandler.fileChanged.disconnect(successHandler);
                        reject(new Error("Operation timed out"));
                    }, 5000);
                });
            };

            window.deleteFile = function(filePath) {
                console.log('deleteFile called', filePath);
                return new Promise((resolve, reject) => {
                    if (!filePath) {
                        reject(new Error("File path is required"));
                        return;
                    }

                    let errorHandler = function(error) {
                        window.fileSystemHandler.errorOccurred.disconnect(errorHandler);
                        window.fileSystemHandler.fileDeleted.disconnect(successHandler);
                        reject(new Error(error));
                    };

                    let successHandler = function(path) {
                        window.fileSystemHandler.errorOccurred.disconnect(errorHandler);
                        window.fileSystemHandler.fileDeleted.disconnect(successHandler);
                        resolve(path);
                    };

                    if (window.fileSystemHandler.errorOccurred && window.fileSystemHandler.fileDeleted) {
                        window.fileSystemHandler.errorOccurred.connect(errorHandler);
                        window.fileSystemHandler.fileDeleted.connect(successHandler);
                        
                        try {
                            window.fileSystemHandler.deleteFile(filePath);
                        } catch (error) {
                            window.fileSystemHandler.errorOccurred.disconnect(errorHandler);
                            window.fileSystemHandler.fileDeleted.disconnect(successHandler);
                            reject(new Error(`Failed to delete file: ${error.message}`));
                        }
                    } else {
                        reject(new Error("Required signals are not available"));
                    }

                    setTimeout(() => {
                        window.fileSystemHandler.errorOccurred.disconnect(errorHandler);
                        window.fileSystemHandler.fileDeleted.disconnect(successHandler);
                        reject(new Error("Operation timed out"));
                    }, 5000);
                });
            };

            window.deleteDirectory = function(dirPath) {
                console.log('deleteDirectory called', dirPath);
                return new Promise((resolve, reject) => {
                    if (!dirPath) {
                        reject(new Error("Directory path is required"));
                        return;
                    }

                    let errorHandler = function(error) {
                        window.fileSystemHandler.errorOccurred.disconnect(errorHandler);
                        window.fileSystemHandler.directoryDeleted.disconnect(successHandler);
                        reject(new Error(error));
                    };

                    let successHandler = function(path) {
                        window.fileSystemHandler.errorOccurred.disconnect(errorHandler);
                        window.fileSystemHandler.directoryDeleted.disconnect(successHandler);
                        resolve(path);
                    };

                    if (window.fileSystemHandler.errorOccurred && window.fileSystemHandler.directoryDeleted) {
                        window.fileSystemHandler.errorOccurred.connect(errorHandler);
                        window.fileSystemHandler.directoryDeleted.connect(successHandler);
                        
                        try {
                            window.fileSystemHandler.deleteDirectory(dirPath);
                        } catch (error) {
                            window.fileSystemHandler.errorOccurred.disconnect(errorHandler);
                            window.fileSystemHandler.directoryDeleted.disconnect(successHandler);
                            reject(new Error(`Failed to delete directory: ${error.message}`));
                        }
                    } else {
                        reject(new Error("Required signals are not available"));
                    }

                    setTimeout(() => {
                        window.fileSystemHandler.errorOccurred.disconnect(errorHandler);
                        window.fileSystemHandler.directoryDeleted.disconnect(successHandler);
                        reject(new Error("Operation timed out"));
                    }, 5000);
                });
            };

            window.readFile = function(filePath) {
                console.log('readFile called', filePath);
                return new Promise((resolve, reject) => {
                    window.readFileCallback = (content) => {
                        resolve(content);
                    };
                    window.fileSystemHandler.readFile(filePath);
                });
            };

            window.executePython = function(code) {
                console.log('executePython called', code);
                return new Promise((resolve, reject) => {
                    if (window.codeExecutor && window.codeExecutor.codeResultReady) {
                        window.codeExecutor.codeResultReady.connect((result) => {
                            resolve(result);
                        });
                        window.codeExecutor.executeSignal({type: 'executePython', code: code});
                    } else {
                        reject(new Error("codeExecutor or codeResultReady is not defined"));
                    }
                });
            };

            window.browserAPI = {
                openNewTab: function(url) {
                    if (typeof window.codeExecutor !== 'undefined') {
                        window.codeExecutor.executeSignal(url);
                    }
                },
                
                readFile: function(filePath, callback) {
                    window.readFileCallback = callback;
                    if (typeof window.fileSystemHandler !== 'undefined') {
                        window.fileSystemHandler.readFile(filePath);
                    }
                }
            };

            console.log('File system functions initialization completed');
        });
    }

    // Initialize as soon as possible
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeChannel);
    } else {
        initializeChannel();
    }
})();
