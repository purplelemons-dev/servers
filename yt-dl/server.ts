
import express from "express";
const app = express();
import {exec} from "child_process";
import fs from "fs";

const PORT = 10000;

const gen_error = (res: express.Response, error: string) => {
    console.log(`Error: ${error}`);
    res.status(500).send("<bold>Error:</bold> " + error);
}

app.use(express.static('public'));

app.post('/download', (req, res) => {
    const url = req.query.url;
    const uniqueId = req.ip + Date.now();
    // TODO get unique id from client 
    console.log(`Got request for ${url} from ${req.ip} with unique id ${uniqueId} path ${req.path}`)

    exec(`./yt-dlp --no-part --restrict-filenames -P ./public/videos/${uniqueId}/ ${url}`, (error, stdout, stderr) => {
        console.log(stdout);
        if (error) {
            gen_error(res, error.message + " during download to server");
        } else if (stderr) {
            gen_error(res, stderr + " during download to server");
        } else {
            const filename = fs.readdirSync(`./public/videos/${uniqueId}/`)[0];
            res.download(__dirname + `/public/videos/${uniqueId}/${filename}`, filename, (err) => {
                console.log()
                if (err) {
                    gen_error(res, err.message + " during upload to client");
                } else {
                    console.log(`Downloaded ${filename} to ${req.ip} with unique id ${uniqueId}`);
                }
                exec(`rm -rf ./public/videos/${uniqueId}/`, (error, stdout, stderr) => {
                    console.log(stdout);
                    if (error) {
                        console.log(`Error: ${error.message} during cleanup`);
                    } else if (stderr) {
                        console.log(`Error: ${stderr} during cleanup`);
                    }
                });
            });
        }
    });
});

app.get('/download', (req, res) => {
    // TODO find download based on what client sent in request
});


app.listen(PORT, () => {
    console.log(`Server is running on http://127.0.0.1:${PORT}`);
});
