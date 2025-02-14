// OPEN AND CLOSE POP-UPS
function openOHForm() {
    document.getElementById("addOH").style.display = "block";
    document.getElementById('overlay').style.display = 'block';
}

function closeOHForm() {
    document.getElementById("addOH").style.display = "none";
    document.getElementById('overlay').style.display = 'none';
}

function openAdminForm() {
    document.getElementById("addAdmin").style.display = "block";
    document.getElementById('overlay').style.display = 'block';
}

function closeAdminForm() {
    document.getElementById("addAdmin").style.display = "none";
    document.getElementById('overlay').style.display = 'none';
}

function openProposalForm() {
    document.getElementById("sendOH").style.display = "block";
    document.getElementById('overlay').style.display = 'block';
}

function closeProposalForm() {
    document.getElementById("sendOH").style.display = "none";
    document.getElementById('overlay').style.display = 'none';
}

function openApprovalForm() {
    fetchOhToApprove()
    document.getElementById("approveOH").style.display = "block";
    document.getElementById('overlay').style.display = 'block';
}

function closeApprovalForm() {
    document.getElementById("approveOH").style.display = "none";
    document.getElementById('overlay').style.display = 'none';
}

function openExportForm() {
    fetchOhToApprove()
    document.getElementById("exportOH").style.display = "block";
    document.getElementById('overlay').style.display = 'block';
}

function closeExportForm() {
    document.getElementById("exportOH").style.display = "none";
    document.getElementById('overlay').style.display = 'none';
}