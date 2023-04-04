
const promt_element = document.getElementById("name-bd9d");
const logged_in = document.getElementById("logged-in");
const conversation_element = document.getElementById("conversation");

/**
 * @param {string} name name your cookie
 * @returns {string} returns the cookie or raises an error
 * @throws {Error} throws an error if the cookie is not found
 */
const getCookie = (name) => {
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

const setCookie = (name,value) => {
    // add to document.cookie if it doesn't exist
    try {
        getCookie(name);
    } catch (error) {
        document.cookie = `${name}=${value};path=/`;
    }  
}


(async () => {
    promt_element.addEventListener("keydown", async (key) => {
        if (key.key === "Enter") {
            // get value of input
            await generate_response();
        }
    });
    /**
     * @type {Map<string, string>}
     */
    const fragment = window.location.hash.slice(1).split("&").reduce((acc, item) => {
        const [key, value] = item.split("=");
        acc.set(key, value);
        return acc;
    }, new Map());
    /*console.log(`fragment: ${JSON.stringify(fragment)}`);
    // log boolean value
    console.log(`boolean fragment: ${Boolean(fragment)}`);*/
    // first off, we check if we were just redirected from discord oauth
    // if so, we need to validate the oauth state and token
    // if not, we need to check if we have a token in local storage
    /**
     * @type {Object}
     */
    let oauth;
    if (fragment.get("access_token")) {
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
                console.log("no token, force login again")
                window.location.href = "/login";
                return;
            }
        }
    } else {
        // we were not redirected from discord oauth
        console.log("we were not redirected from discord oauth");
        window.location.href = "/login";
        return;
    }
    let sess_token = localStorage.getItem("token");
    try {
        sess_token = getCookie("sess_token");
    } catch (error) {
        console.log(error);
        if (!sess_token) {
            // no token, force login again
            console.log("no token, force login again")
            window.location.href = "/login";
            return;
        }
    }
    // Ensure state is valid
    await crypto.subtle.digest( // state is a hash of the session token
        "SHA-256",
        new TextEncoder().encode(
            sess_token
        )
    ).then((hash_buffer) => arrayBufferToHexString(hash_buffer))
        .then(async (hash) => {
            if (hash !== oauth.state) {
                throw new Error("Invalid state/sess_token pair. Please try again.");
            } else {
                // we need to validate oauth state and token. the backend server will access the user's discord servers with oauth.access_token
                await validate(oauth);
            }

        }).catch((error) => {
            // error because hash !== state
            console.log(error);
            // clear local storage to try again
            localStorage.clear();
            document.cookie = "sess_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            alert("Session token does not match oauth state. You could be a victim of a CSRF attack. Please try again.");
            console.log("session token does not match oauth state. force login again")
            window.location.href = "/login";
            return;
        });
})();

const get_conversation = async () => {
    let token;
    try {
        token = getCookie("sess_token");
    } catch (error) {
        token = localStorage.getItem("token");
    }
    console.log(`Getting conversation...`);
    await fetch(`/api/conversation`,
        {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json",
                // We should be able to translate token to user_id in the backend
                "Authorization": `Bearer ${token}`,
            },
        }
    )
        .then((response) => response.json())
        .then((data) => {
            if (data.message === "success") {
                // iterate through data.conversation and add messages to ul#conversation
                console.log(`conversation: ${JSON.stringify(data)}`);
                conversation_element.innerHTML = "";
                data.conversation.forEach((message) => {
                    // create list item element
                    conversation_element.appendChild(new_message(message));
                });
                document.getElementById("system-message").innerHTML = data.system;
            } else {
                throw new Error(data.message);
            }
        });
};

const new_message = (message) => {
    const li = document.createElement("li");
    // replace all newlines with <br>
    message.content = message.content.replace(/\n/g, "<br>");
    // set innerHTML
    li.innerHTML = message.content;
    // styles
    li.classList.add("message", `${message.role}-message`);
    return li;
}

const validate = async (oauth) => {
    let token;
    try {
        token = getCookie("sess_token");
    } catch (error) {
        token = localStorage.getItem("token");
    }
    await fetch("/api/validate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": `Bearer ${token}`
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
                await get_conversation();
                logged_in.classList.remove("hidden");
                logged_in.textContent = `Logged in as ${data.fullname}`;
                promt_element.focus();
            } else {
                // clear local storage to prevent future errors
                localStorage.clear();
                alert(`There was an error logging you in. Please try again. Error: ${data.message}`);
                // force login again
                console.log("force login again because of general error")
                window.location.href = "/login";
                return;
            }
        });
}

const generate_response = async () => {
    const prompt = promt_element.value;
    const system = document.getElementById("system-message").value;
    console.log(`Generating response for ${prompt}...`);

    const new_message = document.createElement("li");
    new_message.textContent = prompt;
    new_message.classList.add("message", "user-message");
    conversation_element.appendChild(new_message);
    promt_element.value = "";
    promt_element.focus();
    console.log(`Sending prompt to backend...`);
    fetch("/api/update", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": `Bearer ${localStorage.getItem("token")}`
        },
        body: JSON.stringify({
            content: prompt,
            system: system
        })
    })
    .then((response) => response.json())
    .then((data) => {
        console.log(`got Response from backend`);
        if (data.message === "success") {
            const conversation_element = document.getElementById("conversation");
            const assistant_message = document.createElement("li");
            conversation_element.appendChild(assistant_message);
            assistant_message.classList.add("message", "assistant-message");
            setCookie("sess_token", localStorage.getItem("token"));
            const event_src = new EventSource("/api/generate");

            event_src.onmessage = async (event) => {
                console.log(`Response from datastream: ${event.data}`);
                let {content} = JSON.parse(event.data);
                content = content.replace(/\n/g, "<br>");
                assistant_message.innerHTML += content;
            };
            event_src.addEventListener("finish", async (event) => {
                console.log(`Finished generating response for ${prompt}\nReason: ${event.data.reason}`);
                conversation_element.scrollTop = conversation_element.scrollHeight;
                event_src.close();
            });
        }
    });
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
