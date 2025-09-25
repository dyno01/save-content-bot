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
                                   from_id: int, to_id: int, chat_type: str, chat_id: str, 
                                   progress_msg: Message = None) -> Dict[str, Any]:
        """Process batch downloads/uploads in parallel with real-time progress"""
        if not PARALLEL_PROCESSING:
            return await self._process_sequential(client, acc, message, from_id, to_id, chat_type, chat_id)
        
        user_id = message.from_user.id
        batch_size = to_id - from_id + 1
        
        # Progress tracking
        progress_tracker = {
            'completed': 0,
            'failed': 0,
            'current_files': {},
            'start_time': time.time(),
            'total_size': 0,
            'downloaded_size': 0
        }
        
        # Create tasks for parallel processing
        tasks = []
        for msgid in range(from_id, to_id + 1):
            task = asyncio.create_task(
                self._process_single_message_with_progress(
                    client, acc, message, msgid, chat_type, chat_id, progress_tracker, progress_msg
                )
            )
            tasks.append(task)
        
        # Store active tasks for user
        self.active_tasks[user_id] = tasks
        
        # Start progress monitoring task
        progress_task = asyncio.create_task(
            self._update_progress(client, progress_msg, progress_tracker, batch_size)
        )
        
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
                for i, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        error_msg = f"Task {i}: {str(result)}"
                        results['failed'] += 1
                        results['errors'].append(error_msg)
                        print(f"DEBUG: {error_msg}")  # Console logging
                    elif result:
                        results['success'] += 1
                    else:
                        error_msg = f"Task {i}: Unknown failure"
                        results['failed'] += 1
                        results['errors'].append(error_msg)
                        print(f"DEBUG: {error_msg}")  # Console logging
                
                # Small delay between batches to prevent rate limiting
                if i + batch_size_limit < len(tasks):
                    await asyncio.sleep(1)
                    
        except Exception as e:
            results['errors'].append(f"Batch processing error: {str(e)}")
        finally:
            # Cancel progress monitoring
            progress_task.cancel()
            # Clean up tasks
            self.active_tasks.pop(user_id, None)
            results['end_time'] = time.time()
            results['duration'] = results['end_time'] - results['start_time']
        
        return results
    
    async def _process_single_message_with_progress(self, client: Client, acc: Client, message: Message, 
                                                  msgid: int, chat_type: str, chat_id: str, 
                                                  progress_tracker: dict, progress_msg: Message) -> bool:
        """Process a single message with detailed progress tracking"""
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
                    progress_tracker['failed'] += 1
                    return False
                
                # Get message type and size
                msg_type = self._get_message_type(msg)
                if not msg_type:
                    progress_tracker['failed'] += 1
                    return False
                
                # Update progress tracker
                file_key = f"msg_{msgid}"
                progress_tracker['current_files'][file_key] = {
                    'status': 'downloading',
                    'type': msg_type,
                    'size': self._get_file_size(msg),
                    'downloaded': 0,
                    'start_time': time.time()
                }
                
                # Handle text messages
                if msg_type == "Text":
                    progress_tracker['current_files'][file_key]['status'] = 'uploading'
                    await self._send_to_log_channel(client, message, msg.text, entities=msg.entities)
                    progress_tracker['current_files'][file_key]['status'] = 'completed'
                    progress_tracker['completed'] += 1
                    return True
                
                # Download media with progress
                file_path = await self._download_media_with_progress(acc, msg, message, progress_tracker, file_key)
                if not file_path:
                    error_msg = f"Failed to download {file_type} from message {msgid}"
                    progress_tracker['current_files'][file_key]['status'] = 'failed'
                    progress_tracker['current_files'][file_key]['error'] = error_msg
                    progress_tracker['failed'] += 1
                    
                    # Send immediate error notification
                    try:
                        await client.send_message(
                            message.from_user.id,
                            f"❌ **{error_msg}**",
                            parse_mode="HTML"
                        )
                    except:
                        pass
                    return False
                
                # Upload with semaphore control
                async with self.upload_semaphore:
                    progress_tracker['current_files'][file_key]['status'] = 'uploading'
                    success = await self._upload_to_user_chat(client, message, file_path, msg, msg_type)
                    
                    # Clean up downloaded file
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    
                    if success:
                        progress_tracker['current_files'][file_key]['status'] = 'completed'
                        progress_tracker['completed'] += 1
                    else:
                        error_msg = f"Failed to upload {file_type} to your chat"
                        progress_tracker['current_files'][file_key]['status'] = 'failed'
                        progress_tracker['current_files'][file_key]['error'] = error_msg
                        progress_tracker['failed'] += 1
                        
                        # Send immediate error notification
                        try:
                            await client.send_message(
                                message.from_user.id,
                                f"❌ **{error_msg}**",
                                parse_mode="HTML"
                            )
                        except:
                            pass
                    
                    return success
                    
        except Exception as e:
            error_msg = f"Error processing message {msgid}: {str(e)}"
            security_manager.log_security_event(message.from_user.id, "PARALLEL_ERROR", error_msg)
            print(f"DEBUG: {error_msg}")  # Console logging for debugging
            
            # Send error message directly to user
            try:
                await client.send_message(
                    message.from_user.id,
                    f"❌ **Error processing message {msgid}:**\n`{str(e)}`",
                    parse_mode="HTML"
                )
            except:
                pass  # Ignore if can't send error message
            
            if file_key in progress_tracker['current_files']:
                progress_tracker['current_files'][file_key]['status'] = 'failed'
                progress_tracker['current_files'][file_key]['error'] = str(e)
            progress_tracker['failed'] += 1
            return False
    
    async def _update_progress(self, client: Client, progress_msg: Message, 
                             progress_tracker: dict, total_files: int):
        """Update progress message in real-time"""
        try:
            while True:
                await asyncio.sleep(2)  # Update every 2 seconds
                
                current_time = time.time()
                elapsed_time = current_time - progress_tracker['start_time']
                
                # Calculate speeds and progress
                completed = progress_tracker['completed']
                failed = progress_tracker['failed']
                in_progress = len([f for f in progress_tracker['current_files'].values() 
                                 if f['status'] in ['downloading', 'uploading']])
                
                # Calculate overall speed
                total_processed = completed + failed
                speed = total_processed / elapsed_time if elapsed_time > 0 else 0
                
                # Create detailed progress message
                progress_text = f"""
🚀 **Real-Time Processing Progress**

📊 **Overall Progress:**
• **Completed:** {completed}/{total_files} ✅
• **Failed:** {failed} ❌
• **In Progress:** {in_progress} ⏳
• **Speed:** {speed:.2f} files/sec
• **Elapsed:** {elapsed_time:.1f}s

⚡ **Current Operations:**
"""
                
                # Add current file details
                for file_key, file_info in progress_tracker['current_files'].items():
                    if file_info['status'] in ['downloading', 'uploading']:
                        file_elapsed = current_time - file_info['start_time']
                        file_speed = file_info['downloaded'] / file_elapsed if file_elapsed > 0 else 0
                        
                        status_emoji = "⬇️" if file_info['status'] == 'downloading' else "⬆️"
                        size_info = f"({self._format_size(file_info['size'])})" if file_info['size'] > 0 else ""
                        
                        progress_text += f"• {status_emoji} {file_info['type']} {size_info} - {file_speed:.1f} KB/s\n"
                    elif file_info['status'] == 'failed':
                        error_info = file_info.get('error', 'Unknown error')
                        progress_text += f"• ❌ {file_info['type']} - {error_info}\n"
                
                # Add mode and target info
                progress_text += f"""
🎯 **Target:** Your Chat
⚡ **Mode:** {'Parallel Processing' if PARALLEL_PROCESSING else 'Sequential Processing'}
"""
                
                # Update progress message
                try:
                    await progress_msg.edit_text(progress_text)
                except:
                    pass  # Ignore edit errors
                    
        except asyncio.CancelledError:
            pass  # Expected when task is cancelled
    
    def _get_file_size(self, msg: Message) -> int:
        """Get file size from message"""
        try:
            if msg.document:
                return msg.document.file_size or 0
            elif msg.video:
                return msg.video.file_size or 0
            elif msg.audio:
                return msg.audio.file_size or 0
            elif msg.voice:
                return msg.voice.file_size or 0
            elif msg.photo:
                return msg.photo.file_size or 0
            return 0
        except:
            return 0
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    async def _download_media_with_progress(self, acc: Client, msg: Message, 
                                          original_message: Message, progress_tracker: dict, 
                                          file_key: str) -> Optional[str]:
        """Download media with progress tracking"""
        try:
            # Create unique filename
            file_id = f"{original_message.id}_{msg.id}_{int(time.time())}"
            file_path = f"downloads/{file_id}"
            
            # Ensure downloads directory exists
            os.makedirs("downloads", exist_ok=True)
            
            # Download with progress callback
            def progress_callback(current, total):
                if file_key in progress_tracker['current_files']:
                    progress_tracker['current_files'][file_key]['downloaded'] = current
                    progress_tracker['downloaded_size'] += current
            
            file_path = await acc.download_media(msg, file_name=file_path, progress=progress_callback)
            return file_path
            
        except Exception as e:
            security_manager.log_security_event(original_message.from_user.id, "DOWNLOAD_ERROR", str(e))
            return None
    
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
                    parse_mode="HTML"
                )
            elif msg_type == "Video":
                await client.send_video(
                    LOG_CHANNEL, 
                    file_path, 
                    caption=caption,
                    parse_mode="HTML"
                )
            elif msg_type == "Photo":
                await client.send_photo(
                    LOG_CHANNEL, 
                    file_path, 
                    caption=caption,
                    parse_mode="HTML"
                )
            elif msg_type == "Audio":
                await client.send_audio(
                    LOG_CHANNEL, 
                    file_path, 
                    caption=caption,
                    parse_mode="HTML"
                )
            elif msg_type == "Voice":
                await client.send_voice(
                    LOG_CHANNEL, 
                    file_path, 
                    caption=caption,
                    parse_mode="HTML"
                )
            elif msg_type == "Animation":
                await client.send_animation(
                    LOG_CHANNEL, 
                    file_path, 
                    caption=caption,
                    parse_mode="HTML"
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
                    parse_mode="HTML"
                )
            elif msg_type == "Video":
                await client.send_video(
                    original_message.chat.id, 
                    file_path, 
                    caption=caption,
                    reply_to_message_id=original_message.id,
                    parse_mode="HTML"
                )
            elif msg_type == "Photo":
                await client.send_photo(
                    original_message.chat.id, 
                    file_path, 
                    caption=caption,
                    reply_to_message_id=original_message.id,
                    parse_mode="HTML"
                )
            elif msg_type == "Audio":
                await client.send_audio(
                    original_message.chat.id, 
                    file_path, 
                    caption=caption,
                    reply_to_message_id=original_message.id,
                    parse_mode="HTML"
                )
            elif msg_type == "Voice":
                await client.send_voice(
                    original_message.chat.id, 
                    file_path, 
                    caption=caption,
                    reply_to_message_id=original_message.id,
                    parse_mode="HTML"
                )
            elif msg_type == "Animation":
                await client.send_animation(
                    original_message.chat.id, 
                    file_path, 
                    caption=caption,
                    reply_to_message_id=original_message.id,
                    parse_mode="HTML"
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
                    parse_mode="HTML"
                )
                return
            
            # Send to log channel
            caption = f"📝 **Text Message**\n\n{text}\n\n👤 **Requested by:** {original_message.from_user.mention}"
            await client.send_message(LOG_CHANNEL, caption, parse_mode="HTML")
            
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
