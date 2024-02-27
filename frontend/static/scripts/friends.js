/* eslint-disable no-restricted-globals */
// eslint-disable-next-line no-unused-vars
function resetSelect() {
  // Set the first option as selected after a user makes a selection
  document.getElementById('mySelect').selectedIndex = 0;
}

function loadFriends(data) {
  const friendlist = $('.friendlist');
  Object.entries(data).forEach(([, value]) => {
    const { username } = value;
    const friend = value.username;
    const unreadMessages = value.unread_messages;
    const { avatar } = value;
    const friendContainer = $('<div>', { class: 'friend-container', 'data-friend': friend });
    const imageThumbnail = $(`<img class="images avatar" src="static/${avatar}">`);
    friendContainer.append(imageThumbnail);
    const nameDiv = $('<div>', { class: 'name', text: username });
    friendContainer.append(nameDiv);
    if (unreadMessages === true) {
      const unreadChats = $('<div>', { class: 'unread-chats' });
      friendContainer.append(unreadChats);
    }
    friendlist.append(friendContainer);
  });
}

function reloadFriends() {
  $(document).ready(() => {
    $.ajax({
      url: '/api/user/friends',
      type: 'GET',
      success(resp) {
        loadFriends(resp);
      },
      error(error) { console.log(error); },
    });
  });
}

reloadFriends();

// AJAX operations
$(document).ready(() => {
  const socket = io();

  // sends an ajax post request when a user friend request is accepted
  $('.lower').on('click', '.accept', function () {
    const friend = $(this).data('friend');
    const id = $(this).data('id');
    const idStr = parseInt(id, 10).toString();
    $.ajax({
      type: 'POST',
      url: '/api/user/friends/new',
      contentType: 'application/json',
      data: JSON.stringify({ friend }),
      dataType: 'json',
      success() {
        socket.emit('accepted_request', { friend, id: idStr });
      },
    });
  });

  $('.lower').on('click', '.decline', function () {
    const id = $(this).data('id');
    socket.emit('delete friend request', { id });
    location.reload();
  });

  // Handle user preferences
  $('.options').on('click', '#to-track', function () {
    const friend = $(this).data('friend');
    $.ajax({
      type: 'POST',
      url: '/api/user/friends/allow_track',
      contentType: 'application/json',
      data: JSON.stringify({ friend }),
      dataType: 'json',
      success: () => {
        socket.emit('allowed track', { friend });
      },
      error: (err) => {
        console.log(err);
      },
    });
  });

  $('.options').on('click', '#disallow-track', function () {
    const friend = $(this).data('friend');
    $.ajax({
      type: 'POST',
      url: '/api/user/friends/disallow_track',
      contentType: 'application/json',
      data: JSON.stringify({ friend }),
      dataType: 'json',
      success: () => {
        socket.emit('disallowed track', { friend });
      },
      error: () => {
      },
    });
  });

  $('.options').on('click', '#remove-friend', function () {
    const friend = $(this).data('friend');
    // eslint-disable-next-line no-restricted-globals, no-alert
    const confirmed = confirm(`Are you sure you want to remove ${friend}?`);
    if (confirmed) {
      $.ajax({
        type: 'DELETE',
        url: '/api/user/friends/remove',
        contentType: 'application/json',
        data: JSON.stringify({ friend }),
        dataType: 'json',
        success() {
          // should emit reload_friends
          socket.emit('verify to delete', { friend });
        },
      });
    }
  });
});
