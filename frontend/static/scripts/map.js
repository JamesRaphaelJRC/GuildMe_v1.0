$(document).ready(() => {
  // const socket = io('http://127.0.0.1:8000');
  const socket = io(`${window.location.protocol}//${window.location.host}`, { transports: ['websocket'] });

  let map;
  let routingControl;
  const locationThumbnail = $('#location-thumb');
  let geoLocationId;
  let intervalId;
  let userLatLong;
  let userMarker;
  const legend = $('#legend');
  let friend;
  let stoppedSpinning = false;
  let customFriendIcon;

  $('#pincher').draggable({
    containment: 'parent', // Restrict dragging within the container
  });

  function createMap() {
    if (!map && userLatLong) {
      map = L.map('map', { zoomControl: false }).setView([userLatLong[0], userLatLong[1]], 13);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
      }).addTo(map);

      legend.show();

      map.whenReady(() => {
        // Add any layers or markers here
        // eslint-disable-next-line no-use-before-define
        showUserOnMap();
      });
    }
  }

  function showUserOnMap() {
    createMap();
    if (userMarker) {
      userMarker.remove(); // remove the old marker and update with current user location
      userMarker = L.marker(userLatLong, { id: 'user-marker' });
    } else {
      userMarker = L.marker(userLatLong, { id: 'user-marker' });
    }

    // Check if the map already has the user marker
    if (map && userMarker && !map.hasLayer(userMarker)) {
      // Update the position of the existing user marker
      userMarker.addTo(map);

      if (!stoppedSpinning) {
        $('.map-section .loading-spinner').hide();
        stoppedSpinning = true;
      }
    }
  }

  function clearMap() {
    if (routingControl) {
      map.removeControl(routingControl);
      routingControl = null;
    }

    if (map) {
      map.eachLayer((layer) => {
        if (layer instanceof L.Marker) {
          map.removeLayer(layer);
        }
      });
    }
  }

  function updateUserLocation(position) {
    $('#pincher').show();

    const { latitude } = position.coords;
    const { longitude } = position.coords;
    locationThumbnail.css('background-image', 'url(static/images/location-on-48.png)');

    // for the profile page location status update
    $('#location-stat').css('background-image', 'url(static/images/icons8-on-48.png)');
    userLatLong = [latitude, longitude];

    $.ajax({
      type: 'POST',
      url: '/api/user/update_location',
      contentType: 'application/json',
      data: JSON.stringify({ latitude, longitude }),
      dataType: 'json',
      success() {
        showUserOnMap();
      },
      error: (err) => {
        console.log(err);
        $('.map-section .loading-spinner').hide();
      },
    });
  }

  function sendError() {
    locationThumbnail.css('background-image', 'url(static/images/location-off.gif)');
    locationThumbnail.attr('title', 'Reload browser to turn on your location');
    const message = 'Location services disabled. To enable, please go to your browser settings and allow location access for this site.';

    $('.map-section .loading-spinner').hide(); // loading spin

    // for the profile page location status update
    $('#location-stat').css('background-image', 'url(static/images/icons8-off-48.png)');
    socket.emit('send error message', { message });
    $('#pincher').hide();
    navigator.geolocation.clearWatch(geoLocationId);
  }

  function loadOnMap(friendCords) {
    // Checks if user location is on
    if (!userLatLong) {
      const message = `Cannot view ${friend} on the map, your location is turned off`;
      socket.emit('send error message', { message });
      clearInterval(intervalId);
      $('#map').hide();
    } else {
      createMap();

      const [friendLat, friendLong] = friendCords;
      const [userLat, userLong] = userLatLong;

      // Stops the setinterval and watchgeolocation when user arrives his destination
      if (friendLat === userLat && friendLong === userLong) {
        clearInterval(intervalId);
        navigator.geolocation.clearWatch(geoLocationId);
      }

      if (!customFriendIcon) { // creates an icon for friend once
        customFriendIcon = L.icon({
          iconUrl: 'static/images/user_destination.png',
          iconSize: [32, 32],
          iconAnchor: [16, 32],
        });
      }

      // Clear existing markers from the layer group
      markersLayer.clearLayers();

      // Add the user marker to the layer group
      const userMarker = L.marker([userLat, userLong]);
      markersLayer.addLayer(userMarker);

      // Add the friend marker to the layer group with custom icon
      const friendMarker = L.marker([friendLat, friendLong], { icon: customFriendIcon });
      markersLayer.addLayer(friendMarker);

      // Set new waypoints if routing control already exists [to avoid duplicity of route direction]
      if (routingControl) {
        routingControl.setWaypoints([
          L.latLng(userLat, userLong),
          L.latLng(friendLat, friendLong),
        ]);
      } else {
        routingControl = L.Routing.control({
          waypoints: [
            L.latLng(userLat, userLong),
            L.latLng(friendLat, friendLong),
          ],
          lineOptions: {
            styles: [{ color: 'green', opacity: 0.5, weight: 9 }],
            addWaypoints: false,
          },
          showAlternatives: true,
          altLineOptions: {
            styles: [{ color: 'gray', opacity: 0.5, weight: 9 }],
            addWaypoints: false,
          },
        }).addTo(map);
      }
    }
    $('.map-section .loading-spinner').hide(); // hide loading spin
  }

  /**
   * Send a request to retrieve friend location.
   * @param {string} friend - friend username.
   */
  function getFriendLocation(friend) {
    let accessGranted = true;
    intervalId = setInterval(() => {
      if (accessGranted) {
        $.ajax({
          type: 'POST',
          url: '/api/user/friend/current_location',
          contentType: 'application/json',
          data: JSON.stringify({ friend }),
          dataType: 'json',
          success: (resp) => {
            friendLatLong = resp.location;
            loadOnMap(friendLatLong);
          },
          error: (resp) => {
            $('.map-section .loading-spinner').hide(); // hide loading spin
            let message;
            if (resp.status === 404) {
              message = `${friend}'s location is currently unavailable.`;
            } else {
              // if 400
              message = `${friend} did not grant you track access or no more exist`;
            }
            socket.emit('send error message', { message });
            accessGranted = false;
          },
        });
      } else {
        clearInterval(intervalId);
      }
    }, 5000);
  }

  if (navigator.geolocation) {
    $('.map-section .loading-spinner').show(); // loading spin
    geoLocationId = navigator.geolocation.watchPosition(
      updateUserLocation,
      sendError,
      { enableHighAccuracy: true },
    );
  } else {
    console.log('Geolocation not supported');
    sendError();
  }

  $('.friendlist').on('click', '.friend-container', function () {
    friend = $(this).data('friend');

    $('#compass').on('click', () => {
      clearInterval(intervalId); // clear prev interval as user clicks from one friend to another
      $('.map-section .loading-spinner').show(); // show loading spin
      $('.map-section').show(); // for mobile view
      getFriendLocation(friend);
    });

    $(document).on('click', (event) => {
      const friendContainer = $('.friend-container')[0];
      const chatbox = $('.chat-section')[0];
      const mapContainer = $('#map')[0]; // Get the raw DOM element
      const pincher = $('#pincher')[0];
      const mapSection = $('.map-section')[0];
      // Check if the target is not #add-icon, its descendant, or #add-friend-input
      if (!friendContainer.contains(event.target)
          && !chatbox.contains(event.target)
          && !mapContainer.contains(event.target)
          && !pincher.contains(event.target)
          && !mapSection.contains(event.target)) {
        clearInterval(intervalId);
        clearMap();
        showUserOnMap();
      }
    });

    // for mobile view
    $('.mobile-close-btn.close-popup').on('click', () => {
      $('.map-section').hide();
    });
  });

  $('#pincher').on('click', () => {
    // Automatically zoom in and focus on the user's position
    if (map && userLatLong) {
      map.setView(userLatLong, 18);
    }
  });

  $('#location-stat').on('click', () => {
    // eslint-disable-next-line no-restricted-globals
    location.reload();
  });
});
