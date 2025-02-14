'use strict';
let calendar;
let hiddenCourses = new Set()

document.addEventListener('DOMContentLoaded', function() {
  let calendarEl = document.getElementById('calendar');

  calendar = new FullCalendar.Calendar(calendarEl, {
    timeZone: 'America/New_York',
    initialView: 'timeGridWeek', 
    allDaySlot: false,
    slotMinTime: '07:00:00',
    nowIndicator: true,
    headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'timeGridDay,timeGridWeek'
    },

    events: fetchEvents,

    /**
     * Handles the click event on calendar events.
     * Parameter {object} info - Event click information.
     */
    eventClick: function (info) {
      info.jsEvent.preventDefault();
      showPopup(info.event, info.jsEvent);

      const editButton = document.getElementById("editOHButton");
      if (editButton) {
        editButton.onclick = function () {
          openEditOH(info.event);
        };
      } else {
        console.error("Edit OH button not found in DOM.");
      }
    },
    
    /**
     * Customizes the rendering of event content.
     * Parameter {object} arg - Event rendering arguments.
     * Returns {object} - Custom DOM nodes for the event.
     */
    eventContent: function(arg) {
      // Parse start and end strings
      let startTime = formatTime(arg.event.startStr);
      let endTime = arg.event.endStr ? formatTime(arg.event.endStr) : '';
      let timeRange = startTime + (endTime ? ' - ' + endTime : '');

      // Create time, title, and note elements
      let time = document.createElement('div');
      time.innerText = timeRange;
      time.classList.add('fc-event-time');

      // Create a container for the custom event content
      let title = document.createElement('div');
      title.innerText =  arg.event.extendedProps.course + ": " + arg.event.title;
      title.classList.add('fc-event-title');

      let location = document.createElement('div');
      location.innerText = arg.event.extendedProps.location;
      location.classList.add('fc-event-location');

      // Append both fields to a single wrapper
      let content = document.createElement('div');
      content.appendChild(time)
      content.appendChild(title);
      content.appendChild(location);
      if (arg.event.extendedProps.is_draft) {
        content.classList.add('fc-event-draft')
      }
      content.classList.add("fc-custom-event")

      return { domNodes: [content] };
    }
  });

  calendar.render();
  window.calendar = calendar;
  
  /**
   * Fetches events dynamically from the server.
   * Parameter {object} fetchInfo - Fetch timing details.
   * Parameter {function} successCallback - Callback for successful event fetch.
   * Parameter {function} failureCallback - Callback for fetch failure.
   */
  function fetchEvents(fetchInfo, successCallback, failureCallback) {
    console.log('fetching events'); 
      $.ajax({
          url: '/events',
          type: 'GET',
          dataType: 'json',
          success: function(data) {
              console.log(data)
              successCallback(data);
          },
          error: function(error) {
              failureCallback(error);
          }
    });
  }

  document.querySelector('.export-ical').addEventListener('click', function() {
    exportToICal();
  });
});

/**
 * Displays error messages for forms dynamically.
 * Parameter {string} message - The error message to display.
 * Parameter {string} id - The ID of the form to attach the message to.
 */
function displayErrorMessage(message, id) {
  console.log(id)
  let errorContainer = document.getElementById("error-message");

  if (!errorContainer) {
      errorContainer = document.createElement("div");
      errorContainer.id = "error-message";
      errorContainer.style.color = "red";
      errorContainer.style.marginTop = "10px";
      document.getElementById(id).appendChild(errorContainer);
  }

  errorContainer.textContent = message;
}

/**
 * Submits a new office hour event to the server.
 * Parameter {string} netid - User identifier for the request.
 */
function postOH(netid) {
  const formData = new FormData(document.getElementById('event-form'));
  formData.append("netid", netid)

  $.ajax({
      url: '/createoh',
      type: 'POST',
      data: formData,
      processData: false, 
      contentType: false, 
      dataType: 'json',
      success: function(data) {
        closeOHForm(); 
        document.getElementById("event-form").reset();
        calendar.refetchEvents() 
      },
      error: function(error) {
        displayErrorMessage(error.responseJSON['message'] || 'An unexpected error occurred.', 'event-form');
        console.error('Error:', error);
      }
  });
}

/**
 * Submits a new draft office hour event to the server.
 * Parameter {string} netid - User identifier for the request.
 */
function sendOH(netid) {
  const formData = new FormData(document.getElementById('propose-oh-form'));
  formData.append("netid", netid)

  $.ajax({
      url: '/sendoh',
      type: 'POST',
      data: formData,
      processData: false, 
      contentType: false, 
      dataType: 'json',
      success: function(data) {
        closeProposalForm(); 
        document.getElementById("propose-oh-form").reset();
        calendar.refetchEvents() 
      },
      error: function(error) {
        displayErrorMessage(error.responseJSON['message'] || 'An unexpected error occurred.', 'propose-oh-form');
        console.error('Error:', error);
      }
  });
}

