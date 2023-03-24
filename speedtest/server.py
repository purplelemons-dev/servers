import socket

def main():
    host = '0.0.0.0'
    port = 10000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)

    print("Speedtest server listening on {}:{}".format(host, port))

    conn, addr = server_socket.accept()
    print("Connection from: " + str(addr))

    while True:
        data = conn.recv(1024)
        if not data:
            break

    conn.close()

if __name__ == '__main__':
    main()
