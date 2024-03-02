$(document).ready(() => {
  const socket = io();
  let loadedFriendRequests = false;

  class Helpers {
    static ringNotificationBell() {
      $('#notification').css('background-image', 'url(static/images/icons8-bell.gif)');
    }

    static stopNotificationBell() {
      $('#notification').css('background-image', 'url(static/images/icons8-notification-96.png)');
    }

    static loadGeneralNotifications() {
      $('.friend-req-box').hide();
      $('.gen-msgs').show();
      $('#friend-requests').css('background-color', 'rgb(240, 236, 236, 0.1)');
      $('#gen-notifications').css('background-color', 'rgb(145, 134, 245)');

      socket.emit('get_general_notifications');
      socket.on('show_general_notifications', (resp) => {
        const generalNotifications = resp.data;
        const generalNotificationDiv = $('.gen-msgs');
        const genMessage = $('.gen-message');
        // const notificationBox = $('.notification-box');

        if (Object.keys(generalNotifications).length === 0) {
          genMessage.text('You have no notification yet');
        } else {
          $('.gen-msgs').empty();

          Object.entries(generalNotifications).forEach(([id, notification]) => {
            const { date } = notification;
            const { message } = notification;
            let not;
            const idStr = parseInt(id, 10).toString();
            if (notification.read === true) {
              not = `<div class="gen-message" data-id=${idStr} style="color: rgb(80, 74, 74)">${message} : ${date}</div>`;
            } else {
              not = `<div class="gen-message" data-id=${idStr}">${message} : ${date}</div>`;
            }
            generalNotificationDiv.append(not);
            generalNotificationDiv.scrollTop(generalNotificationDiv.prop('scrollHeight'));
          });
        }
      });
    }

    static loadFriendRequests() {
      if (loadedFriendRequests === false) {
        socket.emit('get_friend_requests');
        socket.on('user_friend_requests', (resp) => {
          const allReqs = resp.data;
          if (Object.keys(allReqs).length === 0) {
            $('.friend-req-box').text('You have no friend request at this moment');
            $('.friend-req-box').css('border-bottom', '1px solid gray');
          } else {
            Object.entries(allReqs).forEach(([id, request]) => {
              const { date } = request;
              const { from } = request;
              const { avatar } = request;
              const upper = $('.upper');

              let avatarThumb;
              if (avatar) {
                avatarThumb = `<img class="images avatar" src="static/${avatar}" alt="User Avatar">`;
              } else {
                avatarThumb = '<img class="images avatar" src="static/images/icons8-avatar-96.png" alt="User Avatar">';
              }
              upper.append(avatarThumb);

              const friendInfo = `
              <div class="friend-info" data-id=${id}><strong>${from}</strong><br>${date}</div>`;
              upper.append(friendInfo);

              $('.friend-req-box').css('height', '70px'); // reset the height

              const lower = $('.lower');
              const decline = `<div class="mid-btn decline" data-friend=${from} data-id=${id}>decline</div>`;
              const accept = `<div class="mid-btn accept" data-friend=${from} data-id=${id}>accept</div>`;

              lower.append(decline);
              lower.append(accept);
            });
          }
          loadedFriendRequests = true;
        });
      }
    }
  }

  // Handles user click on add friend icon
  $('#add-friend-box').on('click', '#add-icon', (event) => {
    $('#add-friend-input').show();
    event.stopPropagation();

    $('#add-friend-input').on('keypress', (e) => {
      if (e.which === 13) {
        const userInput = $('#add-friend-input').val().trim();
        socket.emit('new_friend_request', { data: userInput });
      }
    });

    $('.label-btn').on('click', () => {
      const userInput = $('#add-friend-input').val().trim();
      socket.emit('new_friend_request', { data: userInput });
    });

    // Closes the add-friend-input box
    $(document).on('click', (event) => {
      const addIcon = $('#add-icon')[0]; // Get the raw DOM element
      const addFriendInput = $('#add-friend-input')[0]; // Get the raw DOM element
      // Check if the target is not #add-icon, its descendant, or #add-friend-input
      if (!addIcon.contains(event.target) && !addFriendInput.contains(event.target)) {
        $('#add-friend-input').hide();
      }
    });
  });

  // Handle actions when user clicks on the notification bell icon
  $('#notification').on('click', (event) => {
    $('.pprofile-container').hide();
    $('.profile-container').hide();
    Helpers.stopNotificationBell();
    $('.notification-box').show();
    event.stopPropagation();
    Helpers.loadGeneralNotifications();

    // Closes the notification box when other parts of the document is clicked on
    $(document).on('click', (event) => {
      const generalNotificationButton = $('#gen-notifications')[0]; // Get the raw DOM element
      const friendRequestButton = $('#friend-requests')[0]; // Get the raw DOM element
      const allNotification = $('.all-notifications')[0];

      // Check if the target is not the above variables
      if (!generalNotificationButton.contains(event.target)
          && !friendRequestButton.contains(event.target)
          && !allNotification.contains(event.target)) {
        $('.notification-box').hide();
      }
    });

    $('#gen-notifications').on('click', () => {
      $('#friend-requests').css('background-color', 'rgb(240, 236, 236, 0.1)');
      $('#gen-notifications').css('background-color', 'rgb(145, 134, 245)');
      Helpers.loadGeneralNotifications();
    });

    $('#friend-requests').on('click', () => {
      $('.gen-msgs').hide();
      $('.friend-req-box').show();
      $('#gen-notifications').css('background-color', 'rgb(240, 236, 236, 0.1)');
      $('#friend-requests').css('background-color', 'rgb(145, 134, 245)');
      Helpers.loadFriendRequests();
    });

    $('.all-notifications').on('click', '.gen-message', function () {
      const id = $(this).data('id');
      const idStr = parseInt(id, 10).toString();
      socket.emit('mark as read', { id: idStr });
      socket.on('blurr read', () => {
        $(this).css('color', 'rgb(80, 74, 74)');
      });
    });
  });

  $('#profile-pic').on('click', (event) => {
    $('.profile-container').show();
    $('.notification-box').hide();
    event.stopPropagation();

    $('#closePopup').on('click', () => {
      $('.profile-container').hide();
    });
    // Closes the profile-container
    $(document).on('click', (event) => {
      const profileContainer = $('.profile-container')[0];
      const locationUpdateicon = $('#location-stat')[0]; // Get the raw DOM element
      const uploadBtn = $('#new-avatar')[0]; // Get the raw DOM element
      // Check if the target is not #add-icon, its descendant, or #add-friend-input
      if (!locationUpdateicon.contains(event.target)
          && !uploadBtn.contains(event.target)
          && !profileContainer.contains(event.target)
      ) {
        $('.profile-container').hide();
      }
    });

    $('#new-avatar').on('click', () => {
      // $('.upload-box').show();
      uploadBox = $('.upload-box');
      uploadBox.show();

      $('#cancel').on('click', () => {
        uploadBox.hide();
      });
    });

    $('.del-user').on('click', () => {
      // eslint-disable-next-line no-restricted-globals, no-alert
      const confirmed = confirm('Are you sure you want to delete this account?');

      if (confirmed) {
        socket.emit('delete all user notifications');
        $.ajax({
          type: 'DELETE',
          url: '/api/user/remove',
          contentType: 'application/json',
          success(response) {
            if (response.redirect) {
              // redirects user to the homepage
              window.location.href = response.redirect;
            }
          },
          error() {
            const message = 'something went wrong';
            socket.emit('send error message', { message });
          },
        });
      }
    });
  });

  // Handle user logout
  $('#logout').on('click', () => {
    $.ajax({
      type: 'GET',
      url: '/user/logout',
      contentType: 'application/json',
      success(response) {
        if (response.redirect) {
          window.location.href = response.redirect;
        }
      },
      error: () => {
        console.error();
      },
    });
  });

  // Flash error messages
  socket.on('error', (data) => {
    const { message } = data;
    $('#flash-text').text(message).css('color', 'red');
    $('#flash-text').fadeIn();
    setTimeout(() => {
      $('#flash-text').fadeOut();
    }, 3000);
  });

  // Flash successful messages
  socket.on('success', (data) => {
    const { message } = data;
    $('#flash-text').text(message).css('color', 'green');
    $('#flash-text').fadeIn();
    setTimeout(() => {
      $('#flash-text').fadeOut();
    }, 3000);
    $('#add-friend-input').val('');
  });

  // Alerts friend of a new notification
  socket.on('alert_user', () => {
    Helpers.ringNotificationBell();
  });

  socket.on('reload_friend_request', () => {
    loadedFriendRequests = false;
    Helpers.loadFriendRequests();
  });

  socket.on('reload_general_notification', () => {
    Helpers.loadGeneralNotifications();
  });
});
