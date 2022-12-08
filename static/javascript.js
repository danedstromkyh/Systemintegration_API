function reloadPage() {
    setInterval(reloader, 3000)
}

function reloader() {
    window.location.reload(true);
}
reloadPage()