/**
 * Populate approve form with any approve requests
 * Parameter {object} result_data - Office hours information
 */
function updateApproveForm(result_data) {
  let html = '';
  $('#oh-to-approve-container').html(html);
  console.log(result_data)
  result_data.forEach(result => {
      html += `
          <div class="pill custom-radio-group" data-id="${result.oh_id}">
            <div class="proposed-oh-info">
              <div><strong>${result.dept_num} - ${result.oh_instructor}</strong></div>
              <div>${formatTime(result.oh_date+'T'+result.oh_starttime)} - ${formatTime(result.oh_date+'T'+result.oh_endtime)}, ${result.oh_date}</div>
            </div>
            <label class="custom-radio">
              <input type="radio" name="status_${result.oh_id}" value="approve" />
              <span class="radio-button radio-button-approve">
                <span class="radio-symbol">✓</span>
              </span>
            </label>
            <label class="custom-radio">
              <input type="radio" name="status_${result.oh_id}" value="reject" />
              <span class="radio-button radio-button-reject">
                <span class="radio-symbol">✗</span>
              </span>
            </label>
          </div>
      `;
  });
  if (result_data.length > 0){
    console.log("here")
    $('#oh-to-approve-container').append(html);
  } else {
    $('#oh-to-approve-container').append("Nothing to approve!");
  }
}

/**
 * Fetch office hours requests to approve
 */
function fetchOhToApprove() {
  $.ajax({
      url: "/fetch_oh_to_approve",
      type: "GET",
      contentType: "application/json",
      success: function(response) {
          if (response.status === "success") {
            updateApproveForm(response.results)
          } else {
              console.log(response)
              alert("Failed to fetch course.");
          }
      },
      error: function() {
          alert("An error occurred while saving the course.");
      }
  });
}

/**
 * Approves selected office hours and sends the data to the server.
 */
function approveOH() {
    const items = [];

    // Collect data from each pill
    document.querySelectorAll('div.pill').forEach(pill => {
      const id = pill.dataset.id
      if (pill.querySelector(`input[name="status_${id}"]:checked`)) {
        const status = pill.querySelector(`input[name="status_${id}"]:checked`).value;
        items.push({ id, status });
      }
    });

    $.ajax({
      url: '/approve_office_hours',
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({ items }),
      success: function() {
        closeApprovalForm();
        document.getElementById("approve-oh-form").reset();
        calendar.refetchEvents()
      },
      error: function(error) {
        displayErrorMessage(error.responseJSON['message'] || 'An unexpected error occurred.', 'approve-oh-form');
        console.error('Error:', error);
      }
    });
}

/**
 * Delete the office hours event for the server.
 */
function deleteOfficeHours() {
  const ohId = document.getElementById('ohId').value;
  const formData = new FormData();
  formData.append('oh_id', ohId);

  $.ajax({
    url: '/delete-office-hour',
    type: 'POST',
    data: formData,
    processData: false,
    contentType: false,
    dataType: 'json',
    success: function(data) {
      closePopup();
      calendar.refetchEvents();
    },
    error: function(error) {
      console.error('Error:', error);
      displayErrorMessage('An unexpected error occurred.');
    }
  });
}

/**
 * Update the office hours event in the server.
 */
function updateOfficeHours() {
  const formData = new FormData(document.getElementById('edit-office-hour-form'));
  
  $.ajax({
    url: '/update-office-hour',
    type: 'POST',
    data: formData,
    processData: false,
    contentType: false,
    dataType: 'json',
    success: function(data) {
      closeEditOH();
      calendar.refetchEvents();
    },
    error: function(error) {
      displayErrorMessage(error.responseJSON['message'] || 'An unexpected error occurred.', 'edit-office-hour-form');
      console.error('Error:', error);
    }
  });
}

/**
 * Make user an admin for particular course
 */
function addAdmin() {
  const formData = new FormData(document.getElementById('add-admin-form'));

  $.ajax({
    url: '/add_admin',
    type: 'POST',
    data: formData,
    processData: false, 
    contentType: false, 
    dataType: 'json',
    success: function() {
      closeAdminForm();
      document.getElementById("add-admin-form").reset();
    },
    error: function(error) {
      displayErrorMessage(error.responseJSON['message'] || 'An unexpected error occurred.', 'add-admin-form');
      console.error('Error:', error);
    }
  });
}

/**
 * Convert calendar events into ics file and download it.
 */
