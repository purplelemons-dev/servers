
const promt_element = document.getElementById("name-bd9d");
const logged_in = document.getElementById("logged-in");



(async ()=> {
    const fragment = new URLSearchParams(window.location.hash);
    // first off, we check if we were just redirected from discord oauth
    // if so, we need to validate the oauth state and token
    // if not, we need to check if we have a token in local storage
    let oauth;
    try {
        oauth = {
            access_token: fragment.get("access_token"),
            token_type: fragment.get("token_type"),
            expires_in: fragment.get("expires_in"),
            scope: fragment.get("scope"), // scope should be "identify" and "guilds"
            state: fragment.get("state")
        };
    } catch (error) {
        console.log(error);
        alert("could not get oauth data. Please try again.");
        // try getting local storage token
        if (localStorage.getItem("token")) {
            // we have a token, we can try to get the conversation
            await get_conversation();
        } else {
            // no token, force login again
            window.location.href = "/";
        }
    }
    let sess_token;
    try {
        sess_token = getCookie("sess_token");
    } catch (error) {
        console.log(error);
        sess_token = localStorage.getItem("token");
        if (!sess_token) {
            // no token, force login again
            window.location.href = "/";
        }
    }
    // Ensure state is valid
    await crypto.subtle.digest( // state is a hash of the session token
        "SHA-256",
        new TextEncoder().encode(
            
        )
    ).then((hash_buffer) => arrayBufferToHexString(hash_buffer))
    .then((hash) => {
        if (hash !== oauth.state) {
            throw new Error("Invalid state/sess_token pair. Please try again.");
        }
    }).catch((error) => {
        // error because hash !== state
        console.log(error);
        // clear local storage to try again
        localStorage.clear();
        alert("Session token does not match oauth state. You could be a victim of a CSRF attack. Please try again.");
        window.location.href = "/";
    });
    // we need to validate oauth state and token. the backend server will access the user's discord servers with oauth.access_token
})();

const get_conversation = async () => {
    const conversation = document.getElementById("conversation");
    console.log(`Getting conversation...`);
    fetch(`/api/conversation`,
        {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json",
                // We should be able to translate token to user_id in the backend
                "Authorization": `Bearer ${localStorage.getItem("token")}`,
            },
        }
    )
    .then((response) => response.json())
    .then((data) => {
        console.log(data);
        if (data.message === "success") {
            // iterate through data.conversation and add messages to ul#conversation
        } else {
            throw new Error(data.message);
        }
    });
};

const validate =  async (oauth) => {
    await fetch("/api/validate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": `Bearer ${localStorage.getItem("token")}`
        },
        body: JSON.stringify({
            state: oauth.state,
            access_token: oauth.access_token
        }),
    })
    .then((response) => response.json())
    .then(async (data) => {
        // our token is valid, we can now get the user's conversation
        if (data.message === "success") {
            // token does not originate from discord, we do not store discord tokens
            // data should contain message, user_id, username, discriminator, and token. data.message will be "success" if the user is in the server
            localStorage.setItem("token", getCookie("sess_token"));
            await get_conversation(data.user_id);
            logged_in.classList.remove("hidden");
            logged_in.textContent = `Logged in as ${data.fullname}`;
            promt_element.focus();
        } else {
            // clear local storage to prevent future errors
            localStorage.clear();
            alert(`There was an error logging you in. Please try again. Error: ${data.message}`);
            // force login again
            window.location.href = "/";
        }
    });
}

const generate_response = () => {
    const prompt = promt_element.value;
    console.log(`Generating response for ${prompt}...`);
    /*// create a new li in conversation
    // add data.content text to the li
    let assistant_message = document.createElement("li");
    assistant_message.classList.add("assistant-message");
    assistant_message.classList.add("message");
    conversation.appendChild(assistant_message).textContent = data.content;*/
};

const arrayBufferToHexString = (arrayBuffer) => {
    const byteArray = new Uint8Array(arrayBuffer);
    const hexParts = [];

    for (let i = 0; i < byteArray.length; i++) {
        const hex = byteArray[i].toString(16);
        const paddedHex = ('00' + hex).slice(-2);
        hexParts.push(paddedHex);
    }

    return hexParts.join('');
}

function getCookie(name) {
    const cookieName = name + "=";
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookieArray = decodedCookie.split(';');

    for (let i = 0; i < cookieArray.length; i++) {
        let cookie = cookieArray[i];
        while (cookie.charAt(0) === ' ') {
            cookie = cookie.substring(1);
        }
        if (cookie.indexOf(cookieName) === 0) {
            return cookie.substring(cookieName.length, cookie.length);
        }
    }
    throw new Error("Could not find cookie");
}
