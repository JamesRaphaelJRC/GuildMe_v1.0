$(document).ready(() => {
  const socket = io('http://localhost:8000');
  let friend;
  let room;
  let lastVisitedFriend = '';
  let isChatSectionOpen = false;

  $('.chat-section').resizable({
    minWidth: 100,
    minHeight: 100,
    maxWidth: 500,
    maxHeight: 500,
  });

  class helperFunctions {
    static openChatSection() {
      $('.chat-section').show();
      $('.map-section').css('width', '70%');
      isChatSectionOpen = true;
    }

    static closeChatSection() {
      $('.chat-section').hide();
      $('.map-section').css('width', '100%');
      isChatSectionOpen = false;
    }

    static sendMessage(friend, room) {
      const message = $('.message-box').val().trim();
      if (message !== '') {
        socket.emit('newMessage', { message, friend, room });
      }
      $('.message-box').val('');
      // check if friend is in chat
      helperFunctions.friendIsInChat(friend)
        .then((resp) => {
          if (resp.status === false) {
            socket.emit('to reload friendSection', { friend });
          }
        });
      // .catch((err) => {
      // console.log(err);
      // });
    }

    static displayMessage(data) {
      const { message } = data;
      const { sender } = data;
      const chatbox = $('.chats');
      let content;

      if (sender === friend) {
        content = `
        <div class="message friend-chat">${message}</div>
        `;
      } else {
        content = `
        <div class="message user-chat">${message}</div>
        `;
      }
      chatbox.append(content);
      const chatSection = $('.chat-section');
      // const chatContainer = $('.chat-container');
      chatSection.scrollTop(chatSection.prop('scrollHeight'));
      // chatContainer.scrollTop(chatContainer.prop('scrollHeight'));

      chatbox.scrollTop(chatbox.prop('scrollHeight'));
    }

    static getChatsWithFriend(friend) {
      return new Promise((resolve, reject) => {
        $.ajax({
          type: 'POST',
          url: '/api/user/friend/conversation',
          contentType: 'application/json',
          data: JSON.stringify({ friend }),
          dataType: 'json',
          success: (resp) => {
            resolve(resp);
          },
          error: (err) => {
            reject(err);
          },
        });
      });
    }

    static markReceivedMessagesAsRead(messageObj) {
      const readMsgList = [];
      // gets all unread messages where user === the receiver
      Object.entries(messageObj).forEach(([id, msg]) => {
        if (msg.receiver && msg.receiver !== friend && msg.read === false) {
          readMsgList.push(id);
        }
      });

      // send a request to the endpoint to mark the messages as read
      if (readMsgList.length !== 0) {
        $.ajax({
          type: 'POST',
          url: '/api/user/friend/conversation/read',
          contentType: 'application/json',
          data: JSON.stringify({
            messages: readMsgList,
            conversation_id: messageObj.conversation_id,
          }),
          dataType: 'json',
          success: () => {
          },
          error: (err) => { console.log(err); },
        });
      }
    }

    static updateUserChatLocation(friend, status) {
      $.ajax({
        url: '/api/user/isInChat/update',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ friend, status }),
        dataType: 'json',
        success: () => {
          // socket.emit('to reload friendSection', { friend });
        },
        error: (err) => { console.log(err); },
      });
    }

    static friendIsInChat(friend) {
      return new Promise((resolve, reject) => {
        $.ajax({
          type: 'POST',
          url: '/api/user/isInChat',
          contentType: 'application/json',
          data: JSON.stringify({ friend }),
          dataType: 'json',
          success: (resp) => {
            resolve(resp);
          },
          error: (err) => {
            reject(err);
          },
        });
      });
    }

    static reloadFriends() {
      if (isChatSectionOpen === false) {
        lastVisitedFriend = '';
        helperFunctions.updateUserChatLocation(friend, false);
      }

      $.ajax({
        url: '/api/user/friends',
        type: 'GET',
        success(resp) {
          const friendlist = $('.friendlist');
          friendlist.empty(); // Clears the friend-section

          Object.entries(resp).forEach(([, value]) => {
            const { username, avatar } = value;
            const unreadMessages = value.unread_messages;
            const friend = value.username;

            const friendContainer = $('<div>', { class: 'friend-container', 'data-friend': friend });

            let imageThumbnail;
            if (avatar) {
              imageThumbnail = $(`<img class="images avatar" src="static/${avatar}">`);
            } else {
              imageThumbnail = $('<img class="images avatar" src="static/images/icons8-avatar-96.png">');
            }

            friendContainer.append(imageThumbnail);

            const nameDiv = $('<div>', { class: 'name', text: username });
            friendContainer.append(nameDiv);

            if (unreadMessages === true) {
              const unreadChats = $('<div>', { class: 'unread-chats' });
              friendContainer.append(unreadChats);
            }

            friendlist.append(friendContainer);
          });
        },
        error(error) {
          console.log(error);
        },
      });
    }
  }
  helperFunctions.updateUserChatLocation(friend, false);
  helperFunctions.closeChatSection();

  // Event delegation to the .friendlist for the .friend-container elements
  $('.friendlist').on('click', '.friend-container', function () {
    helperFunctions.openChatSection();
    $('#chat').empty(); // clears the chat area
    $('.message-box').val('');

    $(document).on('mouseup', (event) => {
      const isInsideChatSection = $(event.target).closest('.chat-section').length > 0;

      if (!isInsideChatSection && isChatSectionOpen) {
        helperFunctions.closeChatSection();
        helperFunctions.updateUserChatLocation(friend, false);
        lastVisitedFriend = friend;
      }
    });

    // retrieve friend from the friendlist
    friend = $(this).data('friend');
    $('.friend-name').empty();
    $('.friend-name').append(friend); // set friend name to chat header

    // Closes the chatbox
    $(document).on('click', (event) => {
      const chatSection = $('.chat-section')[0]; // Get the raw DOM element
      const friendContainer = $('.friend-container')[0]; // Get the raw DOM element
      // const allNotification = $('.all-notifications')[0];

      // Check if the target is not the above variables
      if (!chatSection.contains(event.target)
          && !friendContainer.contains(event.target)
          && lastVisitedFriend !== friend // incase user clicks from 1 friend to another
          // && !allNotification.contains(event.target)
      ) {
        helperFunctions.closeChatSection();
        // set user is in chat status with friend to false
        helperFunctions.updateUserChatLocation(friend, false);
        lastVisitedFriend = friend;
      }
    });

    // instantiate options for friend
    $('#mySelect').empty();
    $('#mySelect').append('<option style="display: none;"></option>');
    const option = `<option id='to-track' data-friend=${friend}>allow track</option>`;
    $('#mySelect').append(option);
    const disallow = `<option id='disallow-track' data-friend=${friend}>disallow track</option>`;
    $('#mySelect').append(disallow);
    const removeFriend = `<option id='remove-friend' data-friend=${friend}>remove friend</option>`;
    $('#mySelect').append(removeFriend);

    // Keep track of user current chat
    if (friend !== lastVisitedFriend) {
      helperFunctions.updateUserChatLocation(friend, true);
      lastVisitedFriend = friend;
    }

    helperFunctions.getChatsWithFriend(friend)
      .then((resp) => {
        room = resp.conversation_id; // sets the room to be conversation id
        helperFunctions.markReceivedMessagesAsRead(resp);
        socket.emit('to reload userfriendList');

        // User joins the room
        socket.emit('join', { friend, room });
      })
      .catch(() => {
        const message = 'Friend does not exist anymore';
        socket.emit('send error message', { message });
      });

    // Handle sending new message
    $('.message-box').on('keypress', (e) => {
      // checks if the key pressed is enter ( key 13)
      if (e.which === 13) {
        helperFunctions.sendMessage(friend, room);
      }
    });

    $('.typing-container').on('click', '#send-btn', () => {
      helperFunctions.sendMessage(friend, room);
    });
  });

  socket.on('chat', (data) => {
    helperFunctions.displayMessage(data);
  });

  // Loads all previous messages once user joins the room
  socket.on('prevMessages', (messagesDict) => {
    let loaded = false; // Avoids multiple reloading when the friend is clicked multiple times
    const { messages } = messagesDict;
    if (loaded === false) {
      $('.chats').empty();
      Object.entries(messages).forEach(([, value]) => {
        const message = value.content;
        const { sender } = value;
        helperFunctions.displayMessage({ message, sender });
      });
      loaded = true;
    }
  });

  socket.on('reload friend section', () => {
    helperFunctions.reloadFriends();
  });

  socket.on('reload user friend section', () => {
    helperFunctions.reloadFriends();
  });
});