function exportToICal() {
  const events = calendar.getEvents(); 

  // Add a VTIMEZONE block for America/New_York
  let icsContent = `BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN
PRODID:-//Your App Name//Your App Version//EN
BEGIN:VTIMEZONE
TZID:America/New_York
BEGIN:STANDARD
DTSTART:20231105T020000
RRULE:FREQ=YEARLY;BYDAY=1SU;BYMONTH=11
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:20240310T020000
RRULE:FREQ=YEARLY;BYDAY=2SU;BYMONTH=3
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
END:DAYLIGHT
END:VTIMEZONE
`;

  // Loop through the events and format them for iCal
  events.forEach(event => {
      const start = formatToLocalTime(event.start);
      const end = event.end ? formatToLocalTime(event.end) : '';
      const summary = event.title;
      const location = event.extendedProps.location || '';
      const description = event.extendedProps.description || '';
      
      // we might want to check this out for injec
      icsContent += `BEGIN:VEVENT
DTSTAMP:${new Date().toISOString().replace(/[-:]/g, '').split('.')[0]}Z
DTSTART;TZID=America/New_York:${start}
${end ? `DTEND;TZID=America/New_York:${end}` : ''}
SUMMARY:${summary} 
LOCATION:${location}
DESCRIPTION:${description}
END:VEVENT
`;
  });

  icsContent += `END:VCALENDAR`;

  // Create and download the iCal file
  const blob = new Blob([icsContent], { type: 'text/calendar' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = 'events.ics';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * Convert iso string to local time.
 */
function formatToLocalTime(date) {
  const localDate = new Date(date).toISOString().replace(/[-:]/g, '').split('.')[0];
  return localDate;
}

/**
 * Formats a given ISO string into a human-readable time format (e.g., 1:30 PM).
 * Parameter {string} isoString - The ISO date-time string to format.
 * Returns string - The formatted time string.
 */
function formatTime(isoString) {
  let date = new Date(isoString);
  let hours = date.getHours();
  let minutes = date.getMinutes().toString().padStart(2, '0');
  let ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12 || 12;
  return hours + ':' + minutes + ' ' + ampm;
}

/**
 * Opens popup with event information.
 * Parameter {object} event - The event object to details about.
 */
function showPopup(event, jsEvent) {
  document.getElementById('eventCourse').innerText = event.extendedProps.course;
  document.getElementById('eventInstructor').innerText = event.title;
  document.getElementById('eventLocation').innerText = event.extendedProps.location;
  document.getElementById('ohId').value = event.extendedProps.oh_id;

  let startTime = formatTime(event.startStr);
  let endTime = event.endStr ? formatTime(event.endStr) : '';
  let timeRange = startTime + (endTime ? ' - ' + endTime : '');
  document.getElementById('eventStartEnd').innerText = timeRange;

  let top = jsEvent.clientY;
  let left = jsEvent.clientX;
  const popup = document.getElementById('event-popup');
  
  // initial popup position
  popup.style.top = `${top}px`;
  popup.style.left = `${left}px`;
  popup.classList.remove('hidden');

  // change position if we find that it overflows off the screen
  const popupRect = popup.getBoundingClientRect();
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;

  // handles right edge
  if (popupRect.right > viewportWidth) {
    left = viewportWidth - popupRect.width;
  }
  // handles bottom edge
  if (popupRect.bottom > viewportHeight) {
    top = viewportHeight - popupRect.height;
  }
  // update
  popup.style.top = `${top}px`;
  popup.style.left = `${left}px`;
  
  const overlay = document.getElementById('popup-overlay');
  overlay.style.display = 'block';
}

/**
 * Closes the popup.
 */
function closePopup() {
  document.getElementById('event-popup').classList.add('hidden');
  document.getElementById('popup-overlay').style.display = 'none';
}

/**
 * Opens the edit office hours form and populates it with event data.
 * Parameter {object} event - The event object to edit.
 */
function openEditOH(event) {
  document.getElementById('popup-overlay').style.display = 'none';

  const dateInput = document.getElementById('editdate');
  const startTimeInput = document.getElementById('editstarttime');
  const endTimeInput = document.getElementById('editendtime');
  const locationInput = document.getElementById('editlocation');
  const ohidInput = document.getElementById('ohid');

  if (dateInput) {
    dateInput.value = event.start.toISOString().split('T')[0];
  }
  if (startTimeInput) {
    startTimeInput.value = event.start.toISOString().split('T')[1].slice(0, 5); // HH:MM format
  }
  if (endTimeInput && event.end) {
    endTimeInput.value = event.end.toISOString().split('T')[1].slice(0, 5); // HH:MM format
  }
  if (ohidInput) {
    ohidInput.value = event.extendedProps.oh_id || '';
  }
  if (ohidInput) {
    locationInput.value = event.extendedProps.location || '';
  }

  document.getElementById('event-popup').classList.add('hidden');
  document.getElementById("editOH").style.display = "block";
  document.getElementById('overlay').style.display = 'block';
}

/**
 * Closes the edit office hours form.
 */
function closeEditOH() {
  document.getElementById("editOH").style.display = "none";
  document.getElementById('overlay').style.display = 'none';
}