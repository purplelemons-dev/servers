const express = require('express');
const app = express();
const http = require('http').Server(app);
const io = require('socket.io')(http);

app.use(express.static('public'));

io.on('connection', (socket) => {
  console.log('A user connected');

  socket.on('disconnect', () => {
    console.log('A user disconnected');
  });

  socket.on('cursor move', (cursorData) => {
    socket.broadcast.emit('cursor move', cursorData);
  });
});

const PORT = 10005;
http.listen(PORT, () => {
  console.log(`Listening on port ${PORT}`);
});
