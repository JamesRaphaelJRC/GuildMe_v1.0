#!/usr/bin/env python3
''' Redis Database module '''
import redis
import os
from datetime import datetime
from typing import List, Union, Dict
import json
from backend.db_ops import db


DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def is_str_and_not_None(variables: List) -> bool:
    ''' Verifies if variables are None or not a string
    Return:
        True if list of variables are all not None and of type string
        False otherwise
    '''
    return all(var is not None and isinstance(var, str) for var in variables)


def calc_days_diff(date_str: str) -> int:
    ''' calculates the days difference between two datetimes '''
    date_obj = datetime.strptime(date_str, DATETIME_FORMAT)
    current_date = datetime.now()
    difference = current_date - date_obj
    return difference.days


class RedisClient:
    ''' Redis client database operations '''
    def __init__(self) -> None:
        ''' Instantiatiate a new RedisClient '''
        # redis_url =  os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        # self._redis_client = redis.StrictRedis.from_url(
        #     redis_url, decode_responses=True)
        host = os.environ.get('REDIS_HOST')
        port = os.environ.get('REDIS_PORT')
        password = os.environ.get('REDIS_PASSWORD')
        self._redis_client = (host, port, password)

    def new_notification(self, sender_id: str, receiver_id: str, message: str,
                         not_type: str, read=False) ->\
            Union[Dict[str, str] | None | bool]:
        ''' Creates a new notification and saves to the redis database
        Return:
            The notification data on success,
            None if credentials are not strings
            False if notification already exists
        '''

        if not is_str_and_not_None([sender_id, receiver_id,
                                    message, not_type]):
            return None

        # it is the receivers notifications not the senders
        notification_key = f"notifications:{receiver_id}"
        sender = db.find_user_by(id=sender_id)
        sender_name = sender.username
        sender_avatar = sender.avatar
        receiver_name = db.find_user_by(id=receiver_id).username

        existing_notifications = self._redis_client.hgetall(notification_key)
        for existing_data_json in existing_notifications.values():
            existing_data = json.loads(existing_data_json)
            if (existing_data["from"] == sender_name and
                    existing_data["to"] == receiver_name and
                    existing_data["message"] == message and
                    existing_data['type'] == not_type and
                    existing_data['type'] != 'general'):  # exclude generals
                return False

        notification_id = str(self._redis_client.hlen(notification_key) + 1)
        data = {
            "from": sender_name,
            "to": receiver_name,
            "date": datetime.now().strftime(DATETIME_FORMAT),
            "read": read,
            "message": message,
            "type": not_type,
            "avatar": sender_avatar
        }

        data_json = json.dumps(data)

        self._redis_client.hset(notification_key, notification_id, data_json)

        return self._redis_client.hget(notification_key, notification_id)

    def mark_as_read(self, user_id: str, notification_id: str)\
            -> Union[bool | None]:
        ''' Mark a notification of a given user as read
        Return:
            Notification id on suces, None otherwise
        '''
        if not is_str_and_not_None([user_id]):
            return None
        not_key = f"notifications:{user_id}"

        if self._redis_client.hexists(not_key, notification_id):
            notification = self._redis_client.hget(not_key, notification_id)
            # deserializes the notification and update the read value to true
            not_dict = json.loads(notification)
            not_dict['read'] = True

            # serializes it back and replace the old data in the database
            not_json = json.dumps(not_dict)
            self._redis_client.hset(not_key, notification_id, not_json)
            return True
        return False

    def get_read_notifications(self, user_id: str) ->\
            Union[Dict[str, any] | None]:
        ''' Returns all read notifications of a given user '''
        if not is_str_and_not_None([user_id]):
            return None
        not_key = f"notifications:{user_id}"
        seriaized_notifications = self._redis_client.hgetall(not_key)

        # deserializes all key/value pairs
        all_notifications = {
            json.loads(not_id): json.loads(not_data)
            for not_id, not_data in seriaized_notifications.items()
            }

        # filtering read location
        read_notifications = {not_id: not_data for not_id, not_data in
                              all_notifications.items()
                              if not_data.get('read') is True}

        return read_notifications

    def get_unread_notifications(self, user_id: str) ->\
            Union[Dict[str, any] | None]:
        ''' Returns all unread notifications of a given user '''
        if not is_str_and_not_None([user_id]):
            return None
        not_key = f"notifications:{user_id}"
        seriaized_notifications = self._redis_client.hgetall(not_key)

        # deserializes all key/value pairs
        all_notifications = {
            json.loads(not_id): json.loads(not_data)
            for not_id, not_data in seriaized_notifications.items()
            }

        # filtering read location
        unread_notifications = {
            not_id: not_data for not_id, not_data in
            all_notifications.items() if not_data.get('read') is False
            }

        return unread_notifications

    def get_friend_requests(self, user_id: str) ->\
            Union[Dict[str, any] | None]:
        ''' Gets all friend request of a given user_id
        Return:
            Friend requests (dict) on success, None otherwise
        '''
        not_key = f"notifications:{user_id}"
        seriaized_notifications = self._redis_client.hgetall(not_key)

        # deserializes all key/value pairs
        all_notifications = {
            json.loads(not_id): json.loads(not_data)
            for not_id, not_data in seriaized_notifications.items()
            }

        # Filter friend requests
        friend_requests = {
            not_id: not_data for not_id, not_data
            in all_notifications.items()
            if not_data.get('type') == 'friend request'
            }
        return friend_requests

    def get_general_notifications(self, user_id: str) ->\
            Union[Dict[str, any] | None]:
        ''' Gets all notifications of a given user_id that are not friend
            requests
        Return:
            general notifications (dict) on success format {id1: data1, ...}
            None otherwise
        '''
        not_key = f"notifications:{user_id}"
        seriaized_notifications = self._redis_client.hgetall(not_key)

        # deserializes all key/value pairs
        all_notifications = {
            json.loads(not_id): json.loads(not_data)
            for not_id, not_data in seriaized_notifications.items()
            }

        general_nots = {
            not_id: not_data for not_id, not_data in
            all_notifications.items() if
            not_data.get('type') != 'friend request'
            }
        return general_nots

    def delete_read_notifications_older_than(self, user_id: str,
                                             days_threshold: int = 30)\
            -> Union[bool | None]:
        ''' Remove all read notifications that are not friend requests '''
        if not is_str_and_not_None([user_id]):
            return None

        read_notifications = self.get_read_notifications(user_id)
        if not read_notifications:
            return None
        notification_key = f"notifications:{user_id}"

        # Gets a list of all read notification ids > days_threshold
        ids_gt_threshold = [
            not_id for not_id, not_data in read_notifications.items()
            if 'date' in not_data and calc_days_diff(not_data['date'])
            > days_threshold
        ]
        if ids_gt_threshold:
            self._redis_client.hdel(notification_key, *ids_gt_threshold)
            return True
        return None

    def delete_notification(self, user_id: str, notification_id: str)\
            -> Union[bool | None]:
        ''' Deletes a user notification with a given id
        Return:
            True on success, False otherwise
        '''
        if not is_str_and_not_None([user_id, notification_id]):
            return None

        notification_key = f"notifications:{user_id}"

        num_del = self._redis_client.hdel(notification_key, notification_id)
        if num_del > 0:
            return True
        return False

    def delete_all_notifications(self, user_id: str) -> bool:
        ''' Deletes all notifications for a given user '''
        if not is_str_and_not_None([user_id]):
            return False

        notification_key = f"notifications:{user_id}"
        print('entered to delere')

        return self._redis_client.delete(notification_key) > 0
