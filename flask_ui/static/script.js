// DOM Elements
const chatDisplay = document.getElementById("chat-display");
const userInput = document.getElementById("user-input");
const sendButton = document.getElementById("send-button");

// Add Message to Chat Display
function addMessage(content, sender) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${sender}`;
    bubble.textContent = content;
    chatDisplay.appendChild(bubble);
    chatDisplay.scrollTop = chatDisplay.scrollHeight; // Auto-scroll
}

// Handle Send Button
async function handleSendMessage() {
    const message = userInput.value.trim();
    if (message) {
        addMessage(message, "user");

        // Send message to Flask server for Rasa response
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });

        const data = await response.json();
        const botMessage = data.response || "Sorry, I couldn't understand that.";
        setTimeout(() => addMessage(botMessage, "bot"), 500); // Simulated delay
        userInput.value = "";
    }
}

// Event Listeners
sendButton.addEventListener("click", handleSendMessage);
userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        handleSendMessage();
        e.preventDefault();
    }
});
