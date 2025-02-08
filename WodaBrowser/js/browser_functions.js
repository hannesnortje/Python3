(function() {
    // Initialize QWebChannel
    if (typeof qt === 'undefined') {
        window.qt = { webChannelTransport: null };
    }

    function initializeChannel() {
        new QWebChannel(qt.webChannelTransport, function(channel) {
            window.fileSystemHandler = channel.objects.fileSystemHandler;
            window.codeExecutor = channel.objects.codeExecutor;
            
            // Define and attach functions to window object immediately
            window.createFile = function(filePath, content) {
                console.log('createFile called', filePath, content);
                window.fileSystemHandler.createFile(filePath, content);
            };

            window.createDirectory = function(dirPath) {
                console.log('createDirectory called', dirPath);
                window.fileSystemHandler.createDirectory(dirPath);
            };

            window.changeFileContent = function(filePath, content) {
                console.log('changeFileContent called', filePath, content);
                window.fileSystemHandler.changeFileContent(filePath, content);
            };

            window.deleteFile = function(filePath) {
                console.log('deleteFile called', filePath);
                window.fileSystemHandler.deleteFile(filePath);
            };

            window.deleteDirectory = function(dirPath) {
                console.log('deleteDirectory called', dirPath);
                window.fileSystemHandler.deleteDirectory(dirPath);
            };

            window.readFile = function(filePath) {
                console.log('readFile called', filePath);
                window.fileSystemHandler.readFile(filePath);
            };

            console.log('File system functions initialized and attached to window object');
        });
    }

    // Initialize as soon as possible
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeChannel);
    } else {
        initializeChannel();
    }
})();
