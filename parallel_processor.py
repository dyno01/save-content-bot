# Parallel Processing Module for VJ Save Restricted Content Bot
import asyncio
import os
import time
from typing import List, Dict, Any, Optional
from pyrogram import Client
from pyrogram.types import Message
from config import MAX_CONCURRENT_DOWNLOADS, MAX_CONCURRENT_UPLOADS, PARALLEL_PROCESSING, LOG_CHANNEL, LOG_CHANNEL_USERNAME
from security import security_manager

class ParallelProcessor:
    def __init__(self):
        self.download_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
        self.upload_semaphore = asyncio.Semaphore(MAX_CONCURRENT_UPLOADS)
        self.active_tasks: Dict[int, List[asyncio.Task]] = {}
        
    async def process_batch_parallel(self, client: Client, acc: Client, message: Message, 
                                   from_id: int, to_id: int, chat_type: str, chat_id: str) -> Dict[str, Any]:
        """Process batch downloads/uploads in parallel"""
        if not PARALLEL_PROCESSING:
            return await self._process_sequential(client, acc, message, from_id, to_id, chat_type, chat_id)
        
        user_id = message.from_user.id
        batch_size = to_id - from_id + 1
        
        # Create tasks for parallel processing
        tasks = []
        for msgid in range(from_id, to_id + 1):
            task = asyncio.create_task(
                self._process_single_message(client, acc, message, msgid, chat_type, chat_id)
            )
            tasks.append(task)
        
        # Store active tasks for user
        self.active_tasks[user_id] = tasks
        
        # Process with progress tracking
        results = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'total': batch_size,
            'start_time': time.time()
        }
        
        try:
            # Process tasks in batches to avoid overwhelming the system
            batch_size_limit = min(MAX_CONCURRENT_DOWNLOADS, batch_size)
            
            for i in range(0, len(tasks), batch_size_limit):
                batch_tasks = tasks[i:i + batch_size_limit]
                
                # Wait for batch to complete
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process results
                for result in batch_results:
                    if isinstance(result, Exception):
                        results['failed'] += 1
                        results['errors'].append(str(result))
                    elif result:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                
                # Small delay between batches to prevent rate limiting
                if i + batch_size_limit < len(tasks):
                    await asyncio.sleep(1)
                    
        except Exception as e:
            results['errors'].append(f"Batch processing error: {str(e)}")
        finally:
            # Clean up tasks
            self.active_tasks.pop(user_id, None)
            results['end_time'] = time.time()
            results['duration'] = results['end_time'] - results['start_time']
        
        return results
    
    async def _process_single_message(self, client: Client, acc: Client, message: Message, 
                                    msgid: int, chat_type: str, chat_id: str) -> bool:
        """Process a single message with parallel download/upload"""
        try:
            # Download with semaphore control
            async with self.download_semaphore:
                if chat_type == "private":
                    chatid = int("-100" + chat_id)
                    msg = await acc.get_messages(chatid, msgid)
                elif chat_type == "bot":
                    msg = await acc.get_messages(chat_id, msgid)
                else:  # public
                    msg = await acc.get_messages(chat_id, msgid)
                
                if msg.empty:
                    return False
                
                # Get message type
                msg_type = self._get_message_type(msg)
                if not msg_type:
                    return False
                
                # Handle text messages
                if msg_type == "Text":
                    await self._send_to_log_channel(client, message, msg.text, entities=msg.entities)
                    return True
                
                # Download media
                file_path = await self._download_media(acc, msg, message)
                if not file_path:
                    return False
                
                # Upload with semaphore control
                async with self.upload_semaphore:
                    success = await self._upload_to_log_channel(client, message, file_path, msg, msg_type)
                    
                    # Clean up downloaded file
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    
                    return success
                    
        except Exception as e:
            security_manager.log_security_event(message.from_user.id, "PARALLEL_ERROR", str(e))
            return False
    
    async def _download_media(self, acc: Client, msg: Message, original_message: Message) -> Optional[str]:
        """Download media with progress tracking"""
        try:
            # Create unique filename
            file_id = f"{original_message.id}_{msg.id}_{int(time.time())}"
            file_path = f"downloads/{file_id}"
            
            # Ensure downloads directory exists
            os.makedirs("downloads", exist_ok=True)
            
            # Download with progress
            file_path = await acc.download_media(msg, file_name=file_path)
            return file_path
            
        except Exception as e:
            security_manager.log_security_event(original_message.from_user.id, "DOWNLOAD_ERROR", str(e))
            return None
    
    async def _upload_to_log_channel(self, client: Client, original_message: Message, 
                                   file_path: str, original_msg: Message, msg_type: str) -> bool:
        """Upload to log channel with appropriate message type"""
        try:
            if not LOG_CHANNEL:
                # Fallback to user's chat
                return await self._upload_to_user(client, original_message, file_path, original_msg, msg_type)
            
            # Upload to log channel
            caption = self._create_caption(original_message, original_msg)
            
            if msg_type == "Document":
                await client.send_document(
                    LOG_CHANNEL, 
                    file_path, 
                    caption=caption,
                    parse_mode="html"
                )
            elif msg_type == "Video":
                await client.send_video(
                    LOG_CHANNEL, 
                    file_path, 
                    caption=caption,
                    parse_mode="html"
                )
            elif msg_type == "Photo":
                await client.send_photo(
                    LOG_CHANNEL, 
                    file_path, 
                    caption=caption,
                    parse_mode="html"
                )
            elif msg_type == "Audio":
                await client.send_audio(
                    LOG_CHANNEL, 
                    file_path, 
                    caption=caption,
                    parse_mode="html"
                )
            elif msg_type == "Voice":
                await client.send_voice(
                    LOG_CHANNEL, 
                    file_path, 
                    caption=caption,
                    parse_mode="html"
                )
            elif msg_type == "Animation":
                await client.send_animation(
                    LOG_CHANNEL, 
                    file_path, 
                    caption=caption,
                    parse_mode="html"
                )
            elif msg_type == "Sticker":
                await client.send_sticker(LOG_CHANNEL, file_path)
            
            return True
            
        except Exception as e:
            security_manager.log_security_event(original_message.from_user.id, "UPLOAD_ERROR", str(e))
            return False
    
    async def _upload_to_user(self, client: Client, original_message: Message, 
                            file_path: str, original_msg: Message, msg_type: str) -> bool:
        """Fallback upload to user's chat"""
        try:
            caption = self._create_caption(original_message, original_msg)
            
            if msg_type == "Document":
                await client.send_document(
                    original_message.chat.id, 
                    file_path, 
                    caption=caption,
                    reply_to_message_id=original_message.id,
                    parse_mode="html"
                )
            elif msg_type == "Video":
                await client.send_video(
                    original_message.chat.id, 
                    file_path, 
                    caption=caption,
                    reply_to_message_id=original_message.id,
                    parse_mode="html"
                )
            elif msg_type == "Photo":
                await client.send_photo(
                    original_message.chat.id, 
                    file_path, 
                    caption=caption,
                    reply_to_message_id=original_message.id,
                    parse_mode="html"
                )
            elif msg_type == "Audio":
                await client.send_audio(
                    original_message.chat.id, 
                    file_path, 
                    caption=caption,
                    reply_to_message_id=original_message.id,
                    parse_mode="html"
                )
            elif msg_type == "Voice":
                await client.send_voice(
                    original_message.chat.id, 
                    file_path, 
                    caption=caption,
                    reply_to_message_id=original_message.id,
                    parse_mode="html"
                )
            elif msg_type == "Animation":
                await client.send_animation(
                    original_message.chat.id, 
                    file_path, 
                    caption=caption,
                    reply_to_message_id=original_message.id,
                    parse_mode="html"
                )
            elif msg_type == "Sticker":
                await client.send_sticker(
                    original_message.chat.id, 
                    file_path,
                    reply_to_message_id=original_message.id
                )
            
            return True
            
        except Exception as e:
            security_manager.log_security_event(original_message.from_user.id, "USER_UPLOAD_ERROR", str(e))
            return False
    
    async def _send_to_log_channel(self, client: Client, original_message: Message, 
                                 text: str, entities=None):
        """Send text message to log channel"""
        try:
            if not LOG_CHANNEL:
                # Fallback to user's chat
                await client.send_message(
                    original_message.chat.id,
                    text,
                    entities=entities,
                    reply_to_message_id=original_message.id,
                    parse_mode="html"
                )
                return
            
            # Send to log channel
            caption = f"📝 **Text Message**\n\n{text}\n\n👤 **Requested by:** {original_message.from_user.mention}"
            await client.send_message(LOG_CHANNEL, caption, parse_mode="html")
            
        except Exception as e:
            security_manager.log_security_event(original_message.from_user.id, "TEXT_SEND_ERROR", str(e))
    
    def _create_caption(self, original_message: Message, original_msg: Message) -> str:
        """Create caption for uploaded content"""
        caption_parts = []
        
        # Add original caption if exists
        if original_msg.caption:
            caption_parts.append(f"📄 **Original Caption:**\n{original_msg.caption}")
        
        # Add metadata
        caption_parts.append(f"👤 **Requested by:** {original_message.from_user.mention}")
        caption_parts.append(f"🆔 **User ID:** `{original_message.from_user.id}`")
        caption_parts.append(f"📅 **Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n\n".join(caption_parts)
    
    def _get_message_type(self, msg: Message) -> Optional[str]:
        """Get message type for proper handling"""
        if msg.text:
            return "Text"
        elif msg.document:
            return "Document"
        elif msg.video:
            return "Video"
        elif msg.photo:
            return "Photo"
        elif msg.audio:
            return "Audio"
        elif msg.voice:
            return "Voice"
        elif msg.animation:
            return "Animation"
        elif msg.sticker:
            return "Sticker"
        return None
    
    async def _process_sequential(self, client: Client, acc: Client, message: Message, 
                                from_id: int, to_id: int, chat_type: str, chat_id: str) -> Dict[str, Any]:
        """Fallback sequential processing"""
        results = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'total': to_id - from_id + 1,
            'start_time': time.time()
        }
        
        for msgid in range(from_id, to_id + 1):
            try:
                success = await self._process_single_message(client, acc, message, msgid, chat_type, chat_id)
                if success:
                    results['success'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(str(e))
            
            # Small delay between messages
            await asyncio.sleep(0.5)
        
        results['end_time'] = time.time()
        results['duration'] = results['end_time'] - results['start_time']
        return results
    
    async def cancel_user_tasks(self, user_id: int):
        """Cancel all active tasks for a user"""
        if user_id in self.active_tasks:
            for task in self.active_tasks[user_id]:
                if not task.done():
                    task.cancel()
            self.active_tasks.pop(user_id, None)

# Global parallel processor instance
parallel_processor = ParallelProcessor()
