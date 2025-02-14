'use strict';

document.addEventListener('DOMContentLoaded', function () {
    fetchSavedCourses();

    $('#searchInput').on('input', function () {
        getResults();
    });
});

function displayResults(results) {
    let html = '';

    results.forEach(result => {
        html += `
            <div class="result-item">
                    <button onclick="saveCourse(\`${result.courseid}\`, \`${result.dept_num}\`, \`${result.title}\`)">+</button>
                    <strong><span class="course_num">${result.dept_num}</span></strong>
                <span class="title">${result.title}</span>
            </div>
        `;
    });
    $('#searchResults').html(html);
}

let timer = null
let request = null

function getResults() {
    clearTimeout(timer); // clear any existing debounce timer

    // set new debounce timer
    timer = setTimeout(() => {
        let searchInput = $('#searchInput').val();

        if (searchInput.length > 0) {
            if (request !== null) {
                request.abort();
            }

            request = $.ajax({
                url: "/searchresults",
                type: "GET",
                data: { searchInput: searchInput },
                success: function(response) {
                    if (response.status === "success") {
                        displayResults(response.results);
                    } else {
                        $('#searchResults').html(`<p>${response.message}</p>`);
                    }
                },
                error: function() {
                    $('#searchResults').html('<p>Error retrieving results</p>');
                }
            });
        } else {
            $('#searchResults').empty();
        }
    }, 500); // debounce delay is 500 (can adjust)
}



function loadCourses(results) {
    let html = '';
    $('#savedCourses').html(html);
    results.forEach(result => {
        html += `
            <div style="background-color:${result.color}" class="saved-course-item" id="p${result.courseid}">
                <div class="saved-course-top-line">
                    <div style="flex-grow:6">
                        <strong><span class="course_num">${result.dept_num}</span></strong>
                    </div>
                    <div class="saved-course-buttons">
                        <label class="switch">
                            <input type="checkbox" ${result.is_toggled ? 'checked' : ''}
                            onclick="toggle(\`${result.courseid}\`)">
                            <span class="eye"></span>
                        </label>
                        <button onclick="removeSavedCourse(\`${result.courseid}\`)"></button>
                    </div>
                </div>
                    <span class="title">${result.title}</span>
            </div>
        `;
    });
    $('#savedCourses').append(html);

    let createOhHtml = '';
    $('#courses').html(createOhHtml);
    results.forEach(result => {
        if (result.is_admin) {
            createOhHtml += `
        <option name="course_id" value="${result.courseid}" id="p${result.courseid}">${result.dept_num}</option>
        `
        }
    });
    $('#courses').append(createOhHtml);

    let sendOhHtml = '';
    $('#proposal-courses').html(sendOhHtml);
    results.forEach(result => {
        sendOhHtml += `
        <option name="course_id" value="${result.courseid}" id="p${result.courseid}">${result.dept_num}</option>
        `
    });
    $('#proposal-courses').append(sendOhHtml);

    let adminCoursesHtml = '';
    $('#admin-courses').html(adminCoursesHtml);
    results.forEach(result => {
        if (result.is_admin) {
        adminCoursesHtml += `
            <option name="course_id" value="${result.courseid}" id="p${result.courseid}">${result.dept_num}</option>
        `;
        }
    });
    $('#admin-courses').append(adminCoursesHtml);

    
    let proposeHtml = '';
    $('#associated-instructors').html(proposeHtml);
    proposeHtml += `<option name="instructor" value="58457afe-ca1c-4a01-bd1f-02ec5296ee97">-- Please choose an instructor --</option>`
    results.forEach(result => {
        if (result.courseid == $('#proposal-courses').val()) {
        let instructor_netids = result.instructor_netids
        let instructor_names = result.instructor_names
        console.log(instructor_netids)
        console.log(instructor_names)
        for (let index = 0; index < instructor_netids.length; index++) {
            proposeHtml += `
            <option name="instructor" value="${instructor_netids[index]}" id="${instructor_netids[index]}">${instructor_names[index]}</option>
            `;
        }
    }
    });
    $('#associated-instructors').append(proposeHtml);
}

function removeSavedCourseHtml(courseid, is_admin) {
    const parentSavedCourses = document.getElementById("savedCourses")
    console.log(parentSavedCourses)
    const currentCourseChild = parentSavedCourses.querySelector('#p' + courseid)
    parentSavedCourses.removeChild(currentCourseChild);

    const parentProposalCourses = document.getElementById("proposal-courses")
    console.log(parentProposalCourses)
    const currentProposalChild = parentProposalCourses.querySelector('#p' + courseid)
    parentProposalCourses.removeChild(currentProposalChild);

    if (is_admin) {
        const parentCreateCourses = document.getElementById("courses")
        console.log(parentCreateCourses)
        const currentCreateChild = parentCreateCourses.querySelector('#p' + courseid)
        parentCreateCourses.removeChild(currentCreateChild);

        const parentAdminCourses = document.getElementById("admin-courses")
        console.log(parentAdminCourses)
        const currentAdminChild = parentAdminCourses.querySelector('#p' + courseid)
        parentAdminCourses.removeChild(currentAdminChild);
    }
}

