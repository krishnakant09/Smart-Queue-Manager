import uuid
import logging
from datetime import datetime, timedelta
import json

class QueueManager:
    """
    Manages queue operations using Replit DB for persistence.
    """
    
    def __init__(self, db):
        """
        Initialize QueueManager with a database connection.
        
        Args:
            db: An instance of ReplitDB
        """
        self.db = db
        self.queue_prefix = "queue_item_"
        self.history_key = "queue_history"
        self.stats_key = "queue_statistics"
        
        # Initialize statistics if not exist
        if not self.db.get(self.stats_key):
            self.db.set(self.stats_key, {
                "total_served": 0,
                "avg_wait_time": 0,
                "peak_queue_length": 0,
                "current_queue_length": 0
            })
        
        # Initialize history if not exist
        if not self.db.get(self.history_key):
            self.db.set(self.history_key, [])
    
    def get_all_items(self, queue_prefix=None):
        """
        Get all items in the queue.
        
        Args:
            queue_prefix (str, optional): Prefix for specific business queue
        
        Returns:
            list: List of queue items sorted by priority and timestamp
        """
        items = []
        prefix = queue_prefix if queue_prefix else self.queue_prefix
        all_data = self.db.get_all(prefix)
        
        for key, value in all_data.items():
            if value.get('status') != 'completed':  # Only include active items
                item_id = key.replace(prefix, '')
                value['id'] = item_id
                items.append(value)
        
        # Sort by priority (highest first) and then by timestamp (oldest first)
        return sorted(items, key=lambda x: (-x.get('priority', 0), x.get('timestamp', '')))
    
    def add_item(self, item, queue_prefix=None):
        """
        Add a new item to the queue.
        
        Args:
            item (dict): The queue item to add
            queue_prefix (str, optional): Prefix for specific business queue
        
        Returns:
            str: The ID of the added item
        """
        item_id = str(uuid.uuid4())
        prefix = queue_prefix if queue_prefix else self.queue_prefix
        key = f"{prefix}{item_id}"
        
        self.db.set(key, item)
        
        # Update statistics
        stats_key = f"{queue_prefix}stats" if queue_prefix else self.stats_key
        stats = self.db.get(stats_key, {})
        
        if not stats:
            # Initialize stats if they don't exist
            stats = {
                "total_served": 0,
                "avg_wait_time": 0,
                "peak_queue_length": 0,
                "current_queue_length": 0
            }
        
        current_length = len(self.get_all_items(queue_prefix=queue_prefix))
        stats['current_queue_length'] = current_length
        
        if current_length > stats.get('peak_queue_length', 0):
            stats['peak_queue_length'] = current_length
        
        self.db.set(stats_key, stats)
        
        logging.debug(f"Added item to queue: {item_id}")
        return item_id
    
    def update_item(self, item_id, data):
        """
        Update an existing queue item.
        
        Args:
            item_id (str): The ID of the item to update
            data (dict): The data to update
        
        Returns:
            bool: True if successfully updated, False otherwise
        """
        key = f"{self.queue_prefix}{item_id}"
        existing_item = self.db.get(key)
        
        if not existing_item:
            return False
        
        # Update only provided fields
        for field, value in data.items():
            existing_item[field] = value
        
        self.db.set(key, existing_item)
        logging.debug(f"Updated item in queue: {item_id}")
        return True
    
    def remove_item(self, item_id):
        """
        Remove an item from the queue.
        
        Args:
            item_id (str): The ID of the item to remove
        
        Returns:
            bool: True if successfully removed, False otherwise
        """
        key = f"{self.queue_prefix}{item_id}"
        item = self.db.get(key)
        
        if not item:
            return False
        
        self.db.delete(key)
        
        # Update statistics
        stats = self.db.get(self.stats_key, {})
        stats['current_queue_length'] = len(self.get_all_items())
        self.db.set(self.stats_key, stats)
        
        logging.debug(f"Removed item from queue: {item_id}")
        return True
    
    def complete_item(self, item_id):
        """
        Mark an item as completed and move it to history.
        
        Args:
            item_id (str): The ID of the item to complete
        
        Returns:
            bool: True if successfully completed, False otherwise
        """
        key = f"{self.queue_prefix}{item_id}"
        item = self.db.get(key)
        
        if not item:
            return False
        
        # Mark as completed
        item['status'] = 'completed'
        item['completed_at'] = datetime.now().isoformat()
        self.db.set(key, item)
        
        # Calculate wait time
        try:
            start_time = datetime.fromisoformat(item['timestamp'])
            end_time = datetime.fromisoformat(item['completed_at'])
            wait_time = (end_time - start_time).total_seconds() / 60  # in minutes
            
            # Add to history
            history = self.db.get(self.history_key, [])
            history_item = {
                'id': item_id,
                'name': item.get('name', 'Unknown'),
                'wait_time': wait_time,
                'timestamp': item['timestamp'],
                'completed_at': item['completed_at']
            }
            # Keep only the last 100 items in history
            if len(history) > 100:
                history = history[-99:]
            history.append(history_item)
            self.db.set(self.history_key, history)
            
            # Update statistics
            stats = self.db.get(self.stats_key, {})
            stats['total_served'] = stats.get('total_served', 0) + 1
            stats['current_queue_length'] = len(self.get_all_items())
            
            # Update average wait time
            total_served = stats['total_served']
            current_avg = stats.get('avg_wait_time', 0)
            
            if total_served > 1:
                # Weighted average calculation
                new_avg = (current_avg * (total_served - 1) + wait_time) / total_served
            else:
                new_avg = wait_time
            
            stats['avg_wait_time'] = new_avg
            self.db.set(self.stats_key, stats)
            
        except Exception as e:
            logging.error(f"Error calculating statistics: {e}")
        
        logging.debug(f"Completed item in queue: {item_id}")
        return True
    
    def get_statistics(self, queue_prefix=None):
        """
        Get queue statistics.
        
        Args:
            queue_prefix (str, optional): Prefix for specific business queue
            
        Returns:
            dict: Queue statistics
        """
        stats_key = f"{queue_prefix}stats" if queue_prefix else self.stats_key
        stats = self.db.get(stats_key, {})
        
        if not stats:
            # Initialize stats if they don't exist for this queue
            stats = {
                "total_served": 0,
                "avg_wait_time": 0,
                "peak_queue_length": 0,
                "current_queue_length": 0
            }
            self.db.set(stats_key, stats)
        
        # Update current queue length
        stats['current_queue_length'] = len(self.get_all_items(queue_prefix=queue_prefix))
        
        # Format average wait time for display
        avg_wait_time = stats.get('avg_wait_time', 0)
        if avg_wait_time < 1:
            stats['avg_wait_time_display'] = f"{int(avg_wait_time * 60)} seconds"
        else:
            stats['avg_wait_time_display'] = f"{round(avg_wait_time, 1)} minutes"
        
        return stats
    
    def get_history(self, limit=20):
        """
        Get queue history.
        
        Args:
            limit (int): Maximum number of history items to return
        
        Returns:
            list: Queue history items
        """
        history = self.db.get(self.history_key, [])
        return sorted(history, key=lambda x: x.get('completed_at', ''), reverse=True)[:limit]
    
    def reset_queue(self):
        """
        Reset the entire queue.
        
        Returns:
            bool: True if successful
        """
        # Get all queue items
        all_items = self.db.get_all(self.queue_prefix)
        
        # Delete each item
        for key in all_items.keys():
            self.db.delete(key)
        
        # Reset statistics
        stats = {
            "total_served": 0,
            "avg_wait_time": 0,
            "peak_queue_length": 0,
            "current_queue_length": 0
        }
        self.db.set(self.stats_key, stats)
        
        # Keep history but mark it as a reset point
        history = self.db.get(self.history_key, [])
        history.append({
            'id': 'reset',
            'name': 'Queue Reset',
            'timestamp': datetime.now().isoformat()
        })
        self.db.set(self.history_key, history)
        
        logging.debug("Queue has been reset")
        return True
