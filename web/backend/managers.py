from uuid import uuid4
import logging
import threading
import time
from datetime import datetime, timedelta
from conversation import Conversation

# Set up logging
logger = logging.getLogger(__name__)

class ConversationManager:
    """
    Manages all active conversation sessions in memory.
    """
    def __init__(self):
        self._conversations = {}
        self._lock = threading.RLock()
        self._last_cleanup = time.time()
        logger.info("ConversationManager initialized")

    def create_conversation(self):
        """
        Creates a new Conversation, stores it, and returns its ID.
        
        Returns:
            str: The conversation ID
        """
        conv = Conversation()
        with self._lock:
            self._conversations[conv.id] = conv
            logger.info(f"Created conversation: {conv.id}. Total conversations: {len(self._conversations)}")
        return conv.id

    def get_conversation(self, conversation_id):
        """
        Retrieves a conversation by its ID.
        
        Args:
            conversation_id (str): The UUID of the conversation.
            
        Returns:
            Conversation: The Conversation object, or None if not found.
        """
        self._cleanup_old_conversations()
        
        with self._lock:
            conv = self._conversations.get(conversation_id)
            if not conv:
                logger.warning(f"WARNING: Conversation {conversation_id} not found")
            return conv

    def get_conversation_count(self):
        """Get the total number of active conversations."""
        with self._lock:
            return len(self._conversations)

    def cleanup_conversation(self, conversation_id):
        """Remove a conversation from memory (for future use)."""
        with self._lock:
            if conversation_id in self._conversations:
                del self._conversations[conversation_id]
                logger.info(f"Cleaned up conversation: {conversation_id}")

    def _cleanup_old_conversations(self):
        """Clean up conversations older than configured timeout."""
        current_time = time.time()
        if current_time - self._last_cleanup < 3600:  # Only cleanup every hour
            return
        
        self._last_cleanup = current_time
        
        # Make cleanup timeout configurable (default 7 days instead of 24 hours)
        import os
        cleanup_hours = int(os.getenv('CONVERSATION_CLEANUP_HOURS', '168'))  # 168 = 7 days
        cutoff_time = datetime.now() - timedelta(hours=cleanup_hours)
        
        with self._lock:
            to_delete = []
            for conv_id, conv in self._conversations.items():
                # Check if conversation has created_at timestamp and is old enough
                if hasattr(conv, 'created_at') and conv.created_at < cutoff_time:
                    to_delete.append(conv_id)
            
            for conv_id in to_delete:
                del self._conversations[conv_id]
                logger.info(f"Auto-cleaned expired conversation: {conv_id} (older than {cleanup_hours} hours)")
            
            if to_delete:
                logger.info(f"Cleaned up {len(to_delete)} expired conversations (cleanup threshold: {cleanup_hours} hours)")
            else:
                logger.debug(f"No conversations to cleanup (threshold: {cleanup_hours} hours)")

# Global instance of the manager
conversation_manager = ConversationManager() 