function removeSavedCourse(courseid) {
    $.ajax({
        url: "/remove_saved_course",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ courseid: courseid }),
        success: function(response) {
            if (response.status === "success") {
                removeSavedCourseHtml(courseid, response.is_admin)
                window.calendar.refetchEvents();
                getResults();
            } else {
                alert("Failed to remove course.");
            }
        },
        error: function(e) {
            alert("An error occurred while removing the course:", e);
        }
    });
}

function toggle(courseid) {
    const checkbox = event.target;
    $.ajax({
        url: "/toggle",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ courseid: courseid }),
        success: function(response) {
            if (response.status === "success") {
                window.calendar.refetchEvents();
            } else {
                alert("Failed to toggle course.");
            }
        },
        error: function(e) {
            alert("An error occurred while toggling the course:", e);
        }
    });
}

function addCourseToSavedCourses(result) {
    let html = `
        <div style="background-color:${result.color}" class="saved-course-item" id="p${result.courseid}">
            <div class="saved-course-top-line">
                <div style="flex-grow:6">
                    <strong><span class="course_num">${result.dept_num}</span></strong>
                </div>
                <div class="saved-course-buttons">
                    <label class="switch">
                        <input type="checkbox" ${result.is_toggled ? 'checked' : ''}
                        onclick="toggle(\`${result.courseid}\`)">
                        <span class="eye"></span>
                    </label>
                    <button onclick="removeSavedCourse(\`${result.courseid}\`)"></button>
                </div>
            </div>
                <span class="title">${result.title}</span>
        </div>
    `;
    $('#savedCourses').append(html);


    if (result.is_admin) {
        let createOhHtml = `
            <option name="course_id" value="${result.courseid}" id="p${result.courseid}">${result.dept_num}</option>
        `
        $('#courses').append(createOhHtml);
    }


    let sendOhHtml = `<option name="course_id" value="${result.courseid}" id="p${result.courseid}">${result.dept_num}</option>`
    $('#proposal-courses').append(sendOhHtml);

    if (result.is_admin) {
        let adminCoursesHtml = `
        <option name="course_id" value="${result.courseid}" id="p${result.courseid}">${result.dept_num}</option>`;
        $('#admin-courses').append(adminCoursesHtml);
    }

    let proposeHtml = `<option name="instructor" value="58457afe-ca1c-4a01-bd1f-02ec5296ee97">-- Please choose an instructor --</option>`
    if (result.courseid == $('#proposal-courses').val()) {
        let instructor_netids = result.instructor_netids
        let instructor_names = result.instructor_names
        console.log(instructor_netids)
        console.log(instructor_names)
        for (let index = 0; index < instructor_netids.length; index++) {
            proposeHtml += `
            <option name="instructor" value="${instructor_netids[index]}" id="${instructor_netids[index]}">${instructor_names[index]}</option>
            `;
        }
    }
    $('#associated-instructors').append(proposeHtml);
}

function saveCourse(courseid, deptNum, title) {
    $.ajax({
        url: "/save_course",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ courseid: courseid, dept_num: deptNum, title: title }),
        success: function(response) {
            if (response.status === "success") {
                console.log(response.data)
                addCourseToSavedCourses(response.data)
                window.calendar.refetchEvents();
                getResults();
            } else {
                alert("Failed to save course:", response.status);
            }
        },
        error: function() {
            alert("An error occurred while saving the course.");
        }
    });
}

function fetchSavedCourses() {
    $.ajax({
        url: "/fetch_saved_courses",
        type: "GET",
        contentType: "application/json",
        success: function(response) {
            if (response.status === "success") {
                loadCourses(response.results);
            } else {
                alert("Failed to fetch course.");
            }
        },
        error: function() {
            alert("An error occurred while saving the course.");
        }
    });
}

function updateInstructors(){
    $.ajax({
        url: "/fetch_saved_courses",
        type: "GET",
        contentType: "application/json",
        success: function(response) {
            if (response.status === "success") {
                updateInstructorsWithResults(response.results);
            } else {
                alert("Failed to fetch course.");
            }
        },
        error: function() {
            alert("An error occurred while saving the course.");
        }
    });
}

function updateInstructorsWithResults(results) {
    // Add change event listener to filter instructors based on selected course
    let proposeHtml = '';
    $('#associated-instructors').html(proposeHtml);
    proposeHtml += `<option name="instructor" value="cs-officehrs">-- Please choose an instructor --</option>`
    results.forEach(result => {
        if (result.courseid == $('#proposal-courses').val()) {
        let instructor_netids = result.instructor_netids
        let instructor_names = result.instructor_names
        console.log(instructor_names)
        for (let index = 0; index < instructor_netids.length; index++) {
            proposeHtml += `
            <option name="instructor" value="${instructor_netids[index]}" id="${instructor_netids[index]}">${instructor_names[index]}</option>
            `;
        }
    }
    });
    $('#associated-instructors').append(proposeHtml);
}