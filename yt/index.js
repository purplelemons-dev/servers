
const express = require('express');
const app = express();
const ytdl = require('ytdl-core');
const fs = require('fs');
const { Configuration, OpenAIApi } = require("openai");
const { resolve } = require('path');
app.use(express.static('public'));
app.use(express.json());

const configuration = new Configuration({
    apiKey: fs.readFileSync("./.env","utf-8").trim()
});
const openai = new OpenAIApi(configuration);

app.post('/getscript', async (req, res) => {
    const { url } = req.body;
    // download the audio and use openai.createTranscription on the

    const stream = ytdl(url, {
        filter: 'audioonly',
        format: 'mp3'
    });//.read();
    stream.pipe(fs.createWriteStream('audio.mp3'));

    console.log("getting transcript");

    await new Promise((resolve) => stream.on('end', resolve));

    stream.on('readable', () => {
        let chunk;
        console.log('Stream is readable (new data received in buffer)');
        // Use a loop to make sure we read all currently available data
        while (null !== (chunk = stream.read())) {
          console.log(`Read ${chunk.length} bytes of data...`);
        }
      });
    res.send(response.data);
});

app.get('*', (req, res) => {
    res.redirect("error404.html");
});

app.listen(10006, () => {
    console.log("hosting on http://localhost:10006");
});
