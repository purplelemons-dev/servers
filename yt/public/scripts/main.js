const get_transcript = (url) => {
    fetch("/getscript", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            url: url
        })
    })
    .then(res=>res.text())
    .then((text) => {
        document.querySelector("#transcript").innerHTML = text;
    });
}
