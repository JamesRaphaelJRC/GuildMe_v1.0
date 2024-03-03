/* eslint-disable no-restricted-globals */
// eslint-disable-next-line no-unused-vars
function resetSelect() {
  // Set the first option as selected after a user makes a selection
  document.getElementById('mySelect').selectedIndex = 0;
}

function loadFriends(data) {
  $('.friendlist').empty(); // clears the list first
  const friendlist = $('.friendlist');
  Object.entries(data).forEach(([, value]) => {
    const { username } = value;
    const friend = value.username;
    // const unreadMessages = value.unread_messages; remove now let setinterval load unread messages
    const { avatar } = value;
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
    // if (unreadMessages === true) {
    //   const unreadChats = $('<div>', { class: 'unread-chats' });
    //   friendContainer.append(unreadChats);
    // }
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
  let loadedUserProfile = false;
  const socket = io('http://localhost:8000');

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
        // location.reload();
        socket.emit('reload profile', { friend });
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
        // location.reload();
        socket.emit('reload profile', { friend });
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
        success(resp) {
          // should emit reload_friends
          const friendId = resp.friend_id;
          // send friend id to delete conversation obj if both user and friend are no longer friends
          socket.emit('verify to delete', { friend_id: friendId });
        },
      });
    }
  });

  function updateUserProfile() {
    if (loadedUserProfile === false) {
    // send a GET request to get friends the user granted allow_track permission
      $.ajax({
        type: 'GET',
        url: '/api/user/friends/tracking_me',
        contentType: 'application/json',
        success(resp) {
          const { friends } = resp;
          $('#tracking-me').empty(); // empty before refilling
          if (Object.keys(friends).length > 0) {
            const displayContainer = $('#tracking-me');
            Object.entries(friends).forEach(([, friend]) => {
              const miniBox = `
            <div class="mini-box">
              <img class="images avatar" src="static/${friend.avatar}">
              <div class="who-tracks-me">${friend.username}</div>
            </div>
            `;
              displayContainer.append(miniBox);
            });
          } else {
            const displayContainer = $('#tracking-me');
            const noFriend = '<div class="fade">You have permitted no one to view your location</div>';
            displayContainer.append(noFriend);
          }
        },
        error(err) {
          console.log(err);
        },
      });

      // send GET request to get friends that granted user allow_track permission
      $.ajax({
        type: 'GET',
        url: '/api/user/friends/allow_track',
        contentType: 'application/json',
        success(resp) {
          $('#i-can-track').empty();
          const { friends } = resp;
          if (Object.keys(friends).length > 0) {
            const displayContainer = $('#i-can-track');
            Object.entries(friends).forEach(([, friend]) => {
              const miniBox = `
            <div class="mini-box">
              <img class="images avatar" src="static/${friend.avatar}">
              <div class="who-tracks-me">${friend.username}</div>
            </div>
            `;
              displayContainer.append(miniBox);
            });
          } else {
            const displayContainer = $('#i-can-track');
            const noFriend = '<div class="fade">No one has currently permitted you to access their location</div>';
            displayContainer.append(noFriend);
          }
        },
        error(err) {
          console.log(err);
        },
      });
      loadedUserProfile = true;
    }
  }

  // Handle user search
  $('#searchbox').on('input', function () {
    // checks if the key pressed is enter ( key 13)
    const query = $(this).val().trim();

    if (query.length === 0) {
      reloadFriends();
    } else {
      $.ajax({
        type: 'POST',
        url: '/api/user/friends/search',
        contentType: 'application/json',
        data: JSON.stringify({ query }),
        dataType: 'json',
        success(response) {
          loadFriends(response);
        },
        error(err) {
          console.log(err);
        },
      });
    }
  });

  // action when avatar is clicked
  $('#profile-pic').on('click', () => {
    updateUserProfile();
  });

  socket.on('profile reload', () => {
    loadedUserProfile = false;
    updateUserProfile();
  });
});
