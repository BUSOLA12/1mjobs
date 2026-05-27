import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Conversation, Message, UserProfile, MessageNotification
from .serializer import MessageSerializer, UserAvatarSerializer
from users.serializers import ProfileSerializer
from users.models import UserProfile
from users.serializers import ProfileDetailSerializer
import logging
from django.utils.timezone import localtime
from django.conf import settings
from rest_framework.test import APIRequestFactory
from .models import Conversation, Message
from users.models import UserProfile
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist




logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',  # Log messages will be saved to 'app.log'
    filemode='a'  # Append to the log file instead of overwriting
)

logger = logging.getLogger(__name__)



class MessagingConsumer(AsyncWebsocketConsumer):

   async def connect(self):
        
      query_string = self.scope['query_string'].decode()
      params = dict(x.split("=") for x in query_string.split("&") if "=" in x)


      self.user_id = int(params.get("user_id"))
      logger.info(f"user_id: {self.user_id}")
      self.username = f"User{self.user_id}"

      self.user_group_name = f"user_{self.user_id}"

      await self.channel_layer.group_add(
         self.user_group_name,
         self.channel_name
      )

      await self.update_user_status(True)
      await self.join_all_active_conversations()
      await self.accept()
      await self.broadcast_status_change()

   async def disconnect(self, close_code):
      await self.channel_layer.group_discard(
         self.user_group_name,
         self.channel_name
      )
      await self.update_user_status(False)
      await self.broadcast_status_change()

   async def receive(self, text_data):
      try:
         data = json.loads(text_data)
         message_type = data.get('type')

         if message_type == 'send_message':
               await self.handle_send_message(data)
         elif message_type == 'mark_as_read':
               await self.handle_mark_as_read(data)
         elif message_type == 'typing_start':
               await self.handle_typing_status(data, True)
         elif message_type == 'typing_stop':
               await self.handle_typing_status(data, False)
         elif message_type == 'join_conversation':
               await self.handle_join_conversation(data)
         elif message_type == 'leave_conversation':
               await self.handle_leave_conversation(data)
         elif message_type == 'get_all_messages':
               await self.handle_get_messages(data)

      except json.JSONDecodeError:
         await self.send(text_data=json.dumps({'type': 'error', 'message': 'Invalid JSON'}))

   async def handle_get_messages(self, data):
      conversation_id = data.get("conversation_id")
      message_data = await self.get_conv_messages(conversation_id)
      await self.send(text_data=json.dumps({
         'type': 'got_messages',
         'message': message_data
      }))
      
   async def handle_send_message(self, data):
      conversation_id = data.get("conversation_id")
      content = data.get('content', '').strip()
      sender_id = data.get('sender_id')

      is_member = await self.is_participant(conversation_id)
      if not is_member:
         await self.send(text_data=json.dumps({'type': 'error','message': 'Not a participant in this conversation'}))
         return

      if not content or not conversation_id:
         await self.send(text_data=json.dumps({
               'type': 'error',
               'message': 'Content and conversation required'
         }))
         return

      conversation = await self.get_conversation(conversation_id)
      if not conversation:
         await self.send(text_data=json.dumps({
               'type': 'error',
               'message': 'Conversation not found'
         }))
         return

      recipient = await self.get_other_participant(conversation_id)
      if not recipient:
         return

      message = await self.create_message(conversation_id, recipient.id, content)
      message_data = await self.serialize_message(message)
      recipient_avatar = await self.get_user_avatar(recipient.id)
      sender_avatar = await self.get_user_avatar(self.user_id)
      logger.info(f"recipient_avatar: {recipient_avatar}")

      await self.send(text_data=json.dumps({
         'type': 'message_sent',
         'message_data': message_data
      }))

      conversation_group = f"conversation_{conversation_id}"
      await self.channel_layer.group_send(
         conversation_group,
         {
               'type': 'new_message',
               'message': message_data,
               'reciever_avatar': recipient_avatar,
               'sender_avatar': sender_avatar,
               'conversation_id': conversation_id,
               'sender_id': sender_id
         }
      )

   
   async def handle_mark_as_read(self, data):
      conversation_id = data.get("conversation_id")
      if conversation_id:
         await self.mark_messages_as_read(conversation_id)
         other_user = await self.get_other_participant(conversation_id)
         if other_user:
               await self.channel_layer.group_send(
                  f"user_{other_user.id}",
                  {'type': 'messages_read', 'conversation_id': conversation_id, 'reader': self.username}
               )

   async def handle_typing_status(self, data, is_typing):
      conversation_id = data.get('conversation_id')
      if conversation_id:
         other_user = await self.get_other_participant(conversation_id)
         if other_user:
               await self.channel_layer.group_send(
                  f"user_{other_user.id}",
                  {
                     'type': 'typing_status',
                     'conversation_id': conversation_id,
                     'username': self.username,
                     'is_typing': is_typing
                  }
               )

   async def handle_join_conversation(self, data):
      conversation_id = data.get('conversation_id')
      if conversation_id:
         self.conversation_group = f"conversation_{conversation_id}"
         await self.channel_layer.group_add(
               self.conversation_group,
               self.channel_name
         )

   async def handle_leave_conversation(self, data):
      if hasattr(self, 'conversation_group'):
         await self.channel_layer.group_discard(
               self.conversation_group,
               self.channel_name
         )

   async def send_notification(self, event):
      try:
         await self.send(text_data=json.dumps({
             'type': 'send_notification',
             'data': event['data']
            }))

      except Exception as e:
         print("Error in send notification:", e)

   async def refresh_conv(self, event) :
      try:
         await self.send(text_data=json.dumps({
            'type': 'refresh_conv',
            'timestamp': event['timestamp']
         }))

      except Exception as e:
         print("Error in refreshing conversation:", e)
         await self.send(text_data=json.dumps({
               'type': 'error',
               'message': 'Error in refreshing conversation'
         }))
         return

   async def new_message(self, event):
      try:
         await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message'],
            'conversation_id': event['conversation_id'],
            'sender_avatar': event['sender_avatar'],
            'recipient_avatar': event['reciever_avatar'],
            'sender_id': event['sender_id']
         }))
      except Exception as e:
          print("Error in new message:", e)

   async def messages_read(self, event):
      await self.send(text_data=json.dumps({
         'type': 'messages_read',
         'conversation_id': event['conversation_id'],
         'reader': event['reader']
      }))

   async def typing_status(self, event):
      await self.send(text_data=json.dumps({
         'type': 'typing_status',
         'conversation_id': event['conversation_id'],
         'username': event['username'],
         'is_typing': event['is_typing']
      }))

   async def user_status_change(self, event):
      await self.send(text_data=json.dumps({
         'type': 'user_status_change',
         'username': event['username'],
         'is_online': event['is_online'],
         'last_seen': event['last_seen']
      }))

   async def join_all_active_conversations(self):
    conversation_ids = await self.get_user_conversations()
    for conv_id in conversation_ids:
        conversation_group = f"conversation_{conv_id}"
        await self.channel_layer.group_add(
            conversation_group,
            self.channel_name
        )

   @database_sync_to_async
   def get_conversation(self, conversation_id):
      try:
         return Conversation.objects.filter(id=conversation_id).first()
      except:
         return None

   @database_sync_to_async
   def get_user_avatar(self, user_id):
      try:
         profile = UserProfile.objects.select_related('user').get(user__id=user_id)
         if profile.avatar and hasattr(profile.avatar, 'url'):
            return f"{settings.BASE_URL}{profile.avatar.url}"
         return ""
      except UserProfile.DoesNotExist:
         logger.error(f"UserProfile not found for user {user_id}")
         return ""
      except Exception as e:
         logger.error(f"Error getting avatar for user {user_id}: {str(e)}")
         return ""

   @database_sync_to_async
   def get_other_participant(self, conversation_id):
      try:
         conversation = Conversation.objects.get(id=conversation_id)
         return conversation.participants.exclude(id=self.user_id).first()
      except:
         return None

   @database_sync_to_async
   def create_message(self, conversation_id, recipient_id, content):
      from django.contrib.auth import get_user_model
      User = get_user_model()

      conversation = Conversation.objects.get(id=conversation_id)
      recipient = User.objects.get(id=recipient_id)
      sender = User.objects.get(id=self.user_id)

      message = Message.objects.create(
         conversation=conversation,
         sender=sender,
         recipient=recipient,
         content=content
      )

      message.save()

      notification, created = MessageNotification.objects.get_or_create(
         user=sender,
         is_read=False,
         message=message,
         conversation=conversation,
         defaults={'unread_count': 1}
      )
      if not created:
         notification.unread_count += 1
         notification.save()

      return message

   @database_sync_to_async
   def serialize_message(self, message):
      serializer = MessageSerializer(message)
      return serializer.data

   @database_sync_to_async
   def mark_messages_as_read(self, conversation_id):
      Message.objects.filter(
         conversation_id=conversation_id,
         recipient_id=self.user_id,
         is_read=False
      ).update(is_read=True)




   # @database_sync_to_async
   # def get_conv_messages(self, conversation_id):
   #    from django.contrib.sites.models import Site
   #    c = Conversation.objects.get(pk=conversation_id)
      
      
   #    message = Message.objects.filter(conversation=c).order_by("-timestamp")
      
   #    current_site = Site.objects.get_current()
   #    protocol = 'http'
   #    base_url = f"{protocol}://{current_site.domain}"


   #    data = []
   #    for m in message:
   #       try:
   #          sender_details = UserProfile.objects.get(user=m.sender)
   #          recipient_details = UserProfile.objects.get(user=m.recipient)
   #          sender_avatar_url = None
   #          if sender_details.avatar and sender_details.avatar.url:
   #              sender_avatar_url = f"{base_url}{sender_details.avatar.url}"

   #          recipient_avatar_url = None
   #          if recipient_details.avatar and recipient_details.avatar.url:
   #              recipient_avatar_url = f"{base_url}{recipient_details.avatar.url}"


   #          data.append({
   #                "content": m.content,
   #                "sender_id": m.sender.id,
   #                "recipient_id": m.recipient.id,
   #                "timestamp": localtime(m.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
   #                "message_type": m.message_type,
   #                "sender_avatar": sender_avatar_url,
   #                "recipient_avatar": recipient_avatar_url
   #             })
   #       except UserProfile.DoesNotExist:
   #          data.append({
   #              "content": m.content,
   #              "sender_id": m.sender.id,
   #              "recipient_id": m.recipient.id,
   #              "timestamp": localtime(m.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
   #              "message_type": m.message_type,
   #              "sender_avatar": None,
   #              "recipient_avatar": None
   #          })
   #    return data




 
   
   


   @database_sync_to_async
   def get_user_conversations(self):
      return list(
         Conversation.objects.filter(participants__id=self.user_id)
         .values_list('id', flat=True)
      )
   

   @database_sync_to_async
   def get_conv_messages(self, conversation_id):
      """
      Retrieve messages for a conversation with comprehensive error handling.
      
      Args:
         conversation_id: The ID of the conversation to retrieve messages for
         
      Returns:
         list: List of message dictionaries or empty list on error
      """
      try:
         # Validate conversation_id
         if not conversation_id:
               logger.error("get_conv_messages called with empty conversation_id")
               return []
               
         # Get conversation with error handling
         try:
               c = Conversation.objects.get(pk=conversation_id)
               logger.debug(f"Retrieved conversation {conversation_id}")
         except Conversation.DoesNotExist:
               logger.error(f"Conversation with ID {conversation_id} does not exist")
               return []
         except Exception as e:
               logger.error(f"Error retrieving conversation {conversation_id}: {str(e)}")
               return []
         
         # Get messages with error handling
         try:
               messages = Message.objects.filter(conversation=c).order_by("-timestamp")
               logger.debug(f"Found {messages.count()} messages for conversation {conversation_id}")
         except Exception as e:
               logger.error(f"Error retrieving messages for conversation {conversation_id}: {str(e)}")
               return []
         
         # Get current site safely in async consumer
         try:
               # current_site = get_current_site(self.scope)  # works in Channels consumer
               # protocol = 'https'
               base_url = settings.BASE_URL
               logger.debug(f"Using base URL: {base_url}")
         except Exception as e:
               logger.error(f"Error getting current site: {str(e)}")
               base_url = ""
         
         data = []
         for m in messages:
               try:
                  # Validate message object
                  if not hasattr(m, 'sender') or not hasattr(m, 'recipient'):
                     logger.warning(f"Message {m.id if hasattr(m, 'id') else 'unknown'} missing sender or recipient")
                     continue
                  
                  if not m.sender or not m.recipient:
                     logger.warning(f"Message {m.id if hasattr(m, 'id') else 'unknown'} has null sender or recipient")
                     continue
                  
                  # Initialize default values
                  sender_avatar_url = None
                  recipient_avatar_url = None
                  
                  # Get sender profile with error handling
                  try:
                     sender_details = UserProfile.objects.get(user=m.sender)
                     if sender_details.avatar and hasattr(sender_details.avatar, 'url') and sender_details.avatar.url:
                           sender_avatar_url = f"{base_url}{sender_details.avatar.url}"
                  except UserProfile.DoesNotExist:
                     logger.debug(f"UserProfile not found for sender {m.sender.id}")
                  except Exception as e:
                     logger.warning(f"Error getting sender profile for user {m.sender.id}: {str(e)}")
                  
                  # Get recipient profile with error handling
                  try:
                     recipient_details = UserProfile.objects.get(user=m.recipient)
                     if recipient_details.avatar and hasattr(recipient_details.avatar, 'url') and recipient_details.avatar.url:
                           recipient_avatar_url = f"{base_url}{recipient_details.avatar.url}"
                  except UserProfile.DoesNotExist:
                     logger.debug(f"UserProfile not found for recipient {m.recipient.id}")
                  except Exception as e:
                     logger.warning(f"Error getting recipient profile for user {m.recipient.id}: {str(e)}")
                  
                  # Format timestamp with error handling
                  try:
                     formatted_timestamp = localtime(m.timestamp).strftime("%Y-%m-%d %H:%M:%S")
                  except Exception as e:
                     logger.warning(f"Error formatting timestamp for message {m.id}: {str(e)}")
                     formatted_timestamp = str(m.timestamp) if hasattr(m, 'timestamp') else "Unknown"
                  
                  # Build message data
                  message_data = {
                     "content": getattr(m, 'content', ''),
                     "sender_id": m.sender.id if m.sender else None,
                     "recipient_id": m.recipient.id if m.recipient else None,
                     "timestamp": formatted_timestamp,
                     "message_type": getattr(m, 'message_type', ''),
                     "sender_avatar": sender_avatar_url,
                     "recipient_avatar": recipient_avatar_url
                  }
                  
                  data.append(message_data)
                  
               except Exception as e:
                  logger.error(f"Error processing message {getattr(m, 'id', 'unknown')}: {str(e)}")
                  continue
         
         logger.info(f"Successfully processed {len(data)} messages for conversation {conversation_id}")
         return data
         
      except Exception as e:
         logger.error(f"Unexpected error in get_conv_messages for conversation {conversation_id}: {str(e)}")
         return []



   

   


   

   

   

   

   @database_sync_to_async
   def update_user_status(self, is_online):
      try:
         profile, _ = UserProfile.objects.get_or_create(user_id=self.user_id)
         profile.is_online = is_online
         profile.last_seen = timezone.now()
         profile.save()
      except:
         pass

   @database_sync_to_async
   def get_user_contacts(self):
      conversations = Conversation.objects.filter(participants__id=self.user_id)
      contact_ids = []
      for conv in conversations:
         other_user = conv.participants.exclude(id=self.user_id).first()
         if other_user:
               contact_ids.append(other_user.id)
      return contact_ids

   async def broadcast_status_change(self):
      try:
         contact_ids = await self.get_user_contacts()
         profile_data = await self.get_user_profile_data()

         for contact_id in contact_ids:
               await self.channel_layer.group_send(
                  f"user_{contact_id}",
                  {
                     'type': 'user_status_change',
                     'username': self.username,
                     'is_online': profile_data['is_online'],
                     'last_seen': profile_data['last_seen']
                  }
               )
      except:
         pass

   @database_sync_to_async
   def get_user_profile_data(self):
      try:
         profile = UserProfile.objects.get(user_id=self.user_id)
         return {
               'is_online': profile.is_online,
               'last_seen': profile.last_seen.isoformat() if profile.last_seen else None
         }
      except:
         return {'is_online': False, 'last_seen': None}

   @database_sync_to_async
   def is_participant(self, conversation_id):
      try:
         return Conversation.objects.filter(id=conversation_id, participants__id=self.user_id).exists()
      except:
         return False