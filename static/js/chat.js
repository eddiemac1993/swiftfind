// static/js/chat.js
class ChatApp {
    constructor() {
        this.conversationId = document.body.dataset.conversationId;
        this.userId = document.body.dataset.userId;
        this.socket = null;
        this.notificationSocket = null;
        this.initialize();
    }

    initialize() {
        this.setupWebSockets();
        this.setupEventListeners();
        this.requestNotificationPermission();
    }

    setupWebSockets() {
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        
        // Main chat socket
        this.socket = new WebSocket(
            `${protocol}${window.location.host}/ws/messaging/${this.conversationId}/`
        );
        
        // Notification socket
        this.notificationSocket = new WebSocket(
            `${protocol}${window.location.host}/ws/notifications/${this.userId}/`
        );

        this.socket.onmessage = (e) => this.handleSocketMessage(e);
        this.notificationSocket.onmessage = (e) => this.handleNotification(e);
    }

    handleSocketMessage(event) {
        const data = JSON.parse(event.data);
        
        switch(data.type) {
            case 'chat_message':
                this.appendMessage(data);
                break;
            case 'read_receipt':
                this.updateMessageStatus(data.message_id);
                break;
        }
    }

    handleNotification(event) {
        const data = JSON.parse(event.data);
        
        if (data.type === 'notification') {
            this.updateNotificationBadge();
            
            if (!this.isCurrentConversation(data.conversation_id)) {
                this.showDesktopNotification(data);
            }
        }
    }

    appendMessage(data) {
        const messagesContainer = document.querySelector('.messages-container');
        const messageElement = this.createMessageElement(data);
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    createMessageElement(data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${data.sender_id === this.userId ? 'sent' : 'received'}`;
        messageDiv.dataset.messageId = data.message_id;
        
        messageDiv.innerHTML = `
            <div class="message-content">${data.content}</div>
            <div class="message-meta">
                <span class="timestamp">${new Date(data.timestamp).toLocaleTimeString()}</span>
                ${data.sender_id === this.userId ? '<span class="status"></span>' : ''}
            </div>
        `;
        
        return messageDiv;
    }

    updateNotificationBadge() {
        fetch('/messaging/unread_count/')
            .then(response => response.json())
            .then(data => {
                const badge = document.getElementById('notification-badge');
                badge.textContent = data.count > 0 ? data.count : '';
                badge.style.display = data.count > 0 ? 'inline-block' : 'none';
            });
    }

    showDesktopNotification(data) {
        if (Notification.permission === 'granted') {
            const notification = new Notification(
                `New message from ${data.sender_username}`, 
                {
                    body: data.preview,
                    icon: '/static/images/logo.png',
                    data: { url: `/messaging/${data.conversation_id}/` }
                }
            );
            
            notification.onclick = (e) => {
                window.location.href = e.target.data.url;
            };
        }
    }

    requestNotificationPermission() {
        if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
            Notification.requestPermission();
        }
    }

    isCurrentConversation(conversationId) {
        return conversationId === this.conversationId;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.body.dataset.conversationId) {
        new ChatApp();
    }
});