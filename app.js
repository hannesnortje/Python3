// Initialize CodeMirror editors
const leftEditor = CodeMirror.fromTextArea(document.getElementById('leftEditor'), {
    lineNumbers: true,
    mode: "javascript"
});
const rightEditor = CodeMirror.fromTextArea(document.getElementById('rightEditor'), {
    lineNumbers: true,
    mode: "javascript"
});

// Handle input field interactions
document.getElementById('inputField').addEventListener('keyup', async function(event) {
    if (event.key === 'Enter') {
        const input = event.target.value;
        event.target.value = ''; // Clear input field

        // Call ChatGPT API (mock function here, replace with actual API call)
        const response = await mockChatGPT(input, leftEditor.getValue());
        leftEditor.setValue(response);
        
        // Update right editor with the new code
        rightEditor.setValue(transformCode(response));

        // Save the code snippets to the application store
        saveToStore('leftEditorContent', response);
        saveToStore('rightEditorContent', rightEditor.getValue());
    }
});

// Mock function to simulate ChatGPT API call
async function mockChatGPT(input, context) {
    // Replace with actual API call
    return context + '\n// ' + input;
}

// Function to transform code from the left editor to the right editor
function transformCode(code) {
    // Your transformation logic here
    return code;
}

// Function to save content to localStorage
function saveToStore(key, content) {
    localStorage.setItem(key, content);
}

// Function to sync data to local file system (example using File System Access API)
async function syncToLocalFolder() {
    const options = {
        types: [{
            description: 'Text Files',
            accept: {
                'text/plain': ['.txt'],
            },
        }],
    };
    const handle = await window.showSaveFilePicker(options);
    const writable = await handle.createWritable();
    await writable.write(leftEditor.getValue());
    await writable.close();
